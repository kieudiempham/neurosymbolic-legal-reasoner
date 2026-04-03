"""Retrieve textual evidence spans (statutes, commentary) for verification."""

from __future__ import annotations

from typing import Any

from schemas.rule_schema import Rule


class EvidenceRetriever:
    """Fetches evidence aligned with retrieved rules."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def retrieve(self, rule: Rule, top_k: int) -> list[dict[str, Any]]:
        """Return evidence dicts with doc_id, span, and snippet text."""
        raise NotImplementedError
