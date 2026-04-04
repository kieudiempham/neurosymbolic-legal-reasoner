"""Exports rules to jsonl, index files, and optional logic-engine formats."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from schemas.rule import RuleRecord


class RuleExporter:
    """Writes `data/processed/rulebase/*` artifacts."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def export(self, rules: list[RuleRecord], out_dir: Path) -> None:
        """Emit rules_logic.jsonl, rule_index.json, and rule_groups.json."""
        raise NotImplementedError
