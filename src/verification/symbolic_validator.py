"""Structural and logic checks without neural models."""

from __future__ import annotations

from typing import Any

from schemas.verification_schema import VerificationResult


class SymbolicValidator:
    """Schema, typing, and consistency validation."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def validate(self, payload: dict[str, Any]) -> VerificationResult:
        """Dispatch to the right checker based on the payload type."""
        raise NotImplementedError
