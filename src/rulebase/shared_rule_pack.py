"""Minimal shared rule pack for Part C: bridge facts as structured facts."""

from __future__ import annotations

from typing import Any

from schemas.rule import RuleRecord, RuleHead
from schemas.rule_metadata import NormalizedRuleMeta


# Minimal canonical shared rules for bridge inference
SHARED_RULES: list[RuleRecord] = [
    RuleRecord(
        rule_id="shared_bridge_canonical_1",
        logic_form="bridge_fact(X) :- domain_fact(X), shared_condition(X)",
        head=RuleHead(predicate="bridge_fact", args=["X"]),
        body=[
            {"predicate": "domain_fact", "args": ["X"]},
            {"predicate": "shared_condition", "args": ["X"]}
        ],
        metadata={
            "rulebase_id": "shared_pack_v1",
            "layer": "shared",
            "domain": "shared",
            "source_doc": "shared_bridge_canonical",
            "source_article": "1",
            "canonical_head": {"predicate": "bridge_fact", "args": ["X"]},
            "canonical_body": [
                {"predicate": "domain_fact", "args": ["X"]},
                {"predicate": "shared_condition", "args": ["X"]}
            ],
            "surface_text": "Bridge fact generation from domain facts",
            "verbalized_vi": "Sinh fact bridge từ fact domain",
            "provenance": {"type": "canonical_shared", "version": "1.0"},
        },
    ),
    RuleRecord(
        rule_id="shared_bridge_canonical_2",
        logic_form="bridge_fact(Y) :- cross_domain_fact(X), transform(X, Y)",
        head=RuleHead(predicate="bridge_fact", args=["Y"]),
        body=[
            {"predicate": "cross_domain_fact", "args": ["X"]},
            {"predicate": "transform", "args": ["X", "Y"]}
        ],
        metadata={
            "rulebase_id": "shared_pack_v1",
            "layer": "shared",
            "domain": "shared",
            "source_doc": "shared_bridge_canonical",
            "source_article": "2",
            "canonical_head": {"predicate": "bridge_fact", "args": ["Y"]},
            "canonical_body": [
                {"predicate": "cross_domain_fact", "args": ["X"]},
                {"predicate": "transform", "args": ["X", "Y"]}
            ],
            "surface_text": "Bridge fact transformation from cross-domain facts",
            "verbalized_vi": "Biến đổi fact bridge từ fact cross-domain",
            "provenance": {"type": "canonical_shared", "version": "1.0"},
        },
    ),
]


def get_shared_rules() -> list[RuleRecord]:
    """Get all shared rules for bridge inference."""
    return SHARED_RULES.copy()


def get_bridge_canonical_rules() -> list[RuleRecord]:
    """Get canonical rules that generate bridge facts."""
    return [r for r in SHARED_RULES if r.metadata.layer == "bridge"]


def validate_shared_rule(rule: RuleRecord) -> bool:
    """Validate that a rule conforms to shared layer standards."""
    if not rule.metadata.domain == "shared":
        return False
    if rule.metadata.layer not in ["bridge", "canonical"]:
        return False
    return True


def register_shared_rule(rule: RuleRecord) -> None:
    """Register a new shared rule (for dynamic extension)."""
    if validate_shared_rule(rule):
        SHARED_RULES.append(rule)
    else:
        raise ValueError(f"Invalid shared rule: {rule.rule_id}")