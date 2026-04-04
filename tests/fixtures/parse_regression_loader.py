"""Backward-compat shim — implementation lives in ``question_side.parse_regression_fixtures``."""

from __future__ import annotations

from question_side.parse_regression_fixtures import load_parse_regression_cases as load_parse_regression_cases

__all__ = ["load_parse_regression_cases", "load_legacy_string_questions"]


def load_legacy_string_questions() -> list[str]:
    return [c["question_text"] for c in load_parse_regression_cases() if c.get("question_text")]
