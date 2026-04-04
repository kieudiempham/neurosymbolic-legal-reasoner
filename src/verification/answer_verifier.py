"""Deprecated stub — use `NeSyEngine.verify_answer` (`answer_verification` mode)."""

from __future__ import annotations

from typing import Any

from schemas.proof import ProofObject
from schemas.verification import VerificationResult


class AnswerVerifier:
    """Ensures answers are entailed by evidence + proof (symbolic or NLI)."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def verify(self, answer: str, proof: ProofObject | None) -> VerificationResult:
        """Run symbolic checks first, then NLI where configured."""
        raise NotImplementedError
