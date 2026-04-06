"""End-to-end QA orchestration: parse → verify → retrieve → backward → clarify → forward → proof → evidence → answer."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from generation.answer_generator import (
    apply_answer_text_and_refresh_citations,
    generate_answer,
    safe_regenerate_final_answer,
)
from reasoning.clarification_manager import (
    build_clarification_prompts_from_requirements,
    build_parse_ambiguity_prompts,
    merge_clarification_prompts_unified,
)
from question_side.parse_clarify_apply import (
    extract_resolved_condition_atoms_from_known_facts,
    known_facts_for_reasoning,
    structured_facts_for_reasoning,
)
from question_side.question_normalizer import build_layer2
from question_side.question_parser import parse_question_layer1
from retrieval.evidence_retriever import (
    EvidenceRetriever,
    configure_evidence_path,
    get_evidence_retriever,
)
from retrieval.advanced_domain_retriever import AdvancedDomainRetriever
from retrieval.domain_scoped_retriever import DomainScopedRuleRetriever, enrich_ranked_with_retrieval_meta
from retrieval.rule_retriever import retrieve_rules
from retrieval.rulebase_loader import RulebaseIndex, configure_rulebase_path, get_rulebase_index
from rulebase.rule_identity import global_rule_key
from rulebase.rulebase_registry import RulebaseRegistry
from runtime.cross_domain_policy import (
    default_policy_for_routing,
    filter_ranked_for_primary_phase,
    merge_secondary_with_policy,
)
from runtime.domain_selector import SimpleDomainSelector
from runtime.qa_runtime_bundle import QARuntimeBundle
from runtime.phase3_pipeline import apply_phase3_post_retrieve
from runtime.reasoning_context import ReasoningContext
from schemas.domain_routing import DomainRoutingPlan
from schemas.rule_metadata import collect_rulebase_ids_from_index
from schemas.http_response import AskResponse, ClarificationPrompt, ClarifyResponse
from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleRecord
from schemas.reasoning_result import ReasoningResult
from schemas.session import SessionState
from schemas.verification import VerificationRecord
from session.session_service import SessionService, get_session_service
from verification.engine import NeSyEngine
from verification.nli_verifier import NLIVerifier
from verification.repair_loop import run_answer_repair_loop, run_parse_repair_loop
from runtime.verification_gates import gate_forward_reasoning, gate_rule_and_backward
from runtime.pipeline_tracing import (
    TraceCollector,
    summarize_answer_trace,
    summarize_evidence_trace,
    summarize_layer1_trace,
    summarize_layer2_trace,
    summarize_verification_trace,
)

logger = logging.getLogger(__name__)


def _merge_pipeline_trace_dict(trace: dict[str, Any], tc: TraceCollector) -> None:
    if not tc._noop:
        d = tc.to_dict()
        m = dict(d.get("meta") or {})
        block = {k: trace[k] for k in (
            "domain_routing",
            "reasoning_context",
            "retrieved_rules_by_domain",
            "proof_steps_by_domain",
            "final_grounding_docs",
            "reasoning_result",
            "phase3",
        ) if k in trace}
        if block:
            m["multi_rulebase_v1"] = block
        d["meta"] = m
        trace["pipeline_trace"] = d


def _rule_dump(r: RuleRecord) -> dict[str, Any]:
    return r.model_dump(mode="json")


def _merge_verification(sess: SessionState, rec: VerificationRecord) -> None:
    sess.verification_logs.append(rec)


def _user_fact_keys(session: SessionState) -> list[str]:
    return list(known_facts_for_reasoning(session).keys())


def _proof_summary_for_evidence(proof: Any) -> str:
    if not proof:
        return ""
    return " ".join((s.description or "") for s in (getattr(proof, "proof_steps", None) or [])[:8])


def _group_retrieved_by_domain(
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    by_dom: dict[str, list[dict[str, Any]]] = {}
    for r, s, d in ranked:
        dom = str(d.get("domain") or "unknown")
        by_dom.setdefault(dom, []).append(
            {
                "rule_id": r.rule_id,
                "rulebase_id": d.get("rulebase_id"),
                "domain": dom,
                "layer": d.get("layer"),
                "score": float(s),
                "source_doc": d.get("source_doc"),
                "source_article": d.get("source_article"),
            }
        )
    return by_dom


def _proof_steps_by_domain(proof: Any) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for s in getattr(proof, "proof_steps", None) or []:
        dom = str(getattr(s, "domain", None) or "unknown")
        out.setdefault(dom, []).append(
            {
                "step_id": getattr(s, "step_id", None),
                "rule_id": getattr(s, "rule_id", None),
                "rulebase_id": getattr(s, "rulebase_id", None),
                "domain": getattr(s, "domain", None),
                "layer": getattr(s, "layer", None),
                "source_doc": getattr(s, "source_doc", None),
                "source_article": getattr(s, "source_article", None),
            }
        )
    return out


def _grounding_docs_from_evidence(ev: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for e in ev or []:
        rows.append(
            {
                "chunk_id": getattr(e, "chunk_id", None),
                "article_clause": getattr(e, "article_clause", None),
                "score": round(float(getattr(e, "score", 0.0)), 5),
            }
        )
    return rows


def _finalize_reasoning_result_dict(
    base: dict[str, Any],
    *,
    proof: Any | None,
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    bstate: Any | None,
    fstate: Any | None,
    selected: RuleRecord | None,
    phase3_result: Any | None = None,
) -> dict[str, Any]:
    out = dict(base)
    
    # Phase 3 data
    if phase3_result is not None:
        out["bridge_rules_used"] = [
            str(x.provenance.bridge_rule_id) 
            for x in phase3_result.bridge_emitted
        ]
        out["bridge_generated_facts"] = [
            x.model_dump(mode="json") 
            for x in phase3_result.bridge_emitted
        ]
        out["rejected_candidates_temporal"] = phase3_result.temporal_rejected
        out["rejected_candidates_conflict"] = phase3_result.conflict_rejected
        out["rule_id_collision_warnings"] = phase3_result.rule_id_collision_warnings
        out["namespacing_mode"] = "global_rule_key_v1"
    
    if proof is not None:
        dom_summary = _proof_steps_by_domain(proof)
        out["proof_summary_by_domain"] = {
            k: [str(s.get("rule_id") or "") for s in v[:16]] for k, v in dom_summary.items()
        }
    if bstate is not None:
        out["subgoals_unresolved"] = list(getattr(bstate, "missing_facts", None) or [])
        out["subgoals_satisfied"] = list(getattr(bstate, "covered_requirements", None) or [])
        out["unresolved_subgoals_domain"] = list(getattr(bstate, "missing_facts", None) or [])
        bp = getattr(bstate, "backward_plan", None) or {}
        if isinstance(bp, dict):
            ev = bp.get("evaluation") or {}
            ltd = ev.get("logic_layer_decisions") or []
            if ltd:
                out["logic_layer_policy_decisions"] = list(ltd)
    if selected is not None:
        out["final_winning_rule_ids"] = [selected.rule_id]
    rt = out.get("rejected_candidates_temporal") or []
    rc = out.get("rejected_candidates_conflict") or []
    out["rejected_candidates"] = list(rt) + list(rc)
    bridge_ids: list[str] = []
    if phase3_result is not None:
        bridge_ids = [str(x.fact_id) for x in phase3_result.bridge_emitted if getattr(x, "fact_id", None)]
    out["bridge_facts_consumed"] = bridge_ids
    out["diagnostics"] = {
        "candidate_rule_count": len(ranked),
        "forward_trace": bool(fstate and getattr(fstate, "forward_result", None)),
        "logic_layer": bool(out.get("logic_layer_policy_decisions")),
    }
    try:
        return ReasoningResult.model_validate(out).model_dump(mode="json")
    except Exception:
        return out


class QAOrchestrator:
    """Central business orchestrator for ask / clarify flows."""

    def __init__(
        self,
        *,
        rulebase_core_path: Path,
        evidence_chunks_path: Path,
        rule_retrieval_top_k: int = 8,
        nesy_nli_mock: bool = False,
        nli_verifier: NLIVerifier | None = None,
        nli_degraded: bool = False,
        nli_meta: dict[str, Any] | None = None,
        entailment_threshold: float = 0.70,
        contradiction_threshold: float = 0.70,
        max_repair_attempts_parse: int = 2,
        max_repair_attempts_answer: int = 2,
        max_repair_attempts_rule: int = 2,
        max_repair_attempts_backward: int = 1,
        max_repair_attempts_forward: int = 1,
        answer_reject_allow_fallback: bool = False,
        session_svc: SessionService | None = None,
        qa_runtime_bundle: QARuntimeBundle | None = None,
    ) -> None:
        self._rulebase_core_path = rulebase_core_path
        self._evidence_chunks_path = evidence_chunks_path
        self._top_k = rule_retrieval_top_k
        self._nesy_nli_mock = nesy_nli_mock
        self._nli_verifier = nli_verifier
        self._nli_degraded = nli_degraded
        self._nli_meta = dict(nli_meta or {})
        self._entailment_threshold = entailment_threshold
        self._contradiction_threshold = contradiction_threshold
        self._max_repair_attempts_parse = max_repair_attempts_parse
        self._max_repair_attempts_answer = max_repair_attempts_answer
        self._max_repair_attempts_rule = max_repair_attempts_rule
        self._max_repair_attempts_backward = max_repair_attempts_backward
        self._max_repair_attempts_forward = max_repair_attempts_forward
        self._answer_reject_allow_fallback = answer_reject_allow_fallback
        self._session_svc = session_svc
        self._evidence: EvidenceRetriever | None = None
        self._bundle: QARuntimeBundle = qa_runtime_bundle or QARuntimeBundle.from_legacy_rulebase_path(
            str(self._rulebase_core_path),
            domain="enterprise",
        )

    @property
    def runtime_bundle(self) -> QARuntimeBundle:
        return self._bundle

    def _session(self) -> SessionService:
        return self._session_svc or get_session_service()

    def _evidence_retriever(self) -> EvidenceRetriever:
        if self._evidence is None:
            configure_evidence_path(self._evidence_chunks_path)
            self._evidence = EvidenceRetriever(self._evidence_chunks_path)
        return self._evidence

    def _nesy(self) -> NeSyEngine:
        kw = dict(
            nesy_nli_mock=self._nesy_nli_mock,
            nli_degraded=self._nli_degraded,
            nli_meta=self._nli_meta,
            entailment_threshold=self._entailment_threshold,
            contradiction_threshold=self._contradiction_threshold,
        )
        return NeSyEngine(nli=self._nli_verifier, **kw)

    def ask(
        self,
        question: str,
        session_id: str | None,
        user_facts: list[str] | None,
        trace_collector: TraceCollector | None = None,
        question_time: str | None = None,
    ) -> AskResponse:
        return run_ask(
            question=question,
            session_id=session_id,
            user_facts=user_facts or [],
            session_svc=self._session(),
            nesy=self._nesy(),
            rulebase_registry=self._bundle.rulebase_registry,
            domain_retriever=self._bundle.domain_retriever,
            domain_selector=self._bundle.domain_selector,
            retriever_advanced=self._bundle.retriever_advanced,
            evidence_retriever=self._evidence_retriever(),
            top_k=self._top_k,
            max_repair_attempts_parse=self._max_repair_attempts_parse,
            max_repair_attempts_answer=self._max_repair_attempts_answer,
            max_repair_attempts_rule=self._max_repair_attempts_rule,
            max_repair_attempts_backward=self._max_repair_attempts_backward,
            max_repair_attempts_forward=self._max_repair_attempts_forward,
            answer_reject_allow_fallback=self._answer_reject_allow_fallback,
            trace_collector=trace_collector,
            question_time=question_time,
        )

    def clarify(self, session_id: str, answers: list[dict[str, Any]], trace_collector: TraceCollector | None = None) -> ClarifyResponse:
        return run_clarify(
            session_id=session_id,
            answers=answers,
            session_svc=self._session(),
            nesy=self._nesy(),
            rulebase_registry=self._bundle.rulebase_registry,
            domain_retriever=self._bundle.domain_retriever,
            domain_selector=self._bundle.domain_selector,
            retriever_advanced=self._bundle.retriever_advanced,
            evidence_retriever=self._evidence_retriever(),
            top_k=self._top_k,
            max_repair_attempts_parse=self._max_repair_attempts_parse,
            max_repair_attempts_answer=self._max_repair_attempts_answer,
            max_repair_attempts_rule=self._max_repair_attempts_rule,
            max_repair_attempts_backward=self._max_repair_attempts_backward,
            max_repair_attempts_forward=self._max_repair_attempts_forward,
            answer_reject_allow_fallback=self._answer_reject_allow_fallback,
            trace_collector=trace_collector,
        )


def run_ask(
    *,
    question: str,
    session_id: str | None,
    user_facts: list[str],
    session_svc: SessionService | None = None,
    nesy: NeSyEngine | None = None,
    rule_index: RulebaseIndex | None = None,
    rulebase_registry: RulebaseRegistry | None = None,
    domain_retriever: DomainScopedRuleRetriever | None = None,
    retriever_advanced: AdvancedDomainRetriever | None = None,
    domain_selector: SimpleDomainSelector | None = None,
    evidence_retriever: EvidenceRetriever | None = None,
    top_k: int = 8,
    max_repair_attempts_parse: int = 2,
    max_repair_attempts_answer: int = 2,
    max_repair_attempts_rule: int = 2,
    max_repair_attempts_backward: int = 1,
    max_repair_attempts_forward: int = 1,
    answer_reject_allow_fallback: bool = False,
    trace_collector: TraceCollector | None = None,
    question_time: str | None = None,
) -> AskResponse:
    svc = session_svc or get_session_service()
    engine = nesy or NeSyEngine(nesy_nli_mock=True)
    tc = trace_collector or TraceCollector.noop()

    if session_id and (st := svc.get(session_id)):
        session = st
        session.original_question = question or session.original_question
        for f in user_facts:
            session.known_facts[f] = True
    else:
        session = svc.create_session(question, user_facts)
    if not tc._noop:
        tc.session_id = session.session_id

    trace: dict[str, Any] = {"stage": []}

    with tc.span("parse_layer1") as sp_l1:
        layer1 = parse_question_layer1(question)
        sp_l1.output_summary = summarize_layer1_trace(layer1)

    with tc.span("parse_layer2") as sp_l2:
        layer2 = build_layer2(layer1, user_facts=_user_fact_keys(session))
        sp_l2.output_summary = summarize_layer2_trace(layer2)
    session.layer1 = layer1
    session.layer2 = layer2
    trace["stage"].append("parse_done")

    with tc.span("parse_repair") as sp_pr:
        layer1, layer2, v_parse, parse_repair_trace = run_parse_repair_loop(
            engine,
            layer1=layer1,
            layer2=layer2,
            question_text=question,
            user_facts=_user_fact_keys(session),
            max_repair_attempts_parse=max_repair_attempts_parse,
        )
        sp_pr.output_summary = {
            "verify_parse": summarize_verification_trace(v_parse),
            "repair_trace_len": len(parse_repair_trace),
            "repair_trace_tail": parse_repair_trace[-3:] if parse_repair_trace else [],
        }
        sp_pr.decision = v_parse.final_decision
    session.layer1 = layer1
    session.layer2 = layer2
    trace["parse_repair"] = parse_repair_trace
    _merge_verification(session, v_parse)
    ambs = (layer2.diagnostics or {}).get("ambiguities") or []
    if any(a.get("blocking") for a in ambs):
        with tc.span("clarification") as sp_cl:
            prompts = merge_clarification_prompts_unified(build_parse_ambiguity_prompts(ambs), [])
            sp_cl.output_summary = {
                "blocking_parse_ambiguity": True,
                "prompt_count": len(prompts),
                "target_kinds": [str((p if isinstance(p, dict) else {}).get("target_kind", "")) for p in prompts[:8]],
            }
        session.clarification_questions = prompts
        svc.save(session)
        _merge_pipeline_trace_dict(trace, tc)
        return AskResponse(
            session_id=session.session_id,
            needs_clarification=True,
            clarification_questions=[ClarificationPrompt.model_validate(p) for p in prompts],
            layer1=layer1,
            layer2=layer2,
            verification_trace=session.verification_logs,
            debug_trace=trace | {"stage": "parse_ambiguity_blocking"},
        )
    if v_parse.final_decision == "REJECT":
        with tc.span("pipeline_exit") as spx:
            spx.output_summary = {"reason": "parse_rejected"}
        svc.save(session)
        _merge_pipeline_trace_dict(trace, tc)
        return AskResponse(
            session_id=session.session_id,
            needs_clarification=False,
            verification_trace=session.verification_logs,
            layer1=layer1,
            layer2=layer2,
            debug_trace=trace | {"error": "parse_rejected"},
        )

    selector = domain_selector or SimpleDomainSelector()
    routing = selector.select(
        {"layer1": layer1, "layer2": layer2, "question": question},
        registry=rulebase_registry,
    )
    if not isinstance(routing, DomainRoutingPlan):
        routing = DomainRoutingPlan.model_validate(routing)
    trace["domain_routing"] = routing.model_dump(mode="json")

    policy = default_policy_for_routing(
        allow_cross_domain_expansion=routing.allow_cross_domain_expansion,
        triggered_bridges=list(routing.triggered_bridges),
    )

    with tc.span("retrieve_rules") as sp_rr:
        ranked: list[tuple[RuleRecord, float, dict[str, Any]]]
        merged_index: RulebaseIndex
        if rulebase_registry is not None and retriever_advanced is not None:
            ret_res, ranked_all, ri_full = retriever_advanced.retrieve(
                layer1, layer2, routing, top_k_final=top_k
            )
            trace["retrieval_result"] = ret_res.model_dump(mode="json")
            ranked_primary, rejected_pf = filter_ranked_for_primary_phase(
                ranked_all,
                primary_domains=list(routing.primary_domains),
                include_shared=routing.include_shared,
            )
            ranked, _exp, _used_dom = merge_secondary_with_policy(
                ranked_primary,
                ranked_all,
                secondary_domains=list(routing.secondary_domains),
                policy=policy,
                triggered_bridges=list(routing.triggered_bridges),
            )
            trace["rejected_candidates_domain_filter"] = rejected_pf[:32]
            ri = ri_full
            merged_index = ri_full
        elif rulebase_registry is not None and domain_retriever is not None:
            ranked_all, merged_index = domain_retriever.retrieve(
                layer1,
                layer2,
                list(routing.primary_domains),
                include_shared=routing.include_shared,
                top_k=top_k,
            )
            ranked_primary, rejected_pf = filter_ranked_for_primary_phase(
                ranked_all,
                primary_domains=list(routing.primary_domains),
                include_shared=routing.include_shared,
            )
            ranked, _exp, _used_dom = merge_secondary_with_policy(
                ranked_primary,
                ranked_all,
                secondary_domains=list(routing.secondary_domains),
                policy=policy,
                triggered_bridges=list(routing.triggered_bridges),
            )
            trace["rejected_candidates_domain_filter"] = rejected_pf[:32]
            ri = merged_index
        else:
            ri = rule_index or get_rulebase_index()
            ranked_all = retrieve_rules(layer1=layer1, layer2=layer2, top_k=top_k, index=ri)
            ranked_all = enrich_ranked_with_retrieval_meta(ranked_all)
            ranked_primary, rejected_pf = filter_ranked_for_primary_phase(
                ranked_all,
                primary_domains=list(routing.primary_domains),
                include_shared=routing.include_shared,
            )
            ranked, _exp, _used_dom = merge_secondary_with_policy(
                ranked_primary,
                ranked_all,
                secondary_domains=list(routing.secondary_domains),
                policy=policy,
                triggered_bridges=list(routing.triggered_bridges),
            )
            trace["rejected_candidates_domain_filter"] = rejected_pf[:32]
            merged_index = ri
        session.retrieved_rules = [r for r, _, _ in ranked]
        sp_rr.output_summary = {
            "domain_routing": routing.model_dump(mode="json"),
            "top_rule_ids": [r.rule_id for r, _, _ in ranked[:8]],
            "top": [
                {
                    "rule_id": r.rule_id,
                    "score_total": s,
                    "matched_features": (d.get("matched_features") or [])[:12],
                    "score_components": d.get("score_components") or {},
                    "rulebase_id": d.get("rulebase_id"),
                    "domain": d.get("domain"),
                    "layer": d.get("layer"),
                    "source_doc": d.get("source_doc"),
                    "source_article": d.get("source_article"),
                    "retrieval_scope": d.get("retrieval_scope"),
                }
                for r, s, d in ranked[: min(8, len(ranked))]
            ],
        }
    trace["stage"].append("retrieve_done")
    trace["rule_retrieval"] = {
        "backend": "advanced_domain_per_scope" if retriever_advanced is not None else "hybrid_bm25_structured",
        "top": (sp_rr.output_summary or {}).get("top", []),
    }
    trace["retrieved_rules_by_domain"] = _group_retrieved_by_domain(ranked)

    # Phase 3: Apply temporal, conflict, and bridge filtering post-retrieval
    with tc.span("phase3_post_retrieve") as sp_p3:
        p3_result = apply_phase3_post_retrieve(
            ranked=ranked,
            session=session,
            question=question,
            routing=routing,
            rulebase_registry=rulebase_registry,
            question_time_explicit=question_time,
            trace=trace,
        )
        ranked = p3_result.ranked
        trace["phase3"] = {
            "question_time_utc": p3_result.question_time_iso,
            "temporal_rejected": p3_result.temporal_rejected[:16],
            "conflict_rejected": p3_result.conflict_rejected[:16],
            "bridge_emitted": [x.model_dump(mode="json") for x in p3_result.bridge_emitted],
            "rule_id_collision_warnings": p3_result.rule_id_collision_warnings,
        }
        sp_p3.output_summary = {
            "question_time": p3_result.question_time_iso,
            "temporal_rejected_count": len(p3_result.temporal_rejected),
            "conflict_rejected_count": len(p3_result.conflict_rejected),
            "bridge_emitted_count": len(p3_result.bridge_emitted),
            "final_ranked_count": len(ranked),
        }

    ctx = ReasoningContext(
        primary_domains=list(routing.primary_domains),
        secondary_domains=list(routing.secondary_domains),
        active_rulebases=collect_rulebase_ids_from_index(merged_index.rules),
        include_shared=routing.include_shared,
        question_time=question_time or p3_result.question_time_iso,
        statute_ids=[],
        cross_domain_policy=policy,
        triggered_bridges=list(routing.triggered_bridges),
    )
    trace["reasoning_context"] = ctx.to_trace_dict()

    goal = layer2.goal

    with tc.span("rule_backward_gate") as sp_b:
        rg = gate_rule_and_backward(
            engine,
            goal=goal,
            layer2=layer2,
            ranked=ranked,
            known_facts=known_facts_for_reasoning(session),
            rule_index=ri,
            max_rule_repair=max_repair_attempts_rule,
            max_backward_repair=max_repair_attempts_backward,
            reasoning_context=ctx,
            cross_domain_policy=policy,
            structured_facts=structured_facts_for_reasoning(session),
        )
        trace["rule_backward_gate"] = rg.trace
        if rg.v_rule:
            _merge_verification(session, rg.v_rule)
        if rg.v_back:
            _merge_verification(session, rg.v_back)
        sp_b.output_summary = {
            "gate_ok": rg.ok,
            "clarification_needed": rg.clarification_needed,
            "tried_rule_ids": rg.tried_rule_ids,
            "error": rg.error,
            "verify_rule": summarize_verification_trace(rg.v_rule) if rg.v_rule else {},
            "verify_backward": summarize_verification_trace(rg.v_back) if rg.v_back else {},
        }
        sp_b.decision = rg.v_back.final_decision if rg.v_back else "none"

    if not rg.ok:
        with tc.span("pipeline_exit") as spx:
            spx.output_summary = {"reason": rg.error or "rule_backward_gate_failed"}
        
        # Build partial reasoning_result even in error case
        error_reasoning_result = _finalize_reasoning_result_dict(
            {"active_domains_used": list(ctx.primary_domains)},
            proof=None,
            ranked=ranked,
            bstate=None,
            fstate=None,
            selected=None,
            phase3_result=p3_result,
        )
        
        svc.save(session)
        _merge_pipeline_trace_dict(trace, tc)
        return AskResponse(
            session_id=session.session_id,
            needs_clarification=False,
            verification_trace=session.verification_logs,
            layer1=layer1,
            layer2=layer2,
            retrieved_rules=[_rule_dump(r) for r, s, d in ranked[:8]],
            reasoning_result=error_reasoning_result,
            debug_trace=trace
            | {
                "error": rg.error or "reasoning_blocked_by_rule_verification",
                "tried_rule_ids": rg.tried_rule_ids,
            },
        )

    selected = rg.selected
    bstate = rg.bstate
    session.reasoning = bstate
    session.selected_rule = selected

    if rg.clarification_needed and bstate:
        with tc.span("clarification") as sp_cl:
            parse_ambs = (layer2.diagnostics or {}).get("ambiguities") or []
            parse_prompts = build_parse_ambiguity_prompts([a for a in parse_ambs if not a.get("blocking")])
            backward_prompts = build_clarification_prompts_from_requirements(
                bstate.missing_facts,
                bstate.requirement_set,
                backward_plan=bstate.backward_plan,
                related_rule_id=selected.rule_id if selected else None,
            )
            prompts = merge_clarification_prompts_unified(parse_prompts, backward_prompts)
            sp_cl.output_summary = {
                "backward_missing_facts": True,
                "prompt_count": len(prompts),
                "missing_facts": bstate.missing_facts,
            }
        session.missing_facts = bstate.missing_facts
        session.clarification_questions = prompts
        
        # Build partial reasoning_result for clarification case
        clarify_reasoning_result = _finalize_reasoning_result_dict(
            {"active_domains_used": list(ctx.primary_domains)},
            proof=None,
            ranked=ranked,
            bstate=bstate,
            fstate=None,
            selected=selected,
            phase3_result=p3_result,
        )
        
        svc.save(session)
        _merge_pipeline_trace_dict(trace, tc)
        return AskResponse(
            session_id=session.session_id,
            needs_clarification=True,
            clarification_questions=[ClarificationPrompt.model_validate(p) for p in prompts],
            layer1=layer1,
            layer2=layer2,
            verification_trace=session.verification_logs,
            retrieved_rules=[_rule_dump(r) for r, s, d in ranked[:8]],
            selected_rule=_rule_dump(selected) if selected else None,
            reasoning=bstate,
            reasoning_result=clarify_reasoning_result,
            debug_trace=trace | {"stage": "needs_clarification"},
        )

    assert selected is not None and bstate is not None

    with tc.span("forward_gate") as sp_f:
        fg = gate_forward_reasoning(
            engine,
            goal=goal,
            selected=selected,
            ranked=ranked,
            session=session,
            known_facts=known_facts_for_reasoning(session),
            backward_plan_dict=bstate.backward_plan,
            max_forward_repair=max_repair_attempts_forward,
            reasoning_context=ctx,
            cross_domain_policy=policy,
            phase3_proof_context=p3_result.proof_phase3_context,
        )
        trace["forward_gate"] = fg.trace
        if fg.v_fwd:
            _merge_verification(session, fg.v_fwd)
        sp_f.output_summary = {
            "gate_ok": fg.ok,
            "verify_forward": summarize_verification_trace(fg.v_fwd) if fg.v_fwd else {},
            "error": fg.error,
        }
        sp_f.decision = fg.v_fwd.final_decision if fg.v_fwd else "none"

    if not fg.ok:
        with tc.span("pipeline_exit") as spx:
            spx.output_summary = {"reason": fg.error or "forward_verification_failed"}
        
        # Build partial reasoning_result for forward gate failure
        fg_fail_reasoning_result = _finalize_reasoning_result_dict(
            {"active_domains_used": list(ctx.primary_domains)},
            proof=None,
            ranked=ranked,
            bstate=bstate,
            fstate=None,
            selected=selected,
            phase3_result=p3_result,
        )
        
        svc.save(session)
        _merge_pipeline_trace_dict(trace, tc)
        return AskResponse(
            session_id=session.session_id,
            needs_clarification=False,
            verification_trace=session.verification_logs,
            layer1=layer1,
            layer2=layer2,
            retrieved_rules=[_rule_dump(r) for r, s, d in ranked[:8]],
            selected_rule=_rule_dump(selected),
            reasoning=bstate,
            reasoning_result=fg_fail_reasoning_result,
            debug_trace=trace | {"error": fg.error or "forward_verification_failed"},
        )

    conclusion = fg.conclusion
    goal_ok = fg.goal_achieved
    fstate = fg.fstate
    proof = fg.proof_obj
    session.reasoning = fstate
    session.proof = proof
    if fstate and fstate.forward_result and fstate.forward_result.get("rule_id"):
        _by_id = {r.rule_id: r for r, _, _ in ranked}
        selected = _by_id.get(fstate.forward_result["rule_id"], selected)
    session.selected_rule = selected

    with tc.span("proof") as sp_p:
        sp_p.output_summary = {
            "proof_id": proof.proof_id,
            "step_count": len(proof.proof_steps or []),
            "derived_conclusion_excerpt": (proof.derived_conclusion or "")[:300],
        }
    trace["proof_steps_by_domain"] = _proof_steps_by_domain(proof)

    with tc.span("retrieve_evidence") as sp_ev:
        ev = (evidence_retriever or get_evidence_retriever()).retrieve(
            question=question,
            rule=selected,
            conclusion=conclusion,
            top_k=5,
            proof_summary=_proof_summary_for_evidence(proof),
            goal=goal,
            modality_text=layer1.modality_text or "",
            layer1=layer1,
            layer2=layer2,
        )
        sp_ev.output_summary = summarize_evidence_trace(ev)
    trace["final_grounding_docs"] = _grounding_docs_from_evidence(ev)

    with tc.span("generate_answer") as sp_ga:
        ans = generate_answer(
            question=question,
            conclusion=conclusion,
            proof=proof,
            evidence=ev,
            goal_achieved=goal_ok,
            rule=selected,
        )
        sp_ga.output_summary = summarize_answer_trace(ans)

    with tc.span("answer_repair") as sp_ar:
        ans_text, v_ans, answer_repair_trace = run_answer_repair_loop(
            engine,
            answer_text=ans.answer_text,
            conclusion=conclusion,
            proof=proof.model_dump(mode="json"),
            modality_expected=layer1.modality_text or "",
            goal_action=str(goal.get("args", ["", "", ""])[1] if len(goal.get("args", [])) > 1 else ""),
            action_token_in_answer=ans.answer_text,
            max_repair_attempts_answer=max_repair_attempts_answer,
        )
        apply_answer_text_and_refresh_citations(ans, ans_text)
        ans.verification_summary += f";answer_repair_attempts={answer_repair_trace[-1].get('attempts_used', 0)}"
        trace["answer_repair"] = answer_repair_trace
        _merge_verification(session, v_ans)
        sp_ar.output_summary = {
            "verify_answer": summarize_verification_trace(v_ans),
            "attempts_used": answer_repair_trace[-1].get("attempts_used", 0) if answer_repair_trace else 0,
            "trace_tail": answer_repair_trace[-2:] if answer_repair_trace else [],
        }
        sp_ar.decision = v_ans.final_decision

    if v_ans.final_decision == "REJECT" and answer_reject_allow_fallback:
        reg = safe_regenerate_final_answer(
            conclusion,
            proof=proof,
            evidence=ev,
            rule=selected,
            goal_achieved=goal_ok,
        )
        reg.verification_summary = ans.verification_summary + ";answer_fallback_regenerate_on_reject"
        ans = reg
    elif v_ans.final_decision == "REJECT":
        ans.verification_summary += ";answer_verification_rejected_no_fallback"
        trace["answer_verification"] = {"final_decision": "REJECT", "note": "no_fallback_per_policy"}

    session.answer = ans
    
    # Build ReasoningResult as first-class artifact
    reasoning_result_dict: dict[str, Any] = {
        "active_domains_used": list(ctx.primary_domains),
    }
    reasoning_result_data = _finalize_reasoning_result_dict(
        reasoning_result_dict,
        proof=proof,
        ranked=ranked,
        bstate=bstate,
        fstate=fstate,
        selected=selected,
        phase3_result=p3_result,
    )
    trace["reasoning_result"] = reasoning_result_data
    
    trace["stage"].append("complete")
    session.pipeline_trace = trace
    _merge_pipeline_trace_dict(trace, tc)
    svc.save(session)

    return AskResponse(
        session_id=session.session_id,
        needs_clarification=False,
        layer1=layer1,
        layer2=layer2,
        verification_trace=session.verification_logs,
        retrieved_rules=[_rule_dump(r) for r, s, d in ranked[:8]],
        selected_rule=_rule_dump(selected),
        reasoning=fstate,
        proof=proof,
        answer=ans,
        reasoning_result=reasoning_result_data,
        debug_trace=trace,
    )


def run_clarify(
    *,
    session_id: str,
    answers: list[dict[str, Any]],
    session_svc: SessionService | None = None,
    nesy: NeSyEngine | None = None,
    rule_index: RulebaseIndex | None = None,
    rulebase_registry: RulebaseRegistry | None = None,
    domain_retriever: DomainScopedRuleRetriever | None = None,
    retriever_advanced: AdvancedDomainRetriever | None = None,
    domain_selector: SimpleDomainSelector | None = None,
    evidence_retriever: EvidenceRetriever | None = None,
    top_k: int = 8,
    max_repair_attempts_parse: int = 2,
    max_repair_attempts_answer: int = 2,
    max_repair_attempts_rule: int = 2,
    max_repair_attempts_backward: int = 1,
    max_repair_attempts_forward: int = 1,
    answer_reject_allow_fallback: bool = False,
    trace_collector: TraceCollector | None = None,
) -> ClarifyResponse:
    svc = session_svc or get_session_service()
    engine = nesy or NeSyEngine(nesy_nli_mock=True)
    tc = trace_collector or TraceCollector.noop()
    session = svc.get(session_id)
    if not session:
        raise KeyError("session_not_found")

    svc.merge_fact_answers(session, answers)
    question = session.original_question
    if not tc._noop:
        tc.question_text = question or ""
        tc.session_id = session_id

    forced = extract_resolved_condition_atoms_from_known_facts(session.known_facts)

    with tc.span("parse_layer1") as sp_l1:
        layer1 = session.layer1 or parse_question_layer1(question)
        sp_l1.output_summary = summarize_layer1_trace(layer1)

    with tc.span("parse_layer2") as sp_l2:
        layer2 = build_layer2(
            layer1,
            user_facts=_user_fact_keys(session),
            forced_condition_atoms=forced if forced else None,
        )
        sp_l2.output_summary = summarize_layer2_trace(layer2)
    session.layer1 = layer1
    session.layer2 = layer2

    trace: dict[str, Any] = {"stage": ["clarify_resume"]}

    with tc.span("parse_repair") as sp_pr:
        layer1, layer2, _v_parse_cl, parse_repair_trace = run_parse_repair_loop(
            engine,
            layer1=layer1,
            layer2=layer2,
            question_text=question,
            user_facts=_user_fact_keys(session),
            max_repair_attempts_parse=max_repair_attempts_parse,
        )
        sp_pr.output_summary = {
            "verify_parse": summarize_verification_trace(_v_parse_cl),
            "repair_trace_len": len(parse_repair_trace),
        }
        sp_pr.decision = _v_parse_cl.final_decision
    session.layer1 = layer1
    session.layer2 = layer2
    trace["parse_repair"] = parse_repair_trace
    _merge_verification(session, _v_parse_cl)
    if _v_parse_cl.final_decision == "REJECT":
        with tc.span("pipeline_exit") as spx:
            spx.output_summary = {"reason": "parse_rejected"}
        svc.save(session)
        _merge_pipeline_trace_dict(trace, tc)
        return ClarifyResponse(
            session_id=session.session_id,
            verification_trace=session.verification_logs,
            layer1=layer1,
            layer2=layer2,
            debug_trace=trace | {"error": "parse_rejected"},
        )

    selector = domain_selector or SimpleDomainSelector()
    routing = selector.select(
        {"layer1": layer1, "layer2": layer2, "question": question},
        registry=rulebase_registry,
    )
    if not isinstance(routing, DomainRoutingPlan):
        routing = DomainRoutingPlan.model_validate(routing)
    trace["domain_routing"] = routing.model_dump(mode="json")

    policy = default_policy_for_routing(
        allow_cross_domain_expansion=routing.allow_cross_domain_expansion,
        triggered_bridges=list(routing.triggered_bridges),
    )

    with tc.span("retrieve_rules") as sp_rr:
        ranked: list[tuple[RuleRecord, float, dict[str, Any]]]
        merged_index: RulebaseIndex
        if rulebase_registry is not None and retriever_advanced is not None:
            ret_res, ranked_all, ri_full = retriever_advanced.retrieve(
                layer1, layer2, routing, top_k_final=top_k
            )
            trace["retrieval_result"] = ret_res.model_dump(mode="json")
            ranked_primary, rejected_pf = filter_ranked_for_primary_phase(
                ranked_all,
                primary_domains=list(routing.primary_domains),
                include_shared=routing.include_shared,
            )
            ranked, _exp, _used_dom = merge_secondary_with_policy(
                ranked_primary,
                ranked_all,
                secondary_domains=list(routing.secondary_domains),
                policy=policy,
                triggered_bridges=list(routing.triggered_bridges),
            )
            trace["rejected_candidates_domain_filter"] = rejected_pf[:32]
            ri = ri_full
            merged_index = ri_full
        elif rulebase_registry is not None and domain_retriever is not None:
            ranked_all, merged_index = domain_retriever.retrieve(
                layer1,
                layer2,
                list(routing.primary_domains),
                include_shared=routing.include_shared,
                top_k=top_k,
            )
            ranked_primary, rejected_pf = filter_ranked_for_primary_phase(
                ranked_all,
                primary_domains=list(routing.primary_domains),
                include_shared=routing.include_shared,
            )
            ranked, _exp, _used_dom = merge_secondary_with_policy(
                ranked_primary,
                ranked_all,
                secondary_domains=list(routing.secondary_domains),
                policy=policy,
                triggered_bridges=list(routing.triggered_bridges),
            )
            trace["rejected_candidates_domain_filter"] = rejected_pf[:32]
            ri = merged_index
        else:
            ri = rule_index or get_rulebase_index()
            ranked_all = retrieve_rules(layer1=layer1, layer2=layer2, top_k=top_k, index=ri)
            ranked_all = enrich_ranked_with_retrieval_meta(ranked_all)
            ranked_primary, rejected_pf = filter_ranked_for_primary_phase(
                ranked_all,
                primary_domains=list(routing.primary_domains),
                include_shared=routing.include_shared,
            )
            ranked, _exp, _used_dom = merge_secondary_with_policy(
                ranked_primary,
                ranked_all,
                secondary_domains=list(routing.secondary_domains),
                policy=policy,
                triggered_bridges=list(routing.triggered_bridges),
            )
            trace["rejected_candidates_domain_filter"] = rejected_pf[:32]
            merged_index = ri
        session.retrieved_rules = [r for r, _, _ in ranked]
        sp_rr.output_summary = {
            "domain_routing": routing.model_dump(mode="json"),
            "top_rule_ids": [r.rule_id for r, _, _ in ranked[:8]],
            "top": [
                {
                    "rule_id": r.rule_id,
                    "score_total": s,
                    "matched_features": (d.get("matched_features") or [])[:12],
                    "score_components": d.get("score_components") or {},
                    "rulebase_id": d.get("rulebase_id"),
                    "domain": d.get("domain"),
                    "layer": d.get("layer"),
                    "source_doc": d.get("source_doc"),
                    "source_article": d.get("source_article"),
                    "retrieval_scope": d.get("retrieval_scope"),
                }
                for r, s, d in ranked[: min(8, len(ranked))]
            ],
        }
    trace["rule_retrieval"] = {
        "backend": "advanced_domain_per_scope" if retriever_advanced is not None else "hybrid_bm25_structured",
        "top": (sp_rr.output_summary or {}).get("top", []),
    }
    trace["retrieved_rules_by_domain"] = _group_retrieved_by_domain(ranked)

    ctx = ReasoningContext(
        primary_domains=list(routing.primary_domains),
        secondary_domains=list(routing.secondary_domains),
        active_rulebases=collect_rulebase_ids_from_index(merged_index.rules),
        include_shared=routing.include_shared,
        question_time=None,
        statute_ids=[],
        cross_domain_policy=policy,
        triggered_bridges=list(routing.triggered_bridges),
    )
    trace["reasoning_context"] = ctx.to_trace_dict()

    goal = layer2.goal

    with tc.span("rule_backward_gate") as sp_b:
        rg = gate_rule_and_backward(
            engine,
            goal=goal,
            layer2=layer2,
            ranked=ranked,
            known_facts=known_facts_for_reasoning(session),
            rule_index=ri,
            max_rule_repair=max_repair_attempts_rule,
            max_backward_repair=max_repair_attempts_backward,
            reasoning_context=ctx,
            cross_domain_policy=policy,
            structured_facts=structured_facts_for_reasoning(session),
        )
        trace["rule_backward_gate"] = rg.trace
        if rg.v_rule:
            _merge_verification(session, rg.v_rule)
        if rg.v_back:
            _merge_verification(session, rg.v_back)
        sp_b.output_summary = {
            "gate_ok": rg.ok,
            "clarification_needed": rg.clarification_needed,
            "tried_rule_ids": rg.tried_rule_ids,
            "error": rg.error,
            "verify_rule": summarize_verification_trace(rg.v_rule) if rg.v_rule else {},
            "verify_backward": summarize_verification_trace(rg.v_back) if rg.v_back else {},
        }
        sp_b.decision = rg.v_back.final_decision if rg.v_back else "none"

    if not rg.ok:
        with tc.span("pipeline_exit") as spx:
            spx.output_summary = {"reason": rg.error or "rule_backward_gate_failed"}
        svc.save(session)
        _merge_pipeline_trace_dict(trace, tc)
        return ClarifyResponse(
            session_id=session.session_id,
            verification_trace=session.verification_logs,
            reasoning=rg.bstate,
            debug_trace=trace
            | {
                "error": rg.error or "reasoning_blocked_by_rule_verification",
                "tried_rule_ids": rg.tried_rule_ids,
            },
        )

    selected = rg.selected
    bstate = rg.bstate
    session.reasoning = bstate
    session.selected_rule = selected

    if rg.clarification_needed and bstate:
        with tc.span("clarification") as sp_cl:
            parse_ambs = (layer2.diagnostics or {}).get("ambiguities") or []
            parse_prompts = build_parse_ambiguity_prompts([a for a in parse_ambs if not a.get("blocking")])
            backward_prompts = build_clarification_prompts_from_requirements(
                bstate.missing_facts,
                bstate.requirement_set,
                backward_plan=bstate.backward_plan,
                related_rule_id=selected.rule_id if selected else None,
            )
            prompts = merge_clarification_prompts_unified(parse_prompts, backward_prompts)
            sp_cl.output_summary = {"prompt_count": len(prompts), "missing_facts": bstate.missing_facts}
        session.missing_facts = bstate.missing_facts
        session.clarification_questions = prompts
        svc.save(session)
        _merge_pipeline_trace_dict(trace, tc)
        return ClarifyResponse(
            session_id=session.session_id,
            needs_clarification=True,
            clarification_questions=[ClarificationPrompt.model_validate(p) for p in prompts],
            verification_trace=session.verification_logs,
            layer1=layer1,
            layer2=layer2,
            selected_rule=_rule_dump(selected) if selected else None,
            reasoning=bstate,
            debug_trace=trace,
        )

    assert selected is not None and bstate is not None

    with tc.span("forward_gate") as sp_f:
        fg = gate_forward_reasoning(
            engine,
            goal=goal,
            selected=selected,
            ranked=ranked,
            session=session,
            known_facts=known_facts_for_reasoning(session),
            backward_plan_dict=bstate.backward_plan,
            max_forward_repair=max_repair_attempts_forward,
            reasoning_context=ctx,
            cross_domain_policy=policy,
        )
        trace["forward_gate"] = fg.trace
        if fg.v_fwd:
            _merge_verification(session, fg.v_fwd)
        sp_f.output_summary = {
            "gate_ok": fg.ok,
            "verify_forward": summarize_verification_trace(fg.v_fwd) if fg.v_fwd else {},
            "error": fg.error,
        }
        sp_f.decision = fg.v_fwd.final_decision if fg.v_fwd else "none"

    if not fg.ok:
        with tc.span("pipeline_exit") as spx:
            spx.output_summary = {"reason": fg.error or "forward_verification_failed"}
        svc.save(session)
        _merge_pipeline_trace_dict(trace, tc)
        return ClarifyResponse(
            session_id=session.session_id,
            verification_trace=session.verification_logs,
            layer1=layer1,
            layer2=layer2,
            selected_rule=_rule_dump(selected),
            reasoning=bstate,
            debug_trace=trace | {"error": fg.error or "forward_verification_failed"},
        )

    conclusion = fg.conclusion
    goal_ok = fg.goal_achieved
    fstate = fg.fstate
    proof = fg.proof_obj
    session.reasoning = fstate
    session.proof = proof
    if fstate and fstate.forward_result and fstate.forward_result.get("rule_id"):
        _by_id = {r.rule_id: r for r, _, _ in ranked}
        selected = _by_id.get(fstate.forward_result["rule_id"], selected)
    session.selected_rule = selected

    with tc.span("proof") as sp_p:
        sp_p.output_summary = {
            "proof_id": proof.proof_id,
            "step_count": len(proof.proof_steps or []),
        }
    trace["proof_steps_by_domain"] = _proof_steps_by_domain(proof)

    with tc.span("retrieve_evidence") as sp_ev:
        ev = (evidence_retriever or get_evidence_retriever()).retrieve(
            question=question,
            rule=selected,
            conclusion=conclusion,
            top_k=5,
            proof_summary=_proof_summary_for_evidence(proof),
            goal=goal,
            modality_text=layer1.modality_text or "",
            layer1=layer1,
            layer2=layer2,
        )
        sp_ev.output_summary = summarize_evidence_trace(ev)
    trace["final_grounding_docs"] = _grounding_docs_from_evidence(ev)

    with tc.span("generate_answer") as sp_ga:
        ans = generate_answer(
            question=question,
            conclusion=conclusion,
            proof=proof,
            evidence=ev,
            goal_achieved=goal_ok,
            rule=selected,
        )
        sp_ga.output_summary = summarize_answer_trace(ans)

    with tc.span("answer_repair") as sp_ar:
        ans_text, v_ans, answer_repair_trace = run_answer_repair_loop(
            engine,
            answer_text=ans.answer_text,
            conclusion=conclusion,
            proof=proof.model_dump(mode="json"),
            modality_expected=layer1.modality_text or "",
            goal_action=str(goal.get("args", ["", "", ""])[1] if len(goal.get("args", [])) > 1 else ""),
            action_token_in_answer=ans.answer_text,
            max_repair_attempts_answer=max_repair_attempts_answer,
        )
        apply_answer_text_and_refresh_citations(ans, ans_text)
        ans.verification_summary += f";answer_repair_attempts={answer_repair_trace[-1].get('attempts_used', 0)}"
        trace["answer_repair"] = answer_repair_trace
        _merge_verification(session, v_ans)
        sp_ar.output_summary = {
            "verify_answer": summarize_verification_trace(v_ans),
            "attempts_used": answer_repair_trace[-1].get("attempts_used", 0) if answer_repair_trace else 0,
        }
        sp_ar.decision = v_ans.final_decision

    if v_ans.final_decision == "REJECT" and answer_reject_allow_fallback:
        reg = safe_regenerate_final_answer(
            conclusion,
            proof=proof,
            evidence=ev,
            rule=selected,
            goal_achieved=goal_ok,
        )
        reg.verification_summary = ans.verification_summary + ";answer_fallback_regenerate_on_reject"
        ans = reg
    elif v_ans.final_decision == "REJECT":
        ans.verification_summary += ";answer_verification_rejected_no_fallback"
        trace["answer_verification"] = {"final_decision": "REJECT", "note": "no_fallback_per_policy"}

    session.answer = ans
    session.pipeline_trace = trace
    _merge_pipeline_trace_dict(trace, tc)
    svc.save(session)

    return ClarifyResponse(
        session_id=session.session_id,
        needs_clarification=False,
        layer1=layer1,
        layer2=layer2,
        verification_trace=session.verification_logs,
        retrieved_rules=[_rule_dump(r) for r, s, d in ranked[:8]],
        selected_rule=_rule_dump(selected),
        reasoning=fstate,
        proof=proof,
        answer=ans,
        debug_trace=trace,
    )
