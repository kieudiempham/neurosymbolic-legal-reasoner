"""Retrieval metrics: MRR, nDCG, hit@k."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def run_retrieval_eval(gold_path: Path, pred_path: Path) -> dict[str, Any]:
    """Qrels-style metrics over retrieved rule ids."""
    raise NotImplementedError
