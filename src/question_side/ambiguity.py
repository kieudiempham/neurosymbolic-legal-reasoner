"""Ambiguity taxonomy + helpers for clarification (parse-side)."""

from __future__ import annotations

from typing import Any, Literal

AmbiguityType = Literal[
    "ambiguous_subject",
    "ambiguous_condition",
    "ambiguous_action",
    "ambiguous_modality",
    "ambiguous_time",
    "ambiguous_exception",
    "ambiguous_goal",
]


def make_ambiguity(
    *,
    kind: AmbiguityType,
    field: str,
    source_text: str,
    candidates: list[str],
    confidence_gap: float,
    blocking: bool,
    priority: int,
    blocking_reason: str = "",
) -> dict[str, Any]:
    return {
        "type": kind,
        "field": field,
        "source_text": source_text,
        "candidates": candidates,
        "confidence_gap": confidence_gap,
        "blocking": blocking,
        "priority": priority,
        "blocking_reason": blocking_reason,
    }
