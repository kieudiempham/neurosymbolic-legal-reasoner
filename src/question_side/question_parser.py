"""Layer 1 parse — policy-driven LLM/heuristic parsing with explicit mode metadata."""

from __future__ import annotations

import logging
import os
from urllib.parse import urlparse
from typing import TYPE_CHECKING, Any

from schemas.question_parse import Layer1Parse
from question_side.heuristic_layer1 import parse_question_layer1_heuristic
from question_side.llm_layer1_parser import parse_layer1_llm
from utils.semantic_families import normalize_family

if TYPE_CHECKING:
    from app.config import Settings

logger = logging.getLogger(__name__)

_PARSER_MODE_REQUIRED = "llm_required"
_PARSER_MODE_PREFER = "prefer_llm"
_PARSER_MODE_HEURISTIC = "heuristic_only"
_VALID_PARSER_MODES = {
    _PARSER_MODE_REQUIRED,
    _PARSER_MODE_PREFER,
    _PARSER_MODE_HEURISTIC,
}


def _env_flag(name: str, default: bool) -> bool:
    v = os.environ.get(name, "").strip().lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "on")


def _classify_llm_parse_error(exc: Exception) -> str:
    msg = str(exc).lower()
    if "no_api_key" in msg:
        return "missing_api_key"
    if "openai_missing" in msg:
        return "llm_dependency_missing"
    if "layer1_llm_not_object" in msg or "jsondecodeerror" in msg or "expecting value" in msg:
        return "llm_malformed_output"
    if "timeout" in msg:
        return "llm_timeout"
    if "api" in msg or "auth" in msg or "rate" in msg:
        return "llm_provider_error"
    return "llm_error"


def _resolve_parser_mode(prefer_llm: bool | None) -> str:
    if prefer_llm is True:
        return _PARSER_MODE_PREFER
    if prefer_llm is False:
        return _PARSER_MODE_HEURISTIC

    raw = (
        os.environ.get("QUESTION_PARSER_MODE")
        or os.environ.get("LEGAL_QA_QUESTION_PARSER_MODE")
        or ""
    ).strip().lower()
    if raw in _VALID_PARSER_MODES:
        return raw
    return _PARSER_MODE_REQUIRED


def _resolve_allow_fallback(default: bool = False) -> bool:
    return _env_flag("QUESTION_PARSER_ALLOW_FALLBACK", _env_flag("LEGAL_QA_QUESTION_PARSER_ALLOW_FALLBACK", default))


class ParserUnavailableError(RuntimeError):
    """Raised when Layer-1 parse cannot run with a real LLM backend."""

    def __init__(self, parser_error: str, *, parse_metadata: dict[str, Any]) -> None:
        super().__init__(parser_error)
        self.parser_error = parser_error
        self.parse_metadata = dict(parse_metadata)


def _resolve_model(llm_model: str | None) -> str | None:
    model = (
        llm_model
        or os.environ.get("LEGAL_QA_LLM_MODEL")
        or os.environ.get("LLM_MODEL")
        or ""
    ).strip()
    return model or None


def _resolve_base_url(llm_base_url: str | None) -> str | None:
    base = (
        llm_base_url
        or os.environ.get("LEGAL_QA_LLM_BASE_URL")
        or os.environ.get("LLM_BASE_URL")
        or ""
    ).strip()
    return base or None


def _resolve_provider(base_url: str | None) -> str | None:
    if not base_url:
        return None
    parsed = urlparse(base_url)
    provider = (parsed.netloc or parsed.path or "").strip()
    return provider or None


def _build_parse_meta(
    *,
    requested_mode: str,
    provider: str | None,
    model: str | None,
    parser_backend: str,
    actual_mode: str,
    parser_fallback_mode: str | None,
    fallback_used: bool,
    fallback_reason: str | None,
    parser_available: bool,
    parser_error: str | None,
) -> dict[str, Any]:
    meta = {
        "requested_mode": requested_mode,
        "parse_mode": actual_mode,
        "actual_mode": actual_mode,
        "provider": provider,
        "model": model,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "parser_fallback_mode": parser_fallback_mode,
        "parser_available": parser_available,
        "parser_error": parser_error,
        "parser_backend": parser_backend,
        "parser_provider": provider,
        "parser_model": model,
        "parser_backend_mode": actual_mode,
    }
    return meta


def _normalize_semantic_parse_metadata(parsed: Layer1Parse) -> Layer1Parse:
    meta = dict(parsed.parse_metadata or {})
    raw_focus = meta.get("question_focus_hint")
    if raw_focus is not None and str(raw_focus).strip().lower() == "legal_consequence":
        meta["question_focus_hint"] = "legal_effect"
    raw_condition_family = meta.get("condition_family_hint")
    if raw_condition_family is not None:
        normalized = normalize_family(raw_condition_family)
        meta["condition_family_hint"] = normalized or "unknown"
    return parsed.model_copy(update={"parse_metadata": meta})


