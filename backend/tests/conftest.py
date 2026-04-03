"""Pytest fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# backend/ is the test cwd; repo root + src/ for `src.*` and `schemas.*`
_ROOT = Path(__file__).resolve().parents[1]
_REPO = _ROOT.parent
_SRC = _REPO / "src"
for p in (_ROOT, _REPO, _SRC):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)


@pytest.fixture(autouse=True)
def _configure_qa_runtime() -> None:
    """TestClient may not run FastAPI startup hooks the same as uvicorn; mirror main.py."""
    from app.config import settings
    from pipeline.qa_runtime import configure_qa_orchestrator

    configure_qa_orchestrator(
        rulebase_core_path=settings.resolved_rulebase_core(),
        evidence_chunks_path=settings.resolved_evidence_chunks(),
        rule_retrieval_top_k=settings.rule_retrieval_top_k,
        nesy_nli_mock=settings.nesy_nli_mock,
    )
