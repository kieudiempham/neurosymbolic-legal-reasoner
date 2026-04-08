"""FastAPI application entry."""

from __future__ import annotations

import logging

from app.path_setup import ensure_src_paths

ensure_src_paths()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_ask import router as ask_router
from app.api.routes_clarify import router as clarify_router
from app.api.routes_clarification_eval import router as eval_router
from app.api.routes_health import router as health_router
from app.api.routes_session import router as session_router
from app.api.routes_domains import router as domains_router
from app.config import settings
from app.utils.logging_utils import setup_logging
from runtime.nli_bootstrap import resolve_nli_stack_bundle
from runtime.qa_runtime import configure_qa_orchestrator

setup_logging(settings.debug)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.on_event("startup")
def _configure_qa() -> None:
    # Validate artifact paths before startup
    logger.info("=== Multi-Domain Artifact Loader Validation ===")
    
    ent_path = settings.resolved_rulebase_enterprise()
    labor_path = settings.resolved_rulebase_labor()
    tax_path = settings.resolved_rulebase_tax()
    shared_path = settings.resolved_rulebase_shared()
    evidence_path = settings.resolved_evidence_chunks()
    
    logger.info(f"Enterprise: {ent_path} | exists={ent_path.exists()}")
    logger.info(f"Labor: {labor_path} | exists={labor_path.exists()}")
    logger.info(f"Tax: {tax_path} | exists={tax_path.exists()}")
    logger.info(f"Shared: {shared_path} | exists={shared_path.exists()}")
    logger.info(f"Evidence: {evidence_path} | exists={evidence_path.exists()}")
    logger.info("============================================")
    
    nli_verifier, nli_meta, nli_degraded = resolve_nli_stack_bundle(settings)
    configure_qa_orchestrator(
        rulebase_core_path=settings.resolved_rulebase_core(),
        evidence_chunks_path=evidence_path,
        rule_retrieval_top_k=settings.rule_retrieval_top_k,
        nesy_nli_mock=settings.nesy_nli_mock,
        nli_verifier=nli_verifier,
        nli_degraded=nli_degraded,
        nli_meta=nli_meta,
        entailment_threshold=settings.nli_entailment_threshold,
        contradiction_threshold=settings.nli_contradiction_threshold,
        answer_reject_allow_fallback=settings.answer_reject_allow_fallback,
        settings=settings,
    )
    logger.info("QA orchestrator configured successfully")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(domains_router)
app.include_router(ask_router)
app.include_router(clarify_router)
app.include_router(eval_router)
app.include_router(session_router)


@app.get("/")
def root() -> dict:
    return {"service": settings.app_name, "docs": "/docs", "health": "/health"}
