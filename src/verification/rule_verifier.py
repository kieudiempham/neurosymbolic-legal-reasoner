"""Verify rule correctness w.r.t. schema and source text."""

from __future__ import annotations

from typing import Any

from schemas.rule_schema import Rule
from schemas.verification_schema import VerificationResult


class RuleVerifier:
    """Cross-checks rules against frames and legal text."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def verify(self, rule: Rule, evidence: dict[str, Any]) -> VerificationResult:
        """Check that rule heads and bodies align with the retrieved text."""
        raise NotImplementedError
