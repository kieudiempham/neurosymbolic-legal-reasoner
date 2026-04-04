"""Deprecated stub — use `NeSyEngine.verify_forward` (`forward_verification` mode)."""

from __future__ import annotations

from typing import Any

from schemas.verification import VerificationResult


class ForwardVerifier:
    """Checks forward applications against rule semantics."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def verify(self, forward_output: dict[str, Any]) -> VerificationResult:
        """Check that each step maps to a valid rule application."""
        raise NotImplementedError
