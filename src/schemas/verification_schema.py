"""Verification outcomes across parsers, rules, reasoning, and answers."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class VerificationResult(BaseModel):
    """Unified record for symbolic or neural verification."""

    verifier_name: str
    target_id: str
    passed: bool
    severity: Literal["info", "warn", "error"] = "info"
    message: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
