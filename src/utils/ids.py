"""Stable identifiers for questions, rules, proofs, and documents."""

from __future__ import annotations

import hashlib
import secrets
import time
import uuid


def new_id(prefix: str = "id") -> str:
    """Generate a unique string id with optional prefix."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def stable_hash(text: str, n: int = 16) -> str:
    """Deterministic short hash for deduplication keys."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:n]


def new_session_id() -> str:
    return f"sess_{int(time.time() * 1000)}_{secrets.token_hex(4)}"


def new_proof_id() -> str:
    return f"proof_{secrets.token_hex(8)}"


def new_trace_id() -> str:
    return f"trace_{secrets.token_hex(6)}"
