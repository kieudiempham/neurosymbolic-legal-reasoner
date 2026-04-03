"""Layer 2: map layer-1 slots to logical objects for reasoning."""

from __future__ import annotations

from typing import Any

from schemas.question_schema import Layer1SemanticSlots, Layer2LogicObjects


class Layer2Normalizer:
    """Normalizes semantic slots into logic objects (goals, queries, constraints)."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def normalize(self, layer1: Layer1SemanticSlots) -> Layer2LogicObjects:
        """Map surface forms to ontology ids and check internal consistency."""
        raise NotImplementedError
