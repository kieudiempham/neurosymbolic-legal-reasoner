"""Layer 1 parse — LLM structured JSON with heuristic fallback (v5-oriented)."""

from __future__ import annotations

import logging
import os
from time import perf_counter
from urllib.parse import urlparse

from schemas.question_parse import Layer1Parse
from question_side.heuristic_layer1 import parse_question_layer1_heuristic
from question_side.llm_layer1_parser import parse_layer1_llm

logger = logging.getLogger(__name__)


def _env_flag(name: str, default: bool) -> bool:
    v = os.environ.get(name, "").strip().lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "on")


def _classify_llm_parse_error(exc: Exception) -> str:
    msg = str(exc).lower()
    if "openai_missing" in msg:
        return "llm_dependency_missing"
    if "layer1_llm_not_object" in msg or "jsondecodeerror" in msg or "expecting value" in msg:
        return "llm_malformed_output"
    if "timeout" in msg:
        return "llm_timeout"
    if "api" in msg or "auth" in msg or "rate" in msg:
        return "llm_provider_error"
    return "llm_error"


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
    key = (llm_api_key or os.environ.get("LEGAL_QA_LLM_API_KEY") or os.environ.get("LLM_API_KEY") or "").strip()
    has_key = bool(key)
    base = (llm_base_url or os.environ.get("LEGAL_QA_LLM_BASE_URL") or os.environ.get("LLM_BASE_URL") or "").strip() or "https://api.groq.com/openai/v1"
    mdl = (llm_model or os.environ.get("LEGAL_QA_LLM_MODEL") or os.environ.get("LLM_MODEL") or "").strip() or "llama-3.1-8b-instant"
    provider = (urlparse(base).netloc or urlparse(base).path or "openai_compatible").strip() or "openai_compatible"
    t0 = perf_counter()
    llm_err_reason: str | None = None

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
            llm_err_reason = _classify_llm_parse_error(e)

    h = parse_question_layer1_heuristic(question)
    meta = dict(h.parse_metadata)
    meta["parser_backend"] = "heuristic"
    meta["parser_provider"] = provider if use_llm else "heuristic"
    meta["parser_model"] = mdl if use_llm else None
    meta["parser_prompt_version"] = "v5_layer1_slot_prompt_1"
    meta["parser_latency_ms"] = round((perf_counter() - t0) * 1000.0, 3)
    if use_llm and has_key:
        meta["fallback_used"] = True
        meta["fallback_reason"] = llm_err_reason or "llm_error"
        meta["parser_backend_mode"] = "degraded"
    else:
        meta["fallback_used"] = False
        meta["fallback_reason"] = "no_llm_api_key" if use_llm and not has_key else "prefer_heuristic"
        meta["parser_backend_mode"] = "fallback"
    return h.model_copy(update={"parse_metadata": meta})
