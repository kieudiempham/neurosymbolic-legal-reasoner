"""Verify question parse quality and consistency."""

from __future__ import annotations

from typing import Any

from schemas.question_schema import Layer2LogicObjects
from schemas.verification_schema import VerificationResult


class ParseVerifier:
    """Checks layer-2 objects against ontology and slot coverage."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def verify(self, layer2: Layer2LogicObjects) -> VerificationResult:
        """Validate slot coverage and that terms belong to the ontology."""
        raise NotImplementedError
