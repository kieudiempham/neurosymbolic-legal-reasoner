"""Canonical rule artifact: source of truth for parser output → backend runtime compilation.

Purpose:
- Single, transparent intermediate between parser (Stage 5) and backend runtime artifact
- Sufficient metadata for multi-rule support (domain, layer, provenance)
- Reviewable (can export to Excel) and compilable (can generate rulebase_reasoning_core.json)
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CanonicalRuleArtifact(BaseModel):
    """One rule as emitted by parser, ready for backend compilation or review.
    
    This is the canonical intermediate representation that bridges:
    - Parser Stage 5 RuleBuilder
    - Review Excel exports
    - Backend runtime rulebase_reasoning_core.json compilation
    
    Fields are grouped by purpose:
    A. Identity & Provenance for multi-rule traceability
    B. Content & Logic for backend reasoning
    C. Enrichment for human review & explanation
    D. Metadata for domain/layer classification
    """

    # A. Identity & Provenance
    rule_id: str = Field(description="Unique rule identifier within rulebase_id")
    domain: str = Field(description="Domain scope (e.g., enterprise, labor, tax)")
    layer: str = Field(default="statute", description="Layer: statute/domain/shared")
    rulebase_id: str = Field(description="Rulebase package identifier")
    
    # B. Source Lineage
    source_doc: str = Field(description="Document identifier/code")
    source_article: str | None = Field(default=None, description="Article number/reference")
    source_clause: str | None = Field(default=None, description="Clause number (Khoản)")
    source_point: str | None = Field(default=None, description="Point marker (Điểm)")
    source_unit_id: str | None = Field(default=None, description="Source legal unit ID from parser")
    source_ref: str = Field(description="Short source reference (e.g., DOC_ID:Điều 10)")
    source_ref_full: str = Field(description="Full source path with context")
    surface_text: str = Field(description="Original Vietnamese text from source")
    
    # C. Rule Content - Logic Layer
    logic_form: str = Field(
        description="canonical logic form: obligation|permission|prohibition|deadline|threshold|"
        "exception|applicability_condition|authority_action|legal_effect|dossier"
    )
    canonical_head: dict[str, Any] = Field(
        default_factory=dict,
        description="Head predicate {predicate: str, args: list}"
    )
    canonical_body: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Body conditions [{predicate: str, args: list, ...}, ...]"
    )
    
    # D. Enrichment for Review & Explanation
    verbalized_vi: str | None = Field(default=None, description="Vietnamese verbalization for explanation")
    explanation_template: str | None = Field(default=None, description="Template for generating explanations")
    predicate_candidates: dict[str, str] = Field(
        default_factory=dict,
        description="Surface form → normalized predicate mapping for audit"
    )
    
    # E. Document Metadata
    doc_type: str = Field(default="", description="law|decree|regulation|decision|etc")
    doc_code: str = Field(default="", description="Official document code (e.g., 67/VBHN-VPQH)")
    issuing_body: str = Field(default="", description="Issuing authority")
    
    # F. Temporal Metadata (placeholder for future temporal policies)
    effective_from: str | None = Field(default=None, description="Effective date (ISO 8601)")
    effective_to: str | None = Field(default=None, description="Expiration date if any")
    
    # G. Review & Status
    review_status: str = Field(default="seed", description="seed|verified|core|archived")
    review_notes: str = Field(default="", description="Reviewer notes or quality flags")
    confidence_score: float | None = Field(default=None, description="Parser confidence (0-1)")
    
    # H. Provenance & Lineage
    generated_from_frame_id: str | None = Field(default=None, description="Source legal frame ID")
    generated_from_normative_sentence_id: str | None = Field(default=None, description="Source normative sentence ID")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "rule_id": "ENT_REG_001",
                "domain": "enterprise",
                "layer": "statute",
                "rulebase_id": "luật_doanh_nghiệp_67",
                "source_doc": "DOC_LUAT_DOANH_NGHIEP_67",
                "source_article": "10",
                "source_clause": "1",
                "source_point": None,
                "source_ref": "Luật DN, Điều 10, Khoản 1",
                "source_ref_full": "Luật Doanh Nghiệp 67/VBHN-VPQH, Điều 10 Khoản 1",
                "surface_text": "Doanh nghiệp phải đăng ký thay đổi nội dung đăng ký trong 15 ngày",
                "logic_form": "obligation",
                "canonical_head": {"predicate": "dang_ky_thay_doi", "args": ["X"]},
                "canonical_body": [
                    {"predicate": "la_doanh_nghiep", "args": ["X"]},
                    {"predicate": "co_chang_doi_noi_dung", "args": ["X"]},
                ],
                "verbalized_vi": "Nếu doanh nghiệp X có thay đổi nội dung đăng ký, X phải đăng ký thay đổi trong 15 ngày",
                "domain": "enterprise",
                "layer": "statute",
                "rulebase_id": "luật_doanh_nghiệp",
                "doc_type": "law",
                "doc_code": "67/VBHN-VPQH",
                "issuing_body": "Văn phòng Quốc hội",
                "review_status": "seed",
            }
        }
