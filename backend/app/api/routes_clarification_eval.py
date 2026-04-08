"""HTTP API endpoints for clarification evaluation."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.path_setup import ensure_src_paths

ensure_src_paths()

from runtime.clarification_evaluation import (
    ClarificationEvaluationRequest,
    run_clarification_evaluation,
)
from runtime.nli_bootstrap import load_app_settings, resolve_pipeline_nesy_engine
from session.session_service import SessionService
from retrieval.rulebase_loader import load_rulebase

router = APIRouter(tags=["clarification-evaluation"])
logger = logging.getLogger(__name__)


class ClarificationEvaluationRequestAPI(BaseModel):
    """API request for clarification evaluation."""

    original_query: str = Field(
        ...,
        description="Original question before clarification",
    )
    gold_clarification_answer: str = Field(
        ...,
        description="Gold clarification answer to inject in phase 2",
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session ID (generated if omitted)",
    )


class ClarificationEvaluationResponseAPI(BaseModel):
    """API response from clarification evaluation."""

    session_id: str
    original_query: str
    gold_clarification_answer: str
    asked_clarification: bool
    clarification_targets: list[str]
    phase1: dict[str, Any] = Field(
        ...,
        description="Before clarification: answer, proof, status",
    )
    phase3: dict[str, Any] = Field(
        ...,
        description="After clarification: answer, proof, status",
    )
    gain: dict[str, bool] = Field(
        ...,
        description="Metrics: gained_answer, gained_proof, resolved_after_clarification",
    )


def _get_session_service() -> SessionService:
    """Dependency: get session service instance."""
    return SessionService()


@router.post(
    "/clarification-eval/run",
    response_model=ClarificationEvaluationResponseAPI,
    summary="Run clarification evaluation (4-phase)",
    description=(
        "Evaluate clarification impact on QA pipeline:\n\n"
        "**Phase 1**: Run initial ask (detect clarification need)\n"
        "**Phase 2**: Inject gold clarification answer\n"
        "**Phase 3**: Rerun clarify with new facts\n"
        "**Phase 4**: Measure gain (before/after metrics)\n\n"
        "Returns: answer/proof/status before and after, plus gain metrics."
    ),
)
async def run_evaluation(
    req: ClarificationEvaluationRequestAPI,
    session_svc: SessionService = Depends(_get_session_service),
) -> ClarificationEvaluationResponseAPI:
    """
    Execute clarification evaluation pipeline.

    Input:
    - original_query: the question needing clarification
    - gold_clarification_answer: the "ground truth" fact to inject

    Output:
    - Phase 1 results: answer/proof/status before clarification
    - Phase 3 results: answer/proof/status after clarification
    - Gain metrics: did we gain answer? proof? resolved?
    """
    try:
        settings = load_app_settings()
        nesy, nli_runtime = resolve_pipeline_nesy_engine(settings=settings)
        
        # Load rulebase if configured
        rule_index = None
        if settings:
            core_path = settings.resolved_rulebase_core()
            if core_path.is_file():
                rule_index = load_rulebase(core_path)
        
        # Run evaluation
        eval_req = ClarificationEvaluationRequest(
            original_query=req.original_query,
            gold_clarification_answer=req.gold_clarification_answer,
            session_id=req.session_id,
        )
        
        eval_result = run_clarification_evaluation(
            eval_req,
            session_svc=session_svc,
            nesy=nesy,
            settings=settings,
            rule_index=rule_index,
        )
        
        return ClarificationEvaluationResponseAPI(
            session_id=eval_result.session_id,
            original_query=eval_result.original_query,
            gold_clarification_answer=eval_result.gold_clarification_answer,
            asked_clarification=eval_result.asked_clarification,
            clarification_targets=eval_result.clarification_targets,
            phase1={
                "answer": eval_result.answer_before,
                "proof": eval_result.proof_before,
                "final_status": eval_result.final_status_before,
            },
            phase3={
                "answer": eval_result.answer_after,
                "proof": eval_result.proof_after,
                "final_status": eval_result.final_status_after,
            },
            gain={
                "gained_answer": eval_result.gained_answer,
                "gained_proof": eval_result.gained_proof,
                "resolved_after_clarification": eval_result.resolved_after_clarification,
            },
        )
    except Exception as e:
        logger.error(f"Clarification evaluation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Clarification evaluation failed: {str(e)}",
        ) from e


@router.post(
    "/clarification-eval/batch",
    response_model=list[ClarificationEvaluationResponseAPI],
    summary="Batch clarification evaluation",
    description="Evaluate multiple question-answer pairs in one request.",
)
async def batch_evaluation(
    requests: list[ClarificationEvaluationRequestAPI],
    session_svc: SessionService = Depends(_get_session_service),
) -> list[ClarificationEvaluationResponseAPI]:
    """
    Run clarification evaluation on multiple samples.

    Processes requests sequentially.
    Each request gets its own session.

    Returns list of evaluation results, one per input request.
    """
    results: list[ClarificationEvaluationResponseAPI] = []
    
    for req in requests:
        try:
            result_single = await run_evaluation(req, session_svc)
            results.append(result_single)
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(
                f"Batch eval item failed for query '{req.original_query[:50]}': {e}"
            )
            # Return error response
            results.append(
                ClarificationEvaluationResponseAPI(
                    session_id="error",
                    original_query=req.original_query,
                    gold_clarification_answer=req.gold_clarification_answer,
                    asked_clarification=False,
                    clarification_targets=[],
                    phase1={"answer": None, "proof": None, "final_status": "error"},
                    phase3={"answer": None, "proof": None, "final_status": "error"},
                    gain={"gained_answer": False, "gained_proof": False, "resolved_after_clarification": False},
                )
            )
    
    return results


@router.get(
    "/clarification-eval/health",
    summary="Health check",
    description="Verify clarification evaluation endpoint is available.",
)
async def health_check() -> dict[str, str]:
    """Check if clarification evaluation service is ready."""
    return {"status": "ok", "service": "clarification-evaluation"}
