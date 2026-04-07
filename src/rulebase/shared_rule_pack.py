"""Shared rule pack loaded from cross-domain overlap analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from schemas.rule import RuleRecord, RuleHead
from schemas.rule_metadata import NormalizedRuleMeta


# Load shared rules from file
SHARED_RULES_FILE = Path(__file__).parent.parent.parent / "data" / "processed" / "shared_rule_pack.jsonl"

def _load_shared_rules() -> list[RuleRecord]:
    """Load shared rules from JSONL file."""
    rules = []
    if SHARED_RULES_FILE.exists():
        with open(SHARED_RULES_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    # Convert to RuleRecord format
                    rule = RuleRecord(
                        rule_id=data['rule_id'],
                        logic_form=data.get('logic_form', ''),
                        head=RuleHead(
                            predicate=data['canonical_head']['predicate'],
                            args=data['canonical_head']['args']
                        ),
                        body=data.get('canonical_body', []),
                        metadata={
                            "rulebase_id": "shared_pack_v1",
                            "layer": "shared",
                            "domain": "shared",
                            **data
                        }
                    )
                    rules.append(rule)
    return rules

SHARED_RULES: list[RuleRecord] = _load_shared_rules()


def get_shared_rules() -> list[RuleRecord]:
    """Get all shared rules from cross-domain overlap."""
    return SHARED_RULES.copy()


def get_bridge_canonical_rules() -> list[RuleRecord]:
    """Get canonical rules that generate bridge facts (legacy)."""
    return []  # No bridge rules in new shared layer


def validate_shared_rule(rule: RuleRecord) -> bool:
    """Validate that a rule conforms to shared layer standards."""
    if rule.metadata.get('domain') != "shared":
        return False
    if rule.metadata.get('layer') not in ["shared"]:
        return False
    return True


def register_shared_rule(rule: RuleRecord) -> None:
    """Register a new shared rule (for dynamic extension)."""
    if validate_shared_rule(rule):
        SHARED_RULES.append(rule)
    else:
        raise ValueError(f"Invalid shared rule: {rule.rule_id}")