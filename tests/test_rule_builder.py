"""Unit tests for law-side rule seed building."""

from __future__ import annotations

from law_side.law_rulebase_models import LegalFrame
from law_side.predicate_normalizer import normalize_surface_to_predicate
from law_side.rule_builder import RuleBuilder


def test_rule_builder_builds_rule_seeds() -> None:
    frame = LegalFrame(
        frame_id="f1",
        ns_id="ns1",
        candidate_id="c1",
        source_unit_id="u1",
        doc_id="d1",
        doc_code="DOC",
        unit_ref_full="Điều 1",
        source_ref="unit=1",
        source_text="Người nộp hồ sơ phải nộp ...",
        frame_type="khung_nghia_vu",
        subject_type="organization",
        subject_role="obligor",
        trigger_event="nộp hồ sơ",
        condition_predicates=None,
        action_predicate="nộp hồ sơ",
        modality="obligation",
        deadline_value=None,
        deadline_unit=None,
        deadline_anchor=None,
        required_documents=None,
        recipient_authority=None,
        legal_effect="must",
        exception_text=None,
        output_status="seed_extracted_first_pass",
        notes="",
    )

    b = RuleBuilder(config={})
    seeds = b.build([frame], action_surface_to_normalized={})
    assert len(seeds) >= 1
    assert seeds[0].frame_id == "f1"
    assert seeds[0].hanh_vi_phap_ly == "nộp hồ sơ"
    assert seeds[0].canonical_predicate == normalize_surface_to_predicate("nộp hồ sơ")
