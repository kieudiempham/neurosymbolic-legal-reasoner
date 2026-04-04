"""Load parse regression JSON cases from tests/fixtures (shared by scripts and tests)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE_DIR = _REPO_ROOT / "tests" / "fixtures"

_DEFAULT_FILES = (
    "parse_regression_questions_core.json",
    "parse_regression_questions_ambiguity.json",
    "parse_regression_questions_roles.json",
)


def fixture_dir() -> Path:
    return _FIXTURE_DIR


def load_parse_regression_cases(*, files: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
    names = files if files is not None else _DEFAULT_FILES
    out: list[dict[str, Any]] = []
    for fn in names:
        path = _FIXTURE_DIR / fn
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"{fn}: expected JSON array")
        for i, row in enumerate(data):
            if not isinstance(row, dict):
                raise ValueError(f"{fn}[{i}]: expected object")
            out.append(row)
    return out
