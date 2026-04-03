"""Skeleton tests for schemas and pipeline wiring (no full E2E yet)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipelines.run_end2end_pipeline import run


def test_end2end_run_stub_raises(tmp_path: Path) -> None:
    cfg = tmp_path / "exp.yaml"
    cfg.write_text("name: t\n", encoding="utf-8")
    with pytest.raises(NotImplementedError):
        run(cfg)
