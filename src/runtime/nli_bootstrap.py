"""
NLI + NeSy bootstrap for Python runners (``run_qa_pipeline``, batch jobs).

Uses the same source of truth as FastAPI startup:

* ``app.llm.build_nli_verifier`` (HF → API → None) via ``app.nli_stack.resolve_nli_stack_for_nesy``
* ``app.config.Settings`` (``.env`` / ``LEGAL_QA_*``)

Backend directory is added to ``sys.path`` when needed so ``import app.*`` works from repo-root scripts.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from verification.engine import NeSyEngine
from verification.nli_verifier import NLIVerifier


def ensure_backend_importable() -> Path:
    """Insert ``<repo>/backend`` on ``sys.path`` so ``app.config`` / ``app.llm`` resolve."""
    repo = Path(__file__).resolve().parents[2]
    backend = repo / "backend"
    s = str(backend)
    if s not in sys.path:
        sys.path.insert(0, s)
    return repo


def load_app_settings() -> Any:
    ensure_backend_importable()
    from app.config import settings

    return settings


def resolve_nli_stack_bundle(
    settings: Any | None = None,
) -> tuple[NLIVerifier | None, dict[str, Any], bool]:
    """
    Same tuple as ``app.nli_stack.resolve_nli_stack_for_nesy`` — single source of truth.

    Intended for ``configure_qa_orchestrator`` (backend startup and tests).
    """
    ensure_backend_importable()
    from app.nli_stack import resolve_nli_stack_for_nesy

    s = settings or load_app_settings()
    return resolve_nli_stack_for_nesy(s)


def nli_runtime_descriptor(
    engine: NeSyEngine,
    settings: Any,
    *,
    stack_meta: dict[str, Any] | None = None,
    nli_degraded: bool | None = None,
) -> dict[str, Any]:
    """Structured meta for ``QAResponse.meta[\"nli_runtime\"]`` and debugging."""
    v = getattr(engine, "_nli", None)
    vn = type(v).__name__ if v is not None else "None"
    degraded = nli_degraded if nli_degraded is not None else bool(getattr(engine, "_nli_degraded", False))
    mock_flag = bool(getattr(engine, "_nesy_nli_mock", False))
    meta = dict(stack_meta or getattr(engine, "_nli_meta", {}) or {})

    source = "mock"
    device: str | None = None
    model_name: str | None = meta.get("nli_model_name")

    if degraded:
        source = "degraded_symbolic_only"
    elif "HuggingFace" in vn:
        source = "hf"
        model_name = model_name or settings.nli_model_name
        try:
            if v is not None:
                svc = getattr(v, "_service", None)
                cfg = getattr(svc, "config", None) if svc is not None else None
                if cfg is not None:
                    device = str(getattr(cfg, "device", "") or "") or None
        except Exception:
            device = None
    elif "OpenAICompatible" in vn:
        source = "api"
        model_name = model_name or settings.llm_model
    elif "Mock" in vn or "Heuristic" in vn:
        source = "mock"
    else:
        source = "unknown"

    return {
        "verifier_class": vn,
        "source": source,
        "model_name": model_name,
        "device": device,
        "nesy_nli_mock": mock_flag,
        "nli_degraded": degraded,
        "nli_policy": settings.nli_policy,
        "stack_meta": meta,
    }


def build_nesy_engine_for_pipeline(settings: Any | None = None) -> tuple[NeSyEngine, dict[str, Any]]:
    """Build ``NeSyEngine`` exactly like the configured orchestrator (HF / API / mock / degraded)."""
    s = settings or load_app_settings()
    v, meta, degraded = resolve_nli_stack_bundle(s)
    eng = NeSyEngine(
        nli=v,
        nesy_nli_mock=s.nesy_nli_mock,
        nli_degraded=degraded,
        nli_meta=meta,
        entailment_threshold=s.nli_entailment_threshold,
        contradiction_threshold=s.nli_contradiction_threshold,
    )
    return eng, nli_runtime_descriptor(eng, s, stack_meta=meta, nli_degraded=degraded)


def resolve_pipeline_nesy_engine(
    *,
    nesy: NeSyEngine | None = None,
    nli_verifier: NLIVerifier | None = None,
    settings: Any | None = None,
) -> tuple[NeSyEngine, dict[str, Any]]:
    """
    Resolve engine for ``run_qa_pipeline`` / batch:

    1. If ``nesy`` is set → use as-is (no override).
    2. Elif ``nli_verifier`` is set → wrap in ``NeSyEngine`` with thresholds from settings.
    3. Else → ``build_nesy_engine_for_pipeline`` (same as backend).
    """
    s = settings or load_app_settings()

    if nesy is not None:
        return nesy, nli_runtime_descriptor(
            nesy,
            s,
            stack_meta=getattr(nesy, "_nli_meta", None),
            nli_degraded=bool(getattr(nesy, "_nli_degraded", False)),
        )

    if nli_verifier is not None:
        eng = NeSyEngine(
            nli=nli_verifier,
            nesy_nli_mock=s.nesy_nli_mock,
            nli_degraded=False,
            nli_meta={"nli_provider": "caller_injected", "nli_status": "ok", "nli_enabled": True},
            entailment_threshold=s.nli_entailment_threshold,
            contradiction_threshold=s.nli_contradiction_threshold,
        )
        rt = nli_runtime_descriptor(eng, s, stack_meta=eng._nli_meta, nli_degraded=False)
        rt["injected_verifier"] = True
        return eng, rt

    return build_nesy_engine_for_pipeline(s)
