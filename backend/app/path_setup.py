"""Ensure repo root and `src/` are importable (schemas.*, src.*)."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_src_paths() -> Path:
    """Return repository root. Idempotent."""
    backend_dir = Path(__file__).resolve().parents[1]
    root = backend_dir.parent
    src = root / "src"
    for p in (root, src):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)
    return root
