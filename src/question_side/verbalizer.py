"""Turn internal structures back to natural language (debugging, clarification)."""

from __future__ import annotations

from typing import Any

from schemas.question_schema import Layer2LogicObjects


class Verbalizer:
    """Human-readable summaries of logic objects and retrieval intents."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def verbalize(self, layer2: Layer2LogicObjects) -> str:
        """Turn structured parses into readable text for notebooks or reports."""
        raise NotImplementedError
