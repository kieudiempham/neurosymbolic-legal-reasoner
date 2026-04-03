"""Aggregate per-run metrics into paper-ready tables."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def summarize(run_dirs: list[Path], out_md: Path) -> None:
    """Merge per-run JSON metrics and emit markdown or LaTeX table snippets."""
    raise NotImplementedError
