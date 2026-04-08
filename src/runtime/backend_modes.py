"""Runtime backend mode declaration for per-request audit logs."""

from __future__ import annotations

from typing import Any


def _stage(provider: str | None = None, model: str | None = None, mode: str = "none") -> dict[str, Any]:
    return {
        "provider": provider,
        "model": model,
        "mode": mode,
    }


def init_backend_modes(*, verifier_engine: Any | None = None) -> dict[str, Any]:
    modes = {
        "parse_backend": _stage(),
        "answer_backend": _stage(),
        "verifier_backend": _stage(),
        "retrieval_backend": _stage(),
    }
    modes["verifier_backend"] = derive_verifier_backend(verifier_engine)
    return modes


def derive_verifier_backend(engine: Any | None) -> dict[str, Any]:
    if engine is None:
        return _stage(mode="none")
    meta = dict(getattr(engine, "_nli_meta", {}) or {})
    provider = str(meta.get("nli_provider") or "symbolic")
    model = meta.get("nli_model_name")
    degraded = bool(getattr(engine, "_nli_degraded", False))
    mock = bool(getattr(engine, "_nesy_nli_mock", False))
    if degraded:
        return _stage(provider=provider, model=model, mode="degraded")
    if mock:
        return _stage(provider=provider, model=model, mode="mock")
    if provider or model:
        return _stage(provider=provider, model=model, mode="real")
    return _stage(provider="symbolic", model=None, mode="none")


def apply_parse_backend(modes: dict[str, Any], layer1: Any | None) -> None:
    meta = getattr(layer1, "parse_metadata", None) or {}
    backend = str(meta.get("parser_backend") or "")
    provider = meta.get("parser_provider") or backend or "heuristic"
    model = meta.get("parser_model")
    backend_mode = str(meta.get("parser_backend_mode") or "").strip().lower()
    fallback_used = bool(meta.get("fallback_used", False))

    if not backend and layer1 is None:
        modes["parse_backend"] = _stage(mode="none")
        return

    if backend_mode in {"real", "fallback", "degraded", "mock", "none"}:
        modes["parse_backend"] = _stage(provider=str(provider), model=model, mode=backend_mode)
        return

    if fallback_used or backend == "heuristic":
        modes["parse_backend"] = _stage(provider=str(provider), model=model, mode="fallback")
        return

    if backend:
        modes["parse_backend"] = _stage(provider=str(provider), model=model, mode="real")
        return

    modes["parse_backend"] = _stage(provider=str(provider), model=model, mode="fallback")


def apply_retrieval_backend(
    modes: dict[str, Any],
    *,
    backend: str | None,
    retrieved_count: int,
) -> None:
    if not backend:
        modes["retrieval_backend"] = _stage(mode="none")
        return

    b = str(backend)
    low = b.lower()
    mode = "real"
    if "fallback" in low:
        mode = "fallback"
    elif "degraded" in low:
        mode = "degraded"
    elif "mock" in low:
        mode = "mock"
    elif retrieved_count <= 0:
        mode = "none"

    modes["retrieval_backend"] = _stage(provider="internal", model=b, mode=mode)


def apply_answer_backend(modes: dict[str, Any], answer: Any | None) -> None:
    if answer is None:
        modes["answer_backend"] = _stage(mode="none")
        return

    generation_mode = str(getattr(answer, "generation_mode", "") or "")
    if generation_mode == "llm_grounded":
        modes["answer_backend"] = _stage(provider="llm", model=generation_mode, mode="real")
        return
    if generation_mode:
        modes["answer_backend"] = _stage(provider="template", model=generation_mode, mode="fallback")
        return
    modes["answer_backend"] = _stage(provider="template", model=None, mode="fallback")
