"""Deprecated stub — use `verification.engine.NeSyEngine.verify_rule` (v5 `rule_verification`)."""

from __future__ import annotations

from typing import Any

from schemas.rule import RuleRecord
from schemas.verification import VerificationResult


class RuleVerifier:
    """Deprecated: NeSyEngine + `rule_verification` mode is the source of truth."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def verify(self, rule: RuleRecord, evidence: dict[str, Any]) -> VerificationResult:
        raise NotImplementedError("Use NeSyEngine.verify_rule")
