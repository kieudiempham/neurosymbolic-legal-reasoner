"""Rerank retrieved rules with cross-encoder or symbolic features."""

from __future__ import annotations

from typing import Any

from schemas.question_schema import Layer2LogicObjects
from schemas.rule_schema import Rule


class RuleRanker:
    """Scores and orders rule candidates."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def rank(
        self, layer2: Layer2LogicObjects, candidates: list[Rule]
    ) -> list[tuple[Rule, float]]:
        """Sort rules by score, highest first."""
        raise NotImplementedError
