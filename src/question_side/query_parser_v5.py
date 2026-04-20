"""Unified v5 query parser facade: Layer1 + Layer2 + parser metadata."""

from __future__ import annotations

from typing import Any

from question_side.question_normalizer import build_layer2
from question_side.question_parser import parse_question_layer1
from schemas.question_parse import Layer1Parse, Layer2Parse


def _resolved_backend_mode(meta: dict[str, Any]) -> str:
    mode = str(meta.get("actual_mode") or meta.get("parser_backend_mode") or "").strip().lower()
    if mode in {"llm_real", "heuristic_fallback", "parse_unavailable"}:
        return mode
    if str(meta.get("parser_backend") or "").strip().lower() == "heuristic":
        return "heuristic_fallback"
    if bool(meta.get("parser_available", False)):
        return "llm_real"
    return "parse_unavailable"


def parse(
    query: str,
    *,
    user_facts: list[str] | None = None,
    forced_condition_atoms: list[str] | None = None,
    prefer_llm: bool | None = None,
    llm_api_key: str | None = None,
    llm_base_url: str | None = None,
    llm_model: str | None = None,
    settings: Any | None = None,
) -> tuple[Layer1Parse, Layer2Parse, dict[str, Any]]:
    layer1 = parse_question_layer1(
        query,
        settings=settings,
        prefer_llm=prefer_llm,
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        llm_model=llm_model,
    )
    layer2 = build_layer2(
        layer1,
        user_facts=user_facts or [],
        forced_condition_atoms=forced_condition_atoms,
    )

    meta = dict(layer1.parse_metadata or {})
    meta["parser_backend_mode"] = _resolved_backend_mode(meta)
    meta["query_parser_version"] = "v5"
    meta["layer2_built"] = True
    return layer1, layer2, meta