def parse_question_layer1(
    question: str,
    *,
    settings: Settings | None = None,
    prefer_llm: bool | None = None,
    llm_api_key: str | None = None,
    llm_base_url: str | None = None,
    llm_model: str | None = None,
) -> Layer1Parse:
    """
    Primary entry: parse using QUESTION_PARSER_MODE policy.
    Supported requested modes: llm_required, prefer_llm, heuristic_only.
    
    If settings is provided, uses its LLM config (from .env); otherwise falls back to
    individual params and os.environ. Using settings is recommended for reliable .env loading.
    
    Env when settings is None: QUESTION_PARSER_MODE, QUESTION_PARSER_ALLOW_FALLBACK, LEGAL_QA_LLM_*.
    """
    requested_mode = _resolve_parser_mode(prefer_llm)
    allow_fallback = _resolve_allow_fallback(default=False)
    
    # Load LLM config from settings (preferred) or fall back to parameters + os.environ
    if settings:
        key = (settings.llm_api_key or "").strip()
        base = settings.llm_base_url or ""
        model = settings.llm_model or ""
        requested_mode = settings.question_parser_mode
        allow_fallback = settings.question_parser_allow_fallback
    else:
        key = (llm_api_key or os.environ.get("LEGAL_QA_LLM_API_KEY") or os.environ.get("LLM_API_KEY") or "").strip()
        base = _resolve_base_url(llm_base_url)
        model = _resolve_model(llm_model)
    
    provider = _resolve_provider(base)

    def _heuristic_result(*, reason: str, fallback_used: bool, parser_error: str | None) -> Layer1Parse:
        h = parse_question_layer1_heuristic(question)
        h_meta = _build_parse_meta(
            requested_mode=requested_mode,
            provider="heuristic",
            model="heuristic_layer1_v2",
            parser_backend="heuristic",
            actual_mode="heuristic_fallback",
            parser_fallback_mode=reason,
            fallback_used=fallback_used,
            fallback_reason=reason,
            parser_available=False,
            parser_error=parser_error,
        )
        # Keep attempted LLM target visible without pretending it was the actual parser.
        h_meta["attempted_provider"] = provider
        h_meta["attempted_model"] = model
        return _normalize_semantic_parse_metadata(h.model_copy(update={"parse_metadata": h_meta}))

    if requested_mode == _PARSER_MODE_HEURISTIC:
        return _heuristic_result(
            reason="heuristic_only_mode",
            fallback_used=False,
            parser_error=None,
        )

    if not key:
        if requested_mode == _PARSER_MODE_PREFER and allow_fallback:
            return _heuristic_result(
                reason="missing_api_key",
                fallback_used=True,
                parser_error="missing_api_key",
            )
        meta = _build_parse_meta(
            requested_mode=requested_mode,
            provider=provider,
            model=model,
            parser_backend="unavailable",
            actual_mode="parse_unavailable",
            parser_fallback_mode=None,
            fallback_used=False,
            fallback_reason=None,
            parser_available=False,
            parser_error="missing_api_key",
        )
        raise ParserUnavailableError("missing_api_key", parse_metadata=meta)
    if not base:
        if requested_mode == _PARSER_MODE_PREFER and allow_fallback:
            return _heuristic_result(
                reason="missing_provider",
                fallback_used=True,
                parser_error="missing_provider",
            )
        meta = _build_parse_meta(
            requested_mode=requested_mode,
            provider=None,
            model=model,
            parser_backend="unavailable",
            actual_mode="parse_unavailable",
            parser_fallback_mode=None,
            fallback_used=False,
            fallback_reason=None,
            parser_available=False,
            parser_error="missing_provider",
        )
        raise ParserUnavailableError("missing_provider", parse_metadata=meta)
    if not provider:
        if requested_mode == _PARSER_MODE_PREFER and allow_fallback:
            return _heuristic_result(
                reason="missing_provider",
                fallback_used=True,
                parser_error="missing_provider",
            )
        meta = _build_parse_meta(
            requested_mode=requested_mode,
            provider=None,
            model=model,
            parser_backend="unavailable",
            actual_mode="parse_unavailable",
            parser_fallback_mode=None,
            fallback_used=False,
            fallback_reason=None,
            parser_available=False,
            parser_error="missing_provider",
        )
        raise ParserUnavailableError("missing_provider", parse_metadata=meta)
    if not model:
        if requested_mode == _PARSER_MODE_PREFER and allow_fallback:
            return _heuristic_result(
                reason="missing_model",
                fallback_used=True,
                parser_error="missing_model",
            )
        meta = _build_parse_meta(
            requested_mode=requested_mode,
            provider=provider,
            model=None,
            parser_backend="unavailable",
            actual_mode="parse_unavailable",
            parser_fallback_mode=None,
            fallback_used=False,
            fallback_reason=None,
            parser_available=False,
            parser_error="missing_model",
        )
        raise ParserUnavailableError("missing_model", parse_metadata=meta)

    try:
        l1, _trace = parse_layer1_llm(
            question,
            api_key=key,
            base_url=base,
            model=model,
        )
    except Exception as e:
        err = _classify_llm_parse_error(e)
        if requested_mode == _PARSER_MODE_PREFER and allow_fallback:
            logger.warning("layer1_llm_failed_using_heuristic_fallback: %s", e)
            return _heuristic_result(
                reason=err,
                fallback_used=True,
                parser_error=err,
            )

        logger.warning("layer1_llm_unavailable_no_fallback: %s", e)
        meta = _build_parse_meta(
            requested_mode=requested_mode,
            provider=provider,
            model=model,
            parser_backend="unavailable",
            actual_mode="parse_unavailable",
            parser_fallback_mode=None,
            fallback_used=False,
            fallback_reason=None,
            parser_available=False,
            parser_error=err,
        )
        raise ParserUnavailableError(err, parse_metadata=meta) from e

    meta = dict(l1.parse_metadata or {})
    meta.update(
        _build_parse_meta(
            requested_mode=requested_mode,
            provider=provider,
            model=model,
            parser_backend="llm",
            actual_mode="llm_real",
            parser_fallback_mode=None,
            fallback_used=False,
            fallback_reason=None,
            parser_available=True,
            parser_error=None,
        )
    )
    return _normalize_semantic_parse_metadata(l1.model_copy(update={"parse_metadata": meta}))
