"""Shared rule pack loaded from cross-domain overlap analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from schemas.rule import RuleRecord, RuleHead
from schemas.rule_metadata import NormalizedRuleMeta


# Load shared rules from file (v2.5 — semantic motifs with labor support)
SHARED_RULES_FILE = Path(__file__).parent.parent.parent / "data" / "processed" / "shared_rule_pack_v2_5_refined.jsonl"
# Fallback to v2 if v2.5 doesn't exist
SHARED_RULES_FILE_V2 = Path(__file__).parent.parent.parent / "data" / "processed" / "shared_rule_pack_v2_semantic_motifs.jsonl"

def _load_shared_rules() -> list[RuleRecord]:
    """Load shared rules from JSONL file (v2.5 with labor support, falls back to v2)."""
    rules = []
    target_file = SHARED_RULES_FILE if SHARED_RULES_FILE.exists() else SHARED_RULES_FILE_V2
    
    if target_file.exists():
        with open(target_file, 'r', encoding='utf-8') as f:
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
                            "rulebase_id": "shared_motif_layer_v2_5",
                            "layer": "shared",
                            "domain": "shared",
                            "motif": data.get('motif', ''),
                            "source_domains": data.get('source_domains', []),
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
    head_pred = str(rule.head.predicate or "").strip().lower()
    logic_form = str(rule.logic_form or "").strip().lower()
    if not head_pred or head_pred == "unknown":
        return False
    if not logic_form or logic_form == "unknown":
        return False
    body = [c for c in (rule.body or []) if isinstance(c, dict)]
    meaningful_body = any(str(c.get("predicate") or "").strip().lower() not in {"", "unknown"} for c in body)
    has_head_args = any(str(a or "").strip() for a in (rule.head.args or []))
    if not meaningful_body and not has_head_args:
        return False
    return True


def register_shared_rule(rule: RuleRecord) -> None:
    """Register a new shared rule (for dynamic extension)."""
    if validate_shared_rule(rule):
        SHARED_RULES.append(rule)
    else:
        raise ValueError(f"Invalid shared rule: {rule.rule_id}")