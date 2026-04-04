"""Neural entailment / NLI for soft consistency checks."""

from __future__ import annotations

from typing import Any

from schemas.verification import VerificationResult


class NLIValidator:
    """NLI-based verification (premise, hypothesis) pairs."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def verify(self, premise: str, hypothesis: str) -> VerificationResult:
        """Load the NLI model and map entailment labels to pass or fail."""
        raise NotImplementedError
