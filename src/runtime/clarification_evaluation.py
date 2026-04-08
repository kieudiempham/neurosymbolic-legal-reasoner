"""Clarification two-phase evaluation: detect → inject gold answer → rerun → measure gain."""

from __future__ import annotations

import logging
from typing import Any

from runtime.qa_orchestrator import run_ask, run_clarify
from schemas.answer import FinalAnswer
from schemas.pipeline_trace import PipelineTrace
from schemas.question_parse import Layer2Parse
from session.session_service import SessionService
from verification.engine import NeSyEngine
from verification.nli_verifier import NLIVerifier

logger = logging.getLogger(__name__)


class ClarificationEvaluationRequest:
    """Evaluation input: original query + gold clarification answer."""

    def __init__(
        self,
        original_query: str,
        gold_clarification_answer: str,
        session_id: str | None = None,
    ) -> None:
        self.original_query = original_query
        self.gold_clarification_answer = gold_clarification_answer
        self.session_id = session_id


class ClarificationPhase1Result:
    """Phase 1 outcome: ask and detect clarification need."""

    def __init__(
        self,
        session_id: str,
        layer2: Layer2Parse | None,
        asked_clarification: bool,
        clarification_targets: list[str],
        proof_phase1: dict[str, Any] | None,
        answer_phase1: FinalAnswer | None,
        answer_text_phase1: str | None,
    ) -> None:
        self.session_id = session_id
        self.layer2 = layer2
        self.asked_clarification = asked_clarification
        self.clarification_targets = clarification_targets
        self.proof_phase1 = proof_phase1
        self.answer_phase1 = answer_phase1
        self.answer_text_phase1 = answer_text_phase1


class ClarificationEvaluationResult:
    """Complete evaluation result with before/after metrics and gain."""

    def __init__(
        self,
        session_id: str,
        original_query: str,
        gold_clarification_answer: str,
        asked_clarification: bool,
        clarification_targets: list[str],
        # Phase 1 (before clarification)
        answer_before: str | None,
        proof_before: dict[str, Any] | None,
        final_status_before: str,
        # Phase 3 (after clarification with gold answer)
        answer_after: str | None,
        proof_after: dict[str, Any] | None,
        final_status_after: str,
        # Gain metrics
        gained_answer: bool,  # changed from None/empty to non-empty
        gained_proof: bool,  # changed from None/partial to complete
        resolved_after_clarification: bool,  # status changed to "answered"
        # Raw artifacts
        phase1_trace: PipelineTrace | None = None,
        phase3_trace: PipelineTrace | None = None,
    ) -> None:
        self.session_id = session_id
        self.original_query = original_query
        self.gold_clarification_answer = gold_clarification_answer
        self.asked_clarification = asked_clarification
        self.clarification_targets = clarification_targets
        # Before
        self.answer_before = answer_before
        self.proof_before = proof_before
        self.final_status_before = final_status_before
        # After
        self.answer_after = answer_after
        self.proof_after = proof_after
        self.final_status_after = final_status_after
        # Gain
        self.gained_answer = gained_answer
        self.gained_proof = gained_proof
        self.resolved_after_clarification = resolved_after_clarification
        # Traces
        self.phase1_trace = phase1_trace
        self.phase3_trace = phase3_trace

    def to_dict(self) -> dict[str, Any]:
        """Serialize evaluation result for logging/export."""
        return {
            "session_id": self.session_id,
            "original_query": self.original_query,
            "gold_clarification_answer": self.gold_clarification_answer,
            "asked_clarification": self.asked_clarification,
            "clarification_targets": self.clarification_targets,
            "before": {
                "answer": self.answer_before,
                "proof": self.proof_before,
                "final_status": self.final_status_before,
            },
            "after": {
                "answer": self.answer_after,
                "proof": self.proof_after,
                "final_status": self.final_status_after,
            },
            "gain": {
                "gained_answer": self.gained_answer,
                "gained_proof": self.gained_proof,
                "resolved_after_clarification": self.resolved_after_clarification,
            },
        }


