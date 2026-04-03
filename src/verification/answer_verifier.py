"""Verify final natural-language answers against proofs and sources."""

from __future__ import annotations

from typing import Any

from schemas.proof_schema import Proof
from schemas.verification_schema import VerificationResult


class AnswerVerifier:
    """Ensures answers are entailed by evidence + proof (symbolic or NLI)."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def verify(self, answer: str, proof: Proof | None) -> VerificationResult:
        """Run symbolic checks first, then NLI where configured."""
        raise NotImplementedError
