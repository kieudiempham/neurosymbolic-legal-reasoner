"""Path helpers and streaming line-based I/O for jsonl artifacts."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml


def read_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file into a plain dict."""
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """Stream JSONL records (one JSON object per line)."""
    import json

    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def write_jsonl(path: Path, records: Iterator[dict[str, Any]]) -> None:
    """Write records as JSONL."""
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def project_root_from_here(here: Path, levels_up: int = 3) -> Path:
    """Resolve the repo root by walking up `levels_up` parents from `here`."""
    return here.resolve().parents[levels_up]
