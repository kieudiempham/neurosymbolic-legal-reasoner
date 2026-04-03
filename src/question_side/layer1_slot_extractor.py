"""Layer 1: semantic slot extraction (may be rule-based, hybrid, or LLM)."""

from __future__ import annotations

from typing import Any

from schemas.question_schema import Layer1SemanticSlots


class Layer1SlotExtractor:
    """Extracts semantic slots aligned with annotation guidelines."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def extract(self, question_id: str, raw_text: str) -> Layer1SemanticSlots:
        """Fill semantic slots: issue, jurisdiction, entities, and related fields."""
        raise NotImplementedError
