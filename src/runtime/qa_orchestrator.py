"""End-to-end QA orchestration: parse → verify → retrieve → backward → clarify → forward → proof → evidence → answer."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from generation.answer_generator import generate_answer, safe_regenerate_answer
from reasoning.backward_reasoner import run_backward
from reasoning.clarification_manager import build_clarification_prompts
from reasoning.forward_reasoner import run_forward
from reasoning.proof_builder import build_proof
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
from verification.symbolic_validator import check_answer_vs_goal

logger = logging.getLogger(__name__)


def _rule_dump(r: RuleRecord) -> dict[str, Any]:
    return r.model_dump(mode="json")


def _merge_verification(sess: SessionState, rec: VerificationRecord) -> None:
    sess.verification_logs.append(rec)


class QAOrchestrator:
    """Central business orchestrator for ask / clarify flows."""

    def __init__(
        self,
        *,
        rulebase_core_path: Path,
        evidence_chunks_path: Path,
        rule_retrieval_top_k: int = 8,
        nesy_nli_mock: bool = True,
        session_svc: SessionService | None = None,
    ) -> None:
        self._rulebase_core_path = rulebase_core_path
        self._evidence_chunks_path = evidence_chunks_path
        self._top_k = rule_retrieval_top_k
        self._nesy_nli_mock = nesy_nli_mock
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
        return NeSyEngine(nesy_nli_mock=self._nesy_nli_mock)

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
    layer2: Layer2Parse = build_layer2(layer1, user_facts=list(session.known_facts.keys()))
    session.layer1 = layer1
    session.layer2 = layer2
    trace["stage"].append("parse_done")

    v_parse = engine.verify_parse(layer1, layer2)
    _merge_verification(session, v_parse)
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

    goal = layer2.goal
    selected, bstate = run_backward(goal=goal, candidates=ranked, known_facts=session.known_facts)
    session.reasoning = bstate
    session.selected_rule = selected

    v_back = engine.verify_backward(
        goal=goal,
        selected_rule_id=selected.rule_id if selected else None,
        requirements_ok=bstate.can_continue_forward,
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
        prompts = build_clarification_prompts(bstate.missing_facts)
        session.missing_facts = bstate.missing_facts
        session.clarification_questions = prompts
        svc.save(session)
        return AskResponse(
            session_id=session.session_id,
            needs_clarification=True,
            clarification_questions=[ClarificationPrompt(**p) for p in prompts],
            layer1=layer1,
            layer2=layer2,
            verification_trace=session.verification_logs,
            retrieved_rules=[_rule_dump(r) for r, s, d in ranked[:8]],
            selected_rule=_rule_dump(selected),
            reasoning=bstate,
            debug_trace=trace | {"stage": "needs_clarification"},
        )

    conclusion, goal_ok, fstate, _ = run_forward(
        rule=selected, known_facts=session.known_facts, goal=goal
    )
    session.reasoning = fstate

    v_fwd = engine.verify_forward(goal=goal, conclusion=conclusion, goal_achieved=goal_ok)
    _merge_verification(session, v_fwd)

    proof = build_proof(rule=selected, used_facts=list(session.known_facts.keys()), conclusion=conclusion)
    session.proof = proof

    ev = (evidence_retriever or get_evidence_retriever()).retrieve(
        question=question, rule=selected, conclusion=conclusion, top_k=5
    )

    ans = generate_answer(
        question=question,
        conclusion=conclusion,
        proof=proof,
        evidence=ev,
        goal_achieved=goal_ok,
    )

    sym_ok, _diag = check_answer_vs_goal(
        modality_expected=layer1.modality_text or "",
        action_token_in_answer=ans.answer_text,
        goal_action=str(goal.get("args", ["", "", ""])[1] if len(goal.get("args", [])) > 1 else ""),
    )
    v_ans = engine.verify_answer(answer_text=ans.answer_text, conclusion=conclusion, symbolic_ok=sym_ok)
    _merge_verification(session, v_ans)
    if v_ans.final_decision in ("REJECT", "REPAIR"):
        ans.answer_text = safe_regenerate_answer(conclusion)
        ans.verification_summary += ";answer_regenerated_once"

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
) -> ClarifyResponse:
    svc = session_svc or get_session_service()
    engine = nesy or NeSyEngine()
    session = svc.get(session_id)
    if not session:
        raise KeyError("session_not_found")

    svc.merge_fact_answers(session, answers)
    question = session.original_question
    layer1 = session.layer1 or parse_question_layer1(question)
    layer2 = session.layer2 or build_layer2(layer1, user_facts=list(session.known_facts.keys()))
    session.layer1 = layer1
    session.layer2 = layer2

    trace: dict[str, Any] = {"stage": ["clarify_resume"]}

    ranked = retrieve_rules(layer1=layer1, layer2=layer2, top_k=top_k, index=rule_index)
    session.retrieved_rules = [r for r, _, _ in ranked]

    goal = layer2.goal
    selected, bstate = run_backward(goal=goal, candidates=ranked, known_facts=session.known_facts)
    session.reasoning = bstate
    session.selected_rule = selected

    v_back = engine.verify_backward(
        goal=goal,
        selected_rule_id=selected.rule_id if selected else None,
        requirements_ok=bstate.can_continue_forward,
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
        prompts = build_clarification_prompts(bstate.missing_facts)
        session.missing_facts = bstate.missing_facts
        session.clarification_questions = prompts
        svc.save(session)
        return ClarifyResponse(
            session_id=session.session_id,
            needs_clarification=True,
            clarification_questions=[ClarificationPrompt(**p) for p in prompts],
            verification_trace=session.verification_logs,
            selected_rule=_rule_dump(selected),
            reasoning=bstate,
            debug_trace=trace,
        )

    conclusion, goal_ok, fstate, _ = run_forward(
        rule=selected, known_facts=session.known_facts, goal=goal
    )
    session.reasoning = fstate
    v_fwd = engine.verify_forward(goal=goal, conclusion=conclusion, goal_achieved=goal_ok)
    _merge_verification(session, v_fwd)

    proof = build_proof(rule=selected, used_facts=list(session.known_facts.keys()), conclusion=conclusion)
    session.proof = proof

    ev = (evidence_retriever or get_evidence_retriever()).retrieve(
        question=question, rule=selected, conclusion=conclusion, top_k=5
    )
    ans = generate_answer(
        question=question,
        conclusion=conclusion,
        proof=proof,
        evidence=ev,
        goal_achieved=goal_ok,
    )
    sym_ok, _ = check_answer_vs_goal(
        modality_expected=layer1.modality_text or "",
        action_token_in_answer=ans.answer_text,
        goal_action=str(goal.get("args", ["", "", ""])[1] if len(goal.get("args", [])) > 1 else ""),
    )
    v_ans = engine.verify_answer(answer_text=ans.answer_text, conclusion=conclusion, symbolic_ok=sym_ok)
    _merge_verification(session, v_ans)
    if v_ans.final_decision in ("REJECT", "REPAIR"):
        ans.answer_text = safe_regenerate_answer(conclusion)

    session.answer = ans
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
