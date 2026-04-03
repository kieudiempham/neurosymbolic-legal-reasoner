"""Stable identifiers for questions, rules, proofs, and documents."""

from __future__ import annotations

import hashlib
import uuid


def new_id(prefix: str = "id") -> str:
    """Generate a unique string id with optional prefix."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def stable_hash(text: str, n: int = 16) -> str:
    """Deterministic short hash for deduplication keys."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:n]
