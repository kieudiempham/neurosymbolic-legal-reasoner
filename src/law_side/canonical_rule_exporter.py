"""Export canonical rule artifacts from parsed legal frames.

Pipeline Stage 5 enhancement:
- Regular RuleSeed → Excel for review (existing)
- NEW: RuleSeed → CanonicalRuleArtifact → JSONL for backend compilation
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from law_side.law_rulebase_models import RuleSeed
from schemas.canonical_rule import CanonicalRuleArtifact
from utils.logger import get_logger

logger = get_logger(__name__)


def rule_seed_to_canonical(
    seed: RuleSeed,
    domain: str = "enterprise",
    rulebase_id: str = "",
) -> CanonicalRuleArtifact:
    """Convert RuleSeed to CanonicalRuleArtifact.
    
    Args:
        seed: RuleSeed from pipeline
        domain: Domain scope (enterprise, labor, tax)
        rulebase_id: Rulebase package ID (e.g., luật_doanh_nghiệp)
    
    Returns:
        CanonicalRuleArtifact ready for storage and compilation
    """
    # Extract source components
    source_article = seed.source_ref.split(",")[0].strip() if seed.source_ref else ""
    source_clause = seed.source_ref.split(",")[1].strip() if "," in seed.source_ref else ""
    
    # Map rule type to logic form
    logic_form = _rule_type_to_logic_form(seed.rule_type, seed.tinh_chat_phap_ly)
    
    # Build canonical head/body from predicate info
    canonical_head = {
        "predicate": seed.canonical_predicate,
        "args": ["X"],  # Primary argument
    }
    
    canonical_body: list[dict[str, Any]] = []
    # Condition predicates if present
    if seed.dieu_kien_ap_dung and seed.dieu_kien_ap_dung.lower() not in ("", "n/a", "không"):
        canonical_body.append({
            "predicate": "condition",
            "text": seed.dieu_kien_ap_dung,
        })
    
    # Default rulebase_id from document if not provided
    if not rulebase_id:
        source_code = (seed.doc_code or "").lower().replace("/", "_").replace(" ", "_")
        rulebase_id = f"{domain}_{source_code}" if source_code else f"{domain}_rulebase"

    # Create artifact
    artifact = CanonicalRuleArtifact(
        rule_id=seed.rule_id,
        domain=domain,
        layer="statute",  # Phase 1 only statute layer
        rulebase_id=rulebase_id,
        
        # Source lineage
        source_doc=seed.doc_code,
        source_article=source_article or None,
        source_clause=source_clause or None,
        source_point=None,
        source_unit_id=seed.source_unit_id,
        source_ref=seed.source_ref,
        source_ref_full=seed.source_ref_full,
        surface_text=seed.surface_text,
        
        # Logic content
        logic_form=logic_form,
        canonical_head=canonical_head,
        canonical_body=canonical_body,
        
        # Enrichment
        verbalized_vi=seed.explanation_template or seed.grounded_summary,
        explanation_template=seed.answer_template,
        predicate_candidates={
            "surface": seed.hanh_vi_phap_ly,
            "normalized": seed.canonical_predicate,
            "family": seed.predicate_family,
        },
        
        # Document metadata
        doc_type="law",  # Will be configured per domain
        doc_code=seed.doc_code,
        issuing_body="",  # Will be filled from document metadata
        
        # Status
        review_status="seed",
        review_notes=seed.ghi_chu_giai_thich or "",
        confidence_score=None,
        
        # Provenance
        generated_from_frame_id=seed.frame_id,
    )
    
    return artifact


def _rule_type_to_logic_form(rule_type: str, tinh_chat: str) -> str:
    """Map RuleSeed rule_type/tinh_chat to canonical logic_form."""
    rule_type_lower = (rule_type or "").lower()
    tinh_chat_lower = (tinh_chat or "").lower()
    
    # Direct mappings
    if "obligation" in rule_type_lower or "nghia_vu" in tinh_chat_lower:
        return "obligation"
    if "permission" in rule_type_lower or "quyen" in tinh_chat_lower:
        return "permission"
    if "prohibition" in rule_type_lower or "cam" in tinh_chat_lower:
        return "prohibition"
    if "deadline" in rule_type_lower or "thoi_han" in tinh_chat_lower:
        return "deadline"
    if "threshold" in rule_type_lower or "nguong" in tinh_chat_lower:
        return "threshold"
    if "exception" in rule_type_lower or "ngoai_le" in tinh_chat_lower:
        return "exception"
    if "condition" in rule_type_lower or "dieu_kien" in tinh_chat_lower:
        return "applicability_condition"
    if "authority" in rule_type_lower or "hanh_dong_co_quan" in tinh_chat_lower:
        return "authority_action"
    if "effect" in rule_type_lower or "ket_qua" in tinh_chat_lower:
        return "legal_effect"
    if "document" in rule_type_lower or "ho_so" in tinh_chat_lower:
        return "dossier"
    
    # Fallback
    return "obligation"  # Most rules are obligations in enterprise law


def export_canonical_rules_jsonl(
    rule_seeds: list[RuleSeed],
    output_path: Path,
    doc_id: str,
    domain: str = "enterprise",
    rulebase_id: str = "",
) -> int:
    """Export rule seeds as canonical JSONL.
    
    Args:
        rule_seeds: List of RuleSeed objects from pipeline
        output_path: Output JSONL file path
        doc_id: Document identifier
        domain: Domain scope
        rulebase_id: Rulebase package ID
    
    Returns:
        Number of rules exported
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    count = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for seed in rule_seeds:
            artifact = rule_seed_to_canonical(seed, doc_id, domain, rulebase_id)
            f.write(artifact.model_dump_json(ensure_ascii=False) + "\n")
            count += 1
    
    logger.info(f"Exported {count} canonical rules to {output_path}")
    return count
