"""Reload rule records from the curated rulebase — used by NeSy rule repair (no string-tweaking)."""

from __future__ import annotations

from retrieval.rulebase_loader import RulebaseIndex
from schemas.rule import RuleRecord


def reload_rule_from_index(index: RulebaseIndex, rule_id: str) -> RuleRecord | None:
    """Return the canonical `RuleRecord` for ``rule_id`` from the loaded index."""
    return index.by_id.get(rule_id)
