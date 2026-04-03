"""Generate clarification questions for missing or ambiguous facts."""

from __future__ import annotations

from typing import Any


class ClarificationGenerator:
    """Produces user-facing clarification questions (template or LLM)."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def generate(self, missing_facts: list[str], context: dict[str, Any]) -> list[str]:
        """Return clarification questions ordered by expected information gain."""
        raise NotImplementedError
