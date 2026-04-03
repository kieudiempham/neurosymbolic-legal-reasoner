"""Build requirement sets from backward chaining results."""

from __future__ import annotations

from typing import Any


class RequirementBuilder:
    """Aggregates required facts/obligations for clarification and proof."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def build(self, backward_output: dict[str, Any]) -> dict[str, Any]:
        """Build a structured requirement set for one question id."""
        raise NotImplementedError
