"""Retrieve candidate rules given a parsed question representation."""

from __future__ import annotations

from typing import Any

from schemas.question_schema import Layer2LogicObjects
from schemas.rule_schema import Rule


class RuleRetriever:
    """Bi-encoder, BM25, or hybrid retrieval over the rulebase."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def retrieve(self, layer2: Layer2LogicObjects, top_k: int) -> list[Rule]:
        """Load the rule index from data/processed/rulebase and return top-k."""
        raise NotImplementedError
