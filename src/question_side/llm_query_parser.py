"""LLM-based parser producing an initial structured parse of the user question."""

from __future__ import annotations

from typing import Any

from schemas.question_schema import Layer1SemanticSlots


class LLMQueryParser:
    """Wraps LLM calls for question parsing (prompts, retries, schema validation)."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def parse(self, question_id: str, raw_text: str) -> Layer1SemanticSlots:
        """Call the model and validate the reply into Layer1SemanticSlots."""
        raise NotImplementedError
