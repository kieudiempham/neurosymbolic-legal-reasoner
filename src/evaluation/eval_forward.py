"""Evaluate forward chaining outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def run_forward_eval(gold_path: Path, pred_path: Path) -> dict[str, Any]:
    """Overlap with gold facts and alignment of forward proof steps."""
    raise NotImplementedError
