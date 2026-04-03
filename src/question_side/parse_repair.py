"""Repair invalid or incomplete parses using heuristics or second-pass LLM."""

from __future__ import annotations

from typing import Any

from schemas.question_schema import Layer1SemanticSlots, Layer2LogicObjects


class ParseRepair:
    """Attempts to fix schema violations and missing slots."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def repair(
        self,
        layer1: Layer1SemanticSlots,
        layer2: Layer2LogicObjects | None,
        diagnostics: dict[str, Any],
    ) -> tuple[Layer1SemanticSlots, Layer2LogicObjects | None]:
        """Repair parses in rounds and write diagnostics next to interim JSONL."""
        raise NotImplementedError
