"""Layer 1 parse — LLM structured JSON with heuristic fallback (v5-oriented)."""

from __future__ import annotations

import logging
import os

from schemas.question_parse import Layer1Parse
from question_side.heuristic_layer1 import parse_question_layer1_heuristic
from question_side.llm_layer1_parser import parse_layer1_llm

logger = logging.getLogger(__name__)


def _env_flag(name: str, default: bool) -> bool:
    v = os.environ.get(name, "").strip().lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "on")


def parse_question_layer1(
    question: str,
    *,
    prefer_llm: bool | None = None,
    llm_api_key: str | None = None,
    llm_base_url: str | None = None,
    llm_model: str | None = None,
) -> Layer1Parse:
    """
    Primary entry: try LLM structured Layer-1 when API key exists and prefer_llm is True.
    Fallback: heuristic (`heuristic_layer1_v2`). Metadata in `parse_metadata`.
    Env: LEGAL_QA_LAYER1_USE_LLM (default true if key present), LEGAL_QA_LLM_* .
    """
    use_llm = _env_flag("LEGAL_QA_LAYER1_USE_LLM", True) if prefer_llm is None else prefer_llm
    has_key = bool((llm_api_key or os.environ.get("LEGAL_QA_LLM_API_KEY") or os.environ.get("LLM_API_KEY") or "").strip())

    if use_llm and has_key:
        try:
            l1, _trace = parse_layer1_llm(
                question,
                api_key=llm_api_key,
                base_url=llm_base_url,
                model=llm_model,
            )
            return l1
        except Exception as e:
            logger.warning("layer1_llm_failed_fallback_heuristic: %s", e)

    h = parse_question_layer1_heuristic(question)
    meta = dict(h.parse_metadata)
    meta["parser_backend"] = "heuristic"
    if use_llm and has_key:
        meta["fallback_used"] = True
        meta["fallback_reason"] = "llm_error"
    else:
        meta["fallback_used"] = False
        meta["fallback_reason"] = "no_llm_api_key" if use_llm and not has_key else "prefer_heuristic"
    return h.model_copy(update={"parse_metadata": meta})
