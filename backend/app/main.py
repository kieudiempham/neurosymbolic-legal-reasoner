"""FastAPI application entry."""

from __future__ import annotations

from app.path_setup import ensure_src_paths

ensure_src_paths()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_ask import router as ask_router
from app.api.routes_clarify import router as clarify_router
from app.api.routes_health import router as health_router
from app.api.routes_session import router as session_router
from app.config import settings
from app.llm import build_nli_verifier
from app.utils.logging_utils import setup_logging
from runtime.qa_runtime import configure_qa_orchestrator

setup_logging(settings.debug)

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.on_event("startup")
def _configure_qa() -> None:
    configure_qa_orchestrator(
        rulebase_core_path=settings.resolved_rulebase_core(),
        evidence_chunks_path=settings.resolved_evidence_chunks(),
        rule_retrieval_top_k=settings.rule_retrieval_top_k,
        nesy_nli_mock=settings.nesy_nli_mock,
        nli_verifier=build_nli_verifier(settings),
        entailment_threshold=settings.nli_entailment_threshold,
        contradiction_threshold=settings.nli_contradiction_threshold,
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(ask_router)
app.include_router(clarify_router)
app.include_router(session_router)


@app.get("/")
def root() -> dict:
    return {"service": settings.app_name, "docs": "/docs", "health": "/health"}
