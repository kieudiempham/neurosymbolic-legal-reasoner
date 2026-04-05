"""Resolve NLI backend + metadata for NeSy (strict vs degraded symbolic-only)."""

from __future__ import annotations

import logging
from typing import Any

from app.config import Settings
from app.llm import build_nli_verifier
from verification.nli_verifier import MockNLIVerifier, NLIVerifier

logger = logging.getLogger(__name__)


def resolve_nli_stack_for_nesy(settings: Settings) -> tuple[NLIVerifier | None, dict[str, Any], bool]:
    """
    Returns ``(verifier, meta, nli_degraded_symbolic_only)``.

    - When ``nesy_nli_mock`` is True: lightweight mock; meta documents answer-only NLI.
    - When mock is False: prefer a real verifier (HF / OpenAI-compatible). If missing and
      ``nli_policy == 'strict'``, raise. If ``degraded``, return (None, meta, True) so the engine
      skips NLI calls with explicit trace.
    """
    meta: dict[str, Any] = {
        "nli_provider": "none",
        "nli_model_name": None,
        "nli_status": "skipped",
        "nli_enabled": False,
    }
    if settings.nesy_nli_mock:
        meta["nli_status"] = "mock_answer_only"
        meta["nli_provider"] = "mock_heuristic"
        meta["nli_enabled"] = True
        v = build_nli_verifier(settings)
        return (v or MockNLIVerifier()), meta, False

    v = build_nli_verifier(settings)
    if v is not None:
        tn = type(v).__name__
        meta["nli_provider"] = tn
        meta["nli_status"] = "ok"
        meta["nli_enabled"] = True
        if "HuggingFace" in tn:
            meta["nli_model_name"] = settings.nli_model_name
        elif "OpenAICompatible" in tn:
            meta["nli_model_name"] = settings.llm_model
        return v, meta, False

    if settings.nli_policy == "strict":
        raise RuntimeError(
            "LEGAL_QA_NLI_POLICY=strict requires a working NLI backend (set LEGAL_QA_NLI_ENABLED=1 "
            "or provide LEGAL_QA_LLM_API_KEY for OpenAI-compatible NLI)."
        )
    meta["nli_status"] = "degraded_symbolic_only"
    meta["nli_provider"] = "none"
    meta["nli_enabled"] = False
    logger.warning(
        "NLI unavailable: running NeSy in degraded symbolic-only mode (no semantic NLI). "
        "Set LEGAL_QA_NLI_ENABLED or provide an API key for full verification."
    )
    return None, meta, True
