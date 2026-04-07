"""POST /ask"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.path_setup import ensure_src_paths

ensure_src_paths()

from runtime.qa_runtime import get_qa_orchestrator
from runtime.qa_orchestrator import run_ask
from schemas.http_response import AskResponse
from schemas.request import AskRequest

router = APIRouter(tags=["ask"])
logger = logging.getLogger(__name__)


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    try:
        orchestrator = get_qa_orchestrator()
        
        # Call run_ask directly to pass domain_hint for domain routing
        response = run_ask(
            question=req.question,
            session_id=req.session_id,
            user_facts=req.user_facts or [],
            session_svc=orchestrator._session(),
            nesy=orchestrator._nesy(),
            rulebase_registry=orchestrator._bundle.rulebase_registry,
            domain_retriever=orchestrator._bundle.domain_retriever,
            domain_selector=orchestrator._bundle.domain_selector,
            retriever_advanced=orchestrator._bundle.retriever_advanced,
            evidence_retriever=orchestrator._evidence_retriever(),
            top_k=orchestrator._top_k,
            max_repair_attempts_parse=orchestrator._max_repair_attempts_parse,
            max_repair_attempts_answer=orchestrator._max_repair_attempts_answer,
            max_repair_attempts_rule=orchestrator._max_repair_attempts_rule,
            max_repair_attempts_backward=orchestrator._max_repair_attempts_backward,
            max_repair_attempts_forward=orchestrator._max_repair_attempts_forward,
            answer_reject_allow_fallback=orchestrator._answer_reject_allow_fallback,
            domain_hint=req.domain if req.domain else None,
        )
        
        # Enrich response with domain routing metadata
        if hasattr(response, "meta") and response.meta:
            if "domain_routing" not in response.meta:
                response.meta["domain_routing"] = {}
            response.meta["domain_routing"].update({
                "user_domain_hint": req.domain,
                "use_router": req.use_router,
            })
        
        return response
    except Exception as e:
        logger.exception("ask_failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
