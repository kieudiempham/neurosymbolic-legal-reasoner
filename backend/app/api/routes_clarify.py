"""POST /clarify"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.path_setup import ensure_src_paths

ensure_src_paths()

from runtime.qa_runtime import get_qa_orchestrator
from schemas.http_response import ClarifyResponse
from schemas.request import ClarifyRequest

router = APIRouter(tags=["clarify"])
logger = logging.getLogger(__name__)


@router.post("/clarify", response_model=ClarifyResponse)
def clarify(req: ClarifyRequest) -> ClarifyResponse:
    try:
        answers = [a.model_dump() for a in req.answers]
        return get_qa_orchestrator().clarify(session_id=req.session_id, answers=answers)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="session_not_found") from e
    except Exception as e:
        logger.exception("clarify_failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
