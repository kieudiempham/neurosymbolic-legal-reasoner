"""Health check."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

from app.config import settings
from app.path_setup import ensure_src_paths

ensure_src_paths()

from retrieval.rulebase_loader import get_rulebase_index
from runtime.qa_runtime import get_global_rulebase_registry
from schemas.http_response import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    idx = get_rulebase_index()
    reg = get_global_rulebase_registry()
    domains_loaded: list[str] = []
    counts: dict[str, int] = {}
    shared_ok = False
    registry_first = reg is not None
    if reg is not None:
        domains_loaded = list(reg.list_domains())
        for d in domains_loaded:
            rb = reg.get_domain_rulebase(d)
            counts[d] = len(rb.rules) if rb else 0
        sh = reg.get_shared()
        shared_ok = sh is not None and len(sh.rules) > 0
        if shared_ok and sh is not None:
            counts["shared"] = len(sh.rules)
    ev_path: Path = settings.resolved_evidence_chunks()
    n_ev = 0
    if ev_path.exists():
        data = json.loads(ev_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            n_ev = len(data)
        else:
            n_ev = len(data.get("chunks") or data.get("evidence_chunks") or [])
    return HealthResponse(
        status="ok",
        rulebase_loaded=len(idx.rules) > 0,
        rule_count=len(idx.rules),
        evidence_chunks=n_ev,
        domains_loaded=domains_loaded,
        shared_layer_loaded=shared_ok,
        rule_counts_by_domain=counts,
        registry_first=registry_first,
    )
