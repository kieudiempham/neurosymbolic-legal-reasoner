"""Verify backward chaining traces."""

from __future__ import annotations

from typing import Any

from schemas.verification_schema import VerificationResult


class BackwardVerifier:
    """Checks soundness of backward reasoning outputs."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def verify(self, backward_output: dict[str, Any]) -> VerificationResult:
        """Ensure goals are covered and the goal graph has no bad cycles."""
        raise NotImplementedError
