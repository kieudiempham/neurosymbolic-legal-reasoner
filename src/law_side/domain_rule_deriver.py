"""Derive domain-level rulebases from statute-specific packs.

Phase 3: Aggregate statute packs into domain rulebases with provenance.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from schemas.canonical_rule import CanonicalRuleArtifact
from utils.logger import get_logger

logger = get_logger(__name__)


def derive_domain_rulebase(
    statute_packs_dir: Path,
    domain: str,
    output_path: Path,
) -> dict[str, Any]:
    """Aggregate statute packs into a domain rulebase.
    
    Args:
        statute_packs_dir: Directory containing statute_pack_*.jsonl files
        domain: Domain name (e.g., 'enterprise')
        output_path: Output path for domain_rulebase.jsonl
    
    Returns:
        Summary dict with counts and provenance
    """
    all_rules: list[CanonicalRuleArtifact] = []
    pack_summaries: dict[str, dict[str, Any]] = {}
    
    for pack_file in statute_packs_dir.glob("statute_pack_*.jsonl"):
        pack_rules: list[CanonicalRuleArtifact] = []
        with pack_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    data["layer"] = "domain"
                    data["review_notes"] = (
                        f"Aggregated from statute pack {pack_file.name}. "
                        + (data.get("review_notes") or "")
                    ).strip()
                    rule = CanonicalRuleArtifact(**data)
                    pack_rules.append(rule)
        
        pack_key = pack_file.stem.replace("statute_pack_", "")
        pack_summaries[pack_key] = {
            "rule_count": len(pack_rules),
            "source_file": str(pack_file),
        }
        all_rules.extend(pack_rules)
    
    # Write domain rulebase
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for rule in all_rules:
            f.write(rule.model_dump_json(ensure_ascii=False) + "\n")
    
    summary = {
        "domain": domain,
        "total_rules": len(all_rules),
        "pack_summaries": pack_summaries,
        "output_path": str(output_path),
    }
    
    logger.info(f"Derived domain rulebase {domain}: {len(all_rules)} rules from {len(pack_summaries)} packs")
    return summary