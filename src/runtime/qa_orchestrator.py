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
)
from question_side.question_normalizer import build_layer2
from question_side.question_parser import parse_question_layer1
from retrieval.evidence_retriever import (
    EvidenceRetriever,
    configure_evidence_path,
    get_evidence_retriever,
)
from retrieval.rule_retriever import retrieve_rules
from retrieval.rulebase_loader import RulebaseIndex, configure_rulebase_path, get_rulebase_index, load_rulebase
from schemas.http_response import AskResponse, ClarificationPrompt, ClarifyResponse
from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleRecord
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
        trace["pipeline_trace"] = tc.to_dict()


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
        self._rule_index: RulebaseIndex | None = None
        self._evidence: EvidenceRetriever | None = None

    def _session(self) -> SessionService:
        return self._session_svc or get_session_service()

    def _index(self) -> RulebaseIndex:
        if self._rule_index is None:
            configure_rulebase_path(self._rulebase_core_path)
            self._rule_index = load_rulebase(self._rulebase_core_path)
        return self._rule_index

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
    ) -> AskResponse:
        return run_ask(
            question=question,
            session_id=session_id,
            user_facts=user_facts or [],
            session_svc=self._session(),
            nesy=self._nesy(),
            rule_index=self._index(),
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

    def clarify(self, session_id: str, answers: list[dict[str, Any]], trace_collector: TraceCollector | None = None) -> ClarifyResponse:
        return run_clarify(
            session_id=session_id,
            answers=answers,
            session_svc=self._session(),
            nesy=self._nesy(),
            rule_index=self._index(),
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
    evidence_retriever: EvidenceRetriever | None = None,
    top_k: int = 8,
    max_repair_attempts_parse: int = 2,
    max_repair_attempts_answer: int = 2,
    max_repair_attempts_rule: int = 2,
    max_repair_attempts_backward: int = 1,
    max_repair_attempts_forward: int = 1,
    answer_reject_allow_fallback: bool = False,
    trace_collector: TraceCollector | None = None,
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

    with tc.span("retrieve_rules") as sp_rr:
        ranked = retrieve_rules(layer1=layer1, layer2=layer2, top_k=top_k, index=rule_index)
        session.retrieved_rules = [r for r, _, _ in ranked]
        sp_rr.output_summary = {
            "top_rule_ids": [r.rule_id for r, _, _ in ranked[:8]],
            "top": [
                {
                    "rule_id": r.rule_id,
                    "score_total": s,
                    "matched_features": (d.get("matched_features") or [])[:12],
                    "score_components": d.get("score_components") or {},
                }
                for r, s, d in ranked[: min(8, len(ranked))]
            ],
        }
    trace["stage"].append("retrieve_done")
    trace["rule_retrieval"] = {
        "backend": "hybrid_bm25_structured",
        "top": (sp_rr.output_summary or {}).get("top", []),
    }

    goal = layer2.goal
    ri = rule_index or get_rulebase_index()

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
        return AskResponse(
            session_id=session.session_id,
            needs_clarification=False,
            verification_trace=session.verification_logs,
            layer1=layer1,
            layer2=layer2,
            retrieved_rules=[_rule_dump(r) for r, s, d in ranked[:8]],
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
        return AskResponse(
            session_id=session.session_id,
            needs_clarification=False,
            verification_trace=session.verification_logs,
            layer1=layer1,
            layer2=layer2,
            retrieved_rules=[_rule_dump(r) for r, s, d in ranked[:8]],
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
            "derived_conclusion_excerpt": (proof.derived_conclusion or "")[:300],
        }

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
        debug_trace=trace,
    )


def run_clarify(
    *,
    session_id: str,
    answers: list[dict[str, Any]],
    session_svc: SessionService | None = None,
    nesy: NeSyEngine | None = None,
    rule_index: RulebaseIndex | None = None,
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

    with tc.span("retrieve_rules") as sp_rr:
        ranked = retrieve_rules(layer1=layer1, layer2=layer2, top_k=top_k, index=rule_index)
        session.retrieved_rules = [r for r, _, _ in ranked]
        sp_rr.output_summary = {
            "top_rule_ids": [r.rule_id for r, _, _ in ranked[:8]],
            "top": [
                {
                    "rule_id": r.rule_id,
                    "score_total": s,
                    "matched_features": (d.get("matched_features") or [])[:12],
                    "score_components": d.get("score_components") or {},
                }
                for r, s, d in ranked[: min(8, len(ranked))]
            ],
        }
    trace["rule_retrieval"] = {
        "backend": "hybrid_bm25_structured",
        "top": (sp_rr.output_summary or {}).get("top", []),
    }

    goal = layer2.goal
    ri = rule_index or get_rulebase_index()

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
