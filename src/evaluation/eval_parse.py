"""Metrics for layer-1/layer-2 parsing (exact match, slot F1, etc.)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def run_parse_eval(gold_path: Path, pred_path: Path) -> dict[str, Any]:
    """Load gold and predicted JSONL, compute metrics, write experiments/tables."""
    raise NotImplementedError
