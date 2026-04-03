"""End-to-end answer evaluation (exact match, token F1, citation overlap)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def run_answer_eval(gold_path: Path, pred_path: Path) -> dict[str, Any]:
    """Standard QA scores plus flags when the answer disagrees with the proof."""
    raise NotImplementedError
