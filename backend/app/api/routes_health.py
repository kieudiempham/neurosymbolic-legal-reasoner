"""Health check."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

from app.config import settings
from app.path_setup import ensure_src_paths

ensure_src_paths()

from retrieval.rulebase_loader import get_rulebase_index
from schemas.http_response import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    idx = get_rulebase_index()
    ev_path: Path = settings.resolved_evidence_chunks()
    n_ev = 0
    if ev_path.exists():
        data = json.loads(ev_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            n_ev = len(data)
        else:
            n_ev = len(data.get("chunks") or data.get("evidence_chunks") or [])
    return HealthResponse(status="ok", rulebase_loaded=len(idx.rules) > 0, rule_count=len(idx.rules), evidence_chunks=n_ev)
