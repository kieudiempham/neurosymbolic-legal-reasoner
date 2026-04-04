"""Lexicon matching: synonyms, specificity vs generic, fallback, near-tie alternatives."""

from __future__ import annotations

from question_side.condition_lexicon import ENTRIES
from question_side.condition_normalizer import normalize_condition_text


def test_synonyms_map_same_canonical_family() -> None:
    """Two paraphrases of DDPL hit the same predicate."""
    r1 = normalize_condition_text(
        "thay đổi người đại diện theo pháp luật",
        actor_entity_id="e1",
        actor_role="company",
        assertion_status="hypothetical",
    )
    r2 = normalize_condition_text(
        "đổi người đại diện theo pháp luật",
        actor_entity_id="e1",
        actor_role="company",
        assertion_status="hypothetical",
    )
    assert r1.canonical_predicate == r2.canonical_predicate == "thay_doi_nguoi_dai_dien_theo_phap_luat"
    assert r1.confidence >= 0.5


def test_specific_beats_shareholder_context() -> None:
    """Member change is more specific than generic shareholder_context."""
    r = normalize_condition_text(
        "thay đổi thành viên góp vốn và danh sách cổ đông",
        actor_entity_id="e1",
        actor_role="company",
        assertion_status="hypothetical",
    )
    assert r.canonical_predicate == "thay_doi_thanh_vien_co_dong"
    assert "shareholder_context" not in r.primary_atom


def test_low_confidence_falls_back_to_stated_condition() -> None:
    r = normalize_condition_text(
        "điều kiện pháp lý trừu tượng không có trong lexicon",
        actor_entity_id="e1",
        actor_role="company",
        assertion_status="hypothetical",
    )
    assert r.canonical_predicate == "stated_condition"
    assert "stated_condition(" in r.primary_atom
    assert r.confidence < 0.5


def test_close_scores_can_surface_alternatives() -> None:
    """Two overlapping patterns may yield low gap and alternatives (when both score)."""
    r = normalize_condition_text(
        "thông báo thay đổi nội dung đăng ký doanh nghiệp và góp vốn",
        actor_entity_id="e1",
        actor_role="company",
        assertion_status="hypothetical",
    )
    assert r.primary_atom
    # Either high-confidence primary or ambiguity_reason when alternatives exist
    assert r.confidence > 0.35


def test_lexicon_entries_have_required_metadata() -> None:
    for e in ENTRIES:
        assert e.get("canonical_predicate")
        assert e.get("trigger_patterns")
        assert e.get("domain")
