"""Evaluate backward chaining (goal coverage, proof overlap)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def run_backward_eval(gold_path: Path, pred_path: Path) -> dict[str, Any]:
    """Compare predicted and gold requirement sets and proof skeletons."""
    raise NotImplementedError
