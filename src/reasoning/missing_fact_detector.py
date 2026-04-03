"""Detect missing facts relative to available facts and rules."""

from __future__ import annotations

from typing import Any


class MissingFactDetector:
    """Identifies gaps that block entailment or proof completion."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def detect(self, requirement_set: dict[str, Any], facts: dict[str, Any]) -> list[str]:
        """List facts still needed to close the proof."""
        raise NotImplementedError
