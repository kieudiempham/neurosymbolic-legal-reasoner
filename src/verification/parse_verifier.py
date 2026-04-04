"""Deprecated stub — use `verification.engine.NeSyEngine.verify_parse` (v5)."""

from __future__ import annotations

from typing import Any

from schemas.question_parse import Layer2Parse
from schemas.verification import VerificationResult


class ParseVerifier:
    """Deprecated: NeSyEngine + `parse_verification` mode is the source of truth."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def verify(self, layer2: Layer2Parse) -> VerificationResult:
        raise NotImplementedError("Use NeSyEngine.verify_parse")
