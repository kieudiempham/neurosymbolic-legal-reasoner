"""Resolve project root (`legal-qa-nesy/`) for config and data paths."""

from __future__ import annotations

from pathlib import Path


def legal_qa_nesy_root() -> Path:
    """Return directory containing configs/, data/, src/ (this file: pipelines/)."""
    return Path(__file__).resolve().parents[2]
