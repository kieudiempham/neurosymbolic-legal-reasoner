"""Backward chaining from query goals to required facts."""

from __future__ import annotations

from typing import Any

from schemas.question_parse import Layer2Parse
from schemas.rule import RuleRecord


class BackwardChainer:
    """Drives goal-directed reasoning over a rule subset."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def chain(
        self, layer2: Layer2Parse, rules: list[RuleRecord]
    ) -> dict[str, Any]:
        """Produce subgoals, partial proofs, and a search trace."""
        raise NotImplementedError
