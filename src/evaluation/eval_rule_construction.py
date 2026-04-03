"""Evaluate rule extraction against gold rule annotations."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def run_rule_eval(gold_path: Path, pred_path: Path) -> dict[str, Any]:
    """Predicate-level precision/recall and structural match of rules."""
    raise NotImplementedError
