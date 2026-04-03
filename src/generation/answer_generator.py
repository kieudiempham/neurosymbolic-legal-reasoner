"""Generate final answers (template or LLM) grounded in proofs."""

from __future__ import annotations

from typing import Any

from schemas.proof_schema import Proof


class AnswerGenerator:
    """Produces user-facing answers with optional citation strings."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def generate(self, proof: Proof | None, context: dict[str, Any]) -> str:
        """Generate an answer conditioned on retrieved evidence and constraints."""
        raise NotImplementedError
