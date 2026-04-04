"""POST /ask"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.path_setup import ensure_src_paths

ensure_src_paths()

from runtime.qa_runtime import get_qa_orchestrator
from schemas.http_response import AskResponse
from schemas.request import AskRequest

router = APIRouter(tags=["ask"])
logger = logging.getLogger(__name__)


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    try:
        return get_qa_orchestrator().ask(
            question=req.question,
            session_id=req.session_id,
            user_facts=req.user_facts,
        )
    except Exception as e:
        logger.exception("ask_failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
