"""End-to-end QA orchestration: parse → verify → retrieve → backward → clarify → forward → proof → evidence → answer."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from generation.answer_generator import generate_answer, safe_regenerate_answer
from reasoning.backward_reasoner import run_backward
from reasoning.clarification_manager import (
    build_clarification_prompts_from_requirements,
    build_parse_ambiguity_prompts,
    merge_clarification_prompts_unified,
)
from reasoning.forward_reasoner import run_forward
from reasoning.proof_builder import build_proof
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
from retrieval.rulebase_loader import RulebaseIndex, configure_rulebase_path, load_rulebase
from schemas.http_response import AskResponse, ClarificationPrompt, ClarifyResponse
from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleRecord
from schemas.session import SessionState
from schemas.verification import VerificationRecord
from session.session_service import SessionService, get_session_service
from verification.engine import NeSyEngine
from verification.nli_verifier import NLIVerifier
from verification.repair_loop import run_answer_repair_loop, run_parse_repair_loop

logger = logging.getLogger(__name__)


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
        nesy_nli_mock: bool = True,
        nli_verifier: NLIVerifier | None = None,
        entailment_threshold: float = 0.70,
        contradiction_threshold: float = 0.70,
        max_repair_attempts_parse: int = 2,
        max_repair_attempts_answer: int = 2,
        session_svc: SessionService | None = None,
    ) -> None:
        self._rulebase_core_path = rulebase_core_path
        self._evidence_chunks_path = evidence_chunks_path
        self._top_k = rule_retrieval_top_k
        self._nesy_nli_mock = nesy_nli_mock
        self._nli_verifier = nli_verifier
        self._entailment_threshold = entailment_threshold
        self._contradiction_threshold = contradiction_threshold
        self._max_repair_attempts_parse = max_repair_attempts_parse
        self._max_repair_attempts_answer = max_repair_attempts_answer
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
            entailment_threshold=self._entailment_threshold,
            contradiction_threshold=self._contradiction_threshold,
        )
        if self._nli_verifier is not None:
            return NeSyEngine(nli=self._nli_verifier, **kw)
        return NeSyEngine(**kw)

    def ask(
        self,
        question: str,
        session_id: str | None,
        user_facts: list[str] | None,
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
        )

    def clarify(self, session_id: str, answers: list[dict[str, Any]]) -> ClarifyResponse:
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
) -> AskResponse:
    svc = session_svc or get_session_service()
    engine = nesy or NeSyEngine()

    if session_id and (st := svc.get(session_id)):
        session = st
        session.original_question = question or session.original_question
        for f in user_facts:
            session.known_facts[f] = True
    else:
        session = svc.create_session(question, user_facts)

    trace: dict[str, Any] = {"stage": []}

    layer1: Layer1Parse = parse_question_layer1(question)
    layer2: Layer2Parse = build_layer2(layer1, user_facts=_user_fact_keys(session))
    session.layer1 = layer1
    session.layer2 = layer2
    trace["stage"].append("parse_done")

    layer1, layer2, v_parse, parse_repair_trace = run_parse_repair_loop(
        engine,
        layer1=layer1,
        layer2=layer2,
        question_text=question,
        user_facts=_user_fact_keys(session),
        max_repair_attempts_parse=max_repair_attempts_parse,
    )
    session.layer1 = layer1
    session.layer2 = layer2
    trace["parse_repair"] = parse_repair_trace
    _merge_verification(session, v_parse)
    ambs = (layer2.diagnostics or {}).get("ambiguities") or []
    if any(a.get("blocking") for a in ambs):
        prompts = merge_clarification_prompts_unified(build_parse_ambiguity_prompts(ambs), [])
        session.clarification_questions = prompts
        svc.save(session)
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
        svc.save(session)
        return AskResponse(
            session_id=session.session_id,
            needs_clarification=False,
            verification_trace=session.verification_logs,
            layer1=layer1,
            layer2=layer2,
            debug_trace=trace | {"error": "parse_rejected"},
        )

    ranked = retrieve_rules(layer1=layer1, layer2=layer2, top_k=top_k, index=rule_index)
    session.retrieved_rules = [r for r, _, _ in ranked]
    trace["stage"].append("retrieve_done")
    trace["rule_retrieval"] = {
        "backend": "hybrid_bm25_structured",
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

    goal = layer2.goal
    selected, bstate = run_backward(goal=goal, candidates=ranked, known_facts=known_facts_for_reasoning(session))
    session.reasoning = bstate
    session.selected_rule = selected

    v_rule = engine.verify_rule(
        layer2_goal=goal,
        rule_candidate=selected,
        law_span=(selected.source_ref_full or selected.source_ref) if selected else None,
        legal_frame=layer2.query_rule_candidate or "",
    )
    _merge_verification(session, v_rule)

    v_back = engine.verify_backward(
        goal=goal,
        selected_rule_id=selected.rule_id if selected else None,
        requirements_ok=bstate.can_continue_forward,
        backward_plan=bstate.backward_plan,
        missing_facts=bstate.missing_facts,
        requirement_keys=[r.key for r in bstate.requirement_set],
    )
    _merge_verification(session, v_back)

    if not selected:
        svc.save(session)
        return AskResponse(
            session_id=session.session_id,
            needs_clarification=False,
            verification_trace=session.verification_logs,
            layer1=layer1,
            layer2=layer2,
            retrieved_rules=[_rule_dump(r) for r, s, d in ranked[:5]],
            reasoning=bstate,
            debug_trace=trace | {"note": "no_unifying_rule"},
        )

    if bstate.missing_facts:
        parse_ambs = (layer2.diagnostics or {}).get("ambiguities") or []
        parse_prompts = build_parse_ambiguity_prompts([a for a in parse_ambs if not a.get("blocking")])
        backward_prompts = build_clarification_prompts_from_requirements(
            bstate.missing_facts,
            bstate.requirement_set,
            backward_plan=bstate.backward_plan,
            related_rule_id=selected.rule_id if selected else None,
        )
        prompts = merge_clarification_prompts_unified(parse_prompts, backward_prompts)
        session.missing_facts = bstate.missing_facts
        session.clarification_questions = prompts
        svc.save(session)
        return AskResponse(
            session_id=session.session_id,
            needs_clarification=True,
            clarification_questions=[ClarificationPrompt.model_validate(p) for p in prompts],
            layer1=layer1,
            layer2=layer2,
            verification_trace=session.verification_logs,
            retrieved_rules=[_rule_dump(r) for r, s, d in ranked[:8]],
            selected_rule=_rule_dump(selected),
            reasoning=bstate,
            debug_trace=trace | {"stage": "needs_clarification"},
        )

    conclusion, goal_ok, fstate, _ = run_forward(
        rule=selected,
        known_facts=known_facts_for_reasoning(session),
        goal=goal,
        backward_plan=bstate.backward_plan,
        candidates=ranked,
    )
    session.reasoning = fstate
    win_rule = selected
    if fstate.forward_result and fstate.forward_result.get("rule_id"):
        _by_id = {r.rule_id: r for r, _, _ in ranked}
        win_rule = _by_id.get(fstate.forward_result["rule_id"], selected)
    session.selected_rule = win_rule
    selected = win_rule

    proof = build_proof(
        rule=selected,
        used_facts=list(known_facts_for_reasoning(session).keys()),
        conclusion=conclusion,
        forward_result=fstate.forward_result,
    )
    session.proof = proof

    v_fwd = engine.verify_forward(
        goal=goal,
        conclusion=conclusion,
        goal_achieved=goal_ok,
        known_facts=known_facts_for_reasoning(session),
        forward_result=fstate.forward_result,
        proof=proof.model_dump(mode="json"),
    )
    _merge_verification(session, v_fwd)

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

    ans = generate_answer(
        question=question,
        conclusion=conclusion,
        proof=proof,
        evidence=ev,
        goal_achieved=goal_ok,
    )

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
    ans.answer_text = ans_text
    ans.verification_summary += f";answer_repair_attempts={answer_repair_trace[-1].get('attempts_used', 0)}"
    trace["answer_repair"] = answer_repair_trace
    _merge_verification(session, v_ans)
    if v_ans.final_decision == "REJECT":
        ans.answer_text = safe_regenerate_answer(conclusion, proof=proof, evidence=ev)
        ans.verification_summary += ";answer_fallback_regenerate_on_reject"

    session.answer = ans
    trace["stage"].append("complete")
    session.pipeline_trace = trace
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
) -> ClarifyResponse:
    svc = session_svc or get_session_service()
    engine = nesy or NeSyEngine()
    session = svc.get(session_id)
    if not session:
        raise KeyError("session_not_found")

    svc.merge_fact_answers(session, answers)
    question = session.original_question
    forced = extract_resolved_condition_atoms_from_known_facts(session.known_facts)
    layer1 = session.layer1 or parse_question_layer1(question)
    layer2 = build_layer2(
        layer1,
        user_facts=_user_fact_keys(session),
        forced_condition_atoms=forced if forced else None,
    )
    session.layer1 = layer1
    session.layer2 = layer2

    trace: dict[str, Any] = {"stage": ["clarify_resume"]}

    layer1, layer2, _v_parse_cl, parse_repair_trace = run_parse_repair_loop(
        engine,
        layer1=layer1,
        layer2=layer2,
        question_text=question,
        user_facts=_user_fact_keys(session),
        max_repair_attempts_parse=max_repair_attempts_parse,
    )
    session.layer1 = layer1
    session.layer2 = layer2
    trace["parse_repair"] = parse_repair_trace
    _merge_verification(session, _v_parse_cl)
    if _v_parse_cl.final_decision == "REJECT":
        svc.save(session)
        return ClarifyResponse(
            session_id=session.session_id,
            verification_trace=session.verification_logs,
            layer1=layer1,
            layer2=layer2,
            debug_trace=trace | {"error": "parse_rejected"},
        )

    ranked = retrieve_rules(layer1=layer1, layer2=layer2, top_k=top_k, index=rule_index)
    session.retrieved_rules = [r for r, _, _ in ranked]
    trace["rule_retrieval"] = {
        "backend": "hybrid_bm25_structured",
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

    goal = layer2.goal
    selected, bstate = run_backward(goal=goal, candidates=ranked, known_facts=known_facts_for_reasoning(session))
    session.reasoning = bstate
    session.selected_rule = selected

    v_rule = engine.verify_rule(
        layer2_goal=goal,
        rule_candidate=selected,
        law_span=(selected.source_ref_full or selected.source_ref) if selected else None,
        legal_frame=layer2.query_rule_candidate or "",
    )
    _merge_verification(session, v_rule)

    v_back = engine.verify_backward(
        goal=goal,
        selected_rule_id=selected.rule_id if selected else None,
        requirements_ok=bstate.can_continue_forward,
        backward_plan=bstate.backward_plan,
        missing_facts=bstate.missing_facts,
        requirement_keys=[r.key for r in bstate.requirement_set],
    )
    _merge_verification(session, v_back)

    if not selected:
        svc.save(session)
        return ClarifyResponse(
            session_id=session.session_id,
            verification_trace=session.verification_logs,
            reasoning=bstate,
            debug_trace=trace,
        )

    if bstate.missing_facts:
        parse_ambs = (layer2.diagnostics or {}).get("ambiguities") or []
        parse_prompts = build_parse_ambiguity_prompts([a for a in parse_ambs if not a.get("blocking")])
        backward_prompts = build_clarification_prompts_from_requirements(
            bstate.missing_facts,
            bstate.requirement_set,
            backward_plan=bstate.backward_plan,
            related_rule_id=selected.rule_id if selected else None,
        )
        prompts = merge_clarification_prompts_unified(parse_prompts, backward_prompts)
        session.missing_facts = bstate.missing_facts
        session.clarification_questions = prompts
        svc.save(session)
        return ClarifyResponse(
            session_id=session.session_id,
            needs_clarification=True,
            clarification_questions=[ClarificationPrompt.model_validate(p) for p in prompts],
            verification_trace=session.verification_logs,
            selected_rule=_rule_dump(selected),
            reasoning=bstate,
            debug_trace=trace,
        )

    conclusion, goal_ok, fstate, _ = run_forward(
        rule=selected,
        known_facts=known_facts_for_reasoning(session),
        goal=goal,
        backward_plan=bstate.backward_plan,
        candidates=ranked,
    )
    session.reasoning = fstate
    if fstate.forward_result and fstate.forward_result.get("rule_id"):
        _by_id = {r.rule_id: r for r, _, _ in ranked}
        selected = _by_id.get(fstate.forward_result["rule_id"], selected)
    session.selected_rule = selected

    proof = build_proof(
        rule=selected,
        used_facts=list(known_facts_for_reasoning(session).keys()),
        conclusion=conclusion,
        forward_result=fstate.forward_result,
    )
    session.proof = proof

    v_fwd = engine.verify_forward(
        goal=goal,
        conclusion=conclusion,
        goal_achieved=goal_ok,
        known_facts=known_facts_for_reasoning(session),
        forward_result=fstate.forward_result,
        proof=proof.model_dump(mode="json"),
    )
    _merge_verification(session, v_fwd)

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
    ans = generate_answer(
        question=question,
        conclusion=conclusion,
        proof=proof,
        evidence=ev,
        goal_achieved=goal_ok,
    )
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
    ans.answer_text = ans_text
    ans.verification_summary += f";answer_repair_attempts={answer_repair_trace[-1].get('attempts_used', 0)}"
    trace["answer_repair"] = answer_repair_trace
    _merge_verification(session, v_ans)
    if v_ans.final_decision == "REJECT":
        ans.answer_text = safe_regenerate_answer(conclusion, proof=proof, evidence=ev)
        ans.verification_summary += ";answer_fallback_regenerate_on_reject"

    session.answer = ans
    session.pipeline_trace = trace
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
