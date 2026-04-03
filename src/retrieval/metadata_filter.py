"""Filter candidates by jurisdiction, time, document type, etc."""

from __future__ import annotations

from typing import Any

from schemas.rule_schema import Rule


class MetadataFilter:
    """Applies structured filters before or after retrieval."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def filter(self, rules: list[Rule], context: dict[str, Any]) -> list[Rule]:
        """Filter candidates using provenance.meta fields."""
        raise NotImplementedError
