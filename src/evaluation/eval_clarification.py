"""Evaluate clarification quality (relevance, coverage)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def run_clarification_eval(gold_path: Path, pred_path: Path) -> dict[str, Any]:
    """Optional BLEU against references; hooks for human-judged usefulness."""
    raise NotImplementedError
