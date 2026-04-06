"""Build shared registries from domain rulebases.

Phase 3: Extract shared entities, predicates, and rules across domains.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from utils.logger import get_logger

logger = get_logger(__name__)


def build_shared_entities_registry(
    domain_rulebases: list[Path],
    output_path: Path,
) -> dict[str, Any]:
    """Extract shared entities from domain rulebases.
    
    Args:
        domain_rulebases: List of domain_rulebase.jsonl paths
        output_path: Output path for shared_entities.json
    
    Returns:
        Summary dict
    """
    entity_counter: Counter[str] = Counter()
    
    for rb_path in domain_rulebases:
        with rb_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    # Extract entities from canonical_head/canonical_body
                    head = data.get("canonical_head", {})
                    body = data.get("canonical_body", [])
                    
                    # Simple entity extraction (placeholder)
                    entities = _extract_entities_from_rule(head, body)
                    entity_counter.update(entities)
    
    # Filter shared entities (appear in multiple domains)
    shared_entities = {
        entity: count for entity, count in entity_counter.items()
        if count > 1  # Placeholder threshold
    }
    
    registry = {
        "registry_type": "shared_entities",
        "entities": list(shared_entities.keys()),
        "counts": dict(shared_entities),
        "source_domains": len(domain_rulebases),
    }
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Built shared entities registry: {len(shared_entities)} entities")
    return registry


def build_shared_predicates_registry(
    domain_rulebases: list[Path],
    output_path: Path,
) -> dict[str, Any]:
    """Extract shared predicates from domain rulebases.
    
    Args:
        domain_rulebases: List of domain_rulebase.jsonl paths
        output_path: Output path for shared_predicates.json
    
    Returns:
        Summary dict
    """
    predicate_counter: Counter[str] = Counter()
    
    for rb_path in domain_rulebases:
        with rb_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    head = data.get("canonical_head", {})
                    body = data.get("canonical_body", [])
                    
                    predicates = _extract_predicates_from_rule(head, body)
                    predicate_counter.update(predicates)
    
    # Filter shared predicates
    shared_predicates = {
        pred: count for pred, count in predicate_counter.items()
        if count > 1
    }
    
    registry = {
        "registry_type": "shared_predicates",
        "predicates": list(shared_predicates.keys()),
        "counts": dict(shared_predicates),
        "source_domains": len(domain_rulebases),
    }
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Built shared predicates registry: {len(shared_predicates)} predicates")
    return registry


def build_shared_rule_pack(
    domain_rulebases: list[Path],
    shared_entities: dict[str, Any],
    shared_predicates: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    """Build shared rule pack from common patterns across domains.
    
    Args:
        domain_rulebases: List of domain_rulebase.jsonl paths
        shared_entities: Shared entities registry
        shared_predicates: Shared predicates registry
        output_path: Output path for shared_rule_pack.jsonl
    
    Returns:
        Summary dict
    """
    shared_rules: list[dict[str, Any]] = []
    
    # Placeholder: Extract rules that use shared entities/predicates
    # In practice, this would involve more sophisticated pattern matching
    
    # Example shared rule: entity relationships
    if "doanh_nghiep" in shared_entities.get("entities", []):
        shared_rule = {
            "rule_id": "SHARED_ENT_001",
            "domain": "shared",
            "layer": "shared",
            "rulebase_id": "shared_bridge",
            "logic_form": "definition",
            "canonical_head": {"predicate": "is_entity_type", "args": ["X", "doanh_nghiep"]},
            "canonical_body": [],
            "verbalized_vi": "X là một doanh nghiệp",
            "derived_from_domains": ["enterprise", "labor"],
        }
        shared_rules.append(shared_rule)
    
    with output_path.open("w", encoding="utf-8") as f:
        for rule in shared_rules:
            f.write(json.dumps(rule, ensure_ascii=False) + "\n")
    
    summary = {
        "shared_rule_count": len(shared_rules),
        "output_path": str(output_path),
    }
    
    logger.info(f"Built shared rule pack: {len(shared_rules)} rules")
    return summary


def _extract_entities_from_rule(head: dict[str, Any], body: list[dict[str, Any]]) -> list[str]:
    """Placeholder entity extraction."""
    entities: list[str] = []
    # Simple: look for known entity patterns in args
    known_entities = ["doanh_nghiep", "nguoi_lao_dong", "co_quan_thue"]
    for item in [head] + body:
        args = item.get("args", [])
        for arg in args:
            if isinstance(arg, str) and arg in known_entities:
                entities.append(arg)
    return entities


def _extract_predicates_from_rule(head: dict[str, Any], body: list[dict[str, Any]]) -> list[str]:
    """Placeholder predicate extraction."""
    predicates: list[str] = []
    for item in [head] + body:
        pred = item.get("predicate")
        if isinstance(pred, str):
            predicates.append(pred)
    return list(set(predicates))