def run_clarification_evaluation(
    req: ClarificationEvaluationRequest,
    *,
    session_svc: SessionService | None = None,
    nesy: NeSyEngine | None = None,
    nli_verifier: NLIVerifier | None = None,
    settings: Any | None = None,
    rule_index: Any | None = None,
    evidence_retriever: Any | None = None,
    top_k: int | None = None,
    max_repair_attempts_parse: int | None = None,
    max_repair_attempts_answer: int | None = None,
    max_repair_attempts_rule: int | None = None,
    max_repair_attempts_backward: int | None = None,
    max_repair_attempts_forward: int | None = None,
) -> ClarificationEvaluationResult:
    """
    Four-phase clarification evaluation:

    **Phase 1**: Run initial QA (ask) to detect if clarification is needed.
    - Input: original query
    - Output: needs clarification? which facts are missing?

    **Phase 2**: Inject gold clarification answer into session state (known_facts).

    **Phase 3**: Rerun reasoning (clarify) with injected fact.
    - Input: session with merged facts from gold answer
    - Output: new answer/proof

    **Phase 4**: Measure gain.
    - Compare answer_before vs answer_after
    - Compare proof_before vs proof_after
    - Check if final_status improved to "answered"

    Returns `ClarificationEvaluationResult` with full before/after metrics and gain flags.
    """
    from runtime.qa_pipeline import run_qa_pipeline, run_clarification_pipeline
    from reasoning.clarification_manager import normalize_clarification_answers

    # Phase 1: Initial ask
    logger.info(f"[ClarEval] Phase 1: Ask with original query: {req.original_query[:80]}")
    phase1_qa = run_qa_pipeline(
        req.original_query,
        session_id=req.session_id,
        session_svc=session_svc,
        nesy=nesy,
        nli_verifier=nli_verifier,
        settings=settings,
        rule_index=rule_index,
        evidence_retriever=evidence_retriever,
        top_k=top_k,
        max_repair_attempts_parse=max_repair_attempts_parse,
        max_repair_attempts_answer=max_repair_attempts_answer,
        max_repair_attempts_rule=max_repair_attempts_rule,
        max_repair_attempts_backward=max_repair_attempts_backward,
        max_repair_attempts_forward=max_repair_attempts_forward,
        debug=True,
        save_trace=False,
    )

    # Extract phase 1 results
    session_id = phase1_qa.session_id or req.session_id or "eval_session"
    asked_clarification = phase1_qa.status == "needs_clarification"
    clarification_targets = [p.get("fact_key", "") for p in (phase1_qa.clarification_prompts or [])]
    answer_before = phase1_qa.final_answer.answer_text if phase1_qa.final_answer else None
    proof_before = None  # Extract from phase1_qa if available
    final_status_before = phase1_qa.status

    logger.info(
        f"[ClarEval] Phase 1 complete: asked_clarification={asked_clarification}, "
        f"clarification_targets={clarification_targets}, status={final_status_before}"
    )

    # If no clarification was asked, phases 2-3 are skipped
    if not asked_clarification:
        logger.info("[ClarEval] No clarification asked in phase 1; evaluation ends")
        return ClarificationEvaluationResult(
            session_id=session_id,
            original_query=req.original_query,
            gold_clarification_answer=req.gold_clarification_answer,
            asked_clarification=False,
            clarification_targets=[],
            answer_before=answer_before,
            proof_before=proof_before,
            final_status_before=final_status_before,
            answer_after=answer_before,
            proof_after=proof_before,
            final_status_after=final_status_before,
            gained_answer=False,
            gained_proof=False,
            resolved_after_clarification=False,
            phase1_trace=phase1_qa.pipeline_trace,
        )

    # Phase 2 & 3: Inject gold answer and rerun
    logger.info(
        f"[ClarEval] Phase 2-3: Injecting gold clarification answer and rerunning: "
        f"{req.gold_clarification_answer[:80]}"
    )

    # Prepare gold clarification as answer dict
    gold_answer_dict = {
        "fact_value": req.gold_clarification_answer,
        "confidence": 1.0,
        "source": "gold_evaluation",
    }

    # Run clarification pipeline with gold answer injected
    phase3_qa = run_clarification_pipeline(
        session_id=session_id,
        answers=[gold_answer_dict],
        session_svc=session_svc,
        nesy=nesy,
        nli_verifier=nli_verifier,
        settings=settings,
        rule_index=rule_index,
        evidence_retriever=evidence_retriever,
        top_k=top_k,
        max_repair_attempts_parse=max_repair_attempts_parse,
        max_repair_attempts_answer=max_repair_attempts_answer,
        max_repair_attempts_rule=max_repair_attempts_rule,
        max_repair_attempts_backward=max_repair_attempts_backward,
        max_repair_attempts_forward=max_repair_attempts_forward,
        debug=True,
        save_trace=False,
    )

    # Extract phase 3 results
    answer_after = phase3_qa.final_answer.answer_text if phase3_qa.final_answer else None
    proof_after = None  # Extract from phase3_qa if available
    final_status_after = phase3_qa.status

    logger.info(
        f"[ClarEval] Phase 3 complete: status={final_status_after}, "
        f"answer_before={bool(answer_before and answer_before.strip())}, "
        f"answer_after={bool(answer_after and answer_after.strip())}"
    )

    # Phase 4: Measure gain
    gained_answer = (
        (not answer_before or not answer_before.strip())
        and (answer_after and answer_after.strip())
    )
    gained_proof = False  # TODO: implement proof comparison logic
    resolved_after_clarification = final_status_after == "answered" and final_status_before != "answered"

    logger.info(
        f"[ClarEval] Phase 4: Gain measured: "
        f"gained_answer={gained_answer}, gained_proof={gained_proof}, "
        f"resolved_after_clarification={resolved_after_clarification}"
    )

    return ClarificationEvaluationResult(
        session_id=session_id,
        original_query=req.original_query,
        gold_clarification_answer=req.gold_clarification_answer,
        asked_clarification=asked_clarification,
        clarification_targets=clarification_targets,
        answer_before=answer_before,
        proof_before=proof_before,
        final_status_before=final_status_before,
        answer_after=answer_after,
        proof_after=proof_after,
        final_status_after=final_status_after,
        gained_answer=gained_answer,
        gained_proof=gained_proof,
        resolved_after_clarification=resolved_after_clarification,
        phase1_trace=phase1_qa.pipeline_trace,
        phase3_trace=phase3_qa.pipeline_trace,
    )
