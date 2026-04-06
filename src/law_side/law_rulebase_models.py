"""Internal dataclasses for rule-base first-pass generation.

These models are intentionally aligned with the *Excel review schemas*
requested in the paper pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class LegalDocument:
    """A legal document with raw + cleaned text."""

    doc_id: str
    doc_code: str
    doc_title: str
    doc_type: str
    issuing_body: str
    issue_date: Optional[str]
    effective_date: Optional[str]
    source_file_name: str
    source_format: str
    domain_scope: str = ""
    domain_subscope: str = ""
    document_role: str = ""
    expected_rule_density: str = ""
    parse_strategy: str = ""
    is_consolidated_version: str = ""
    amends_doc_codes: str = ""
    has_appendix_forms: str = ""
    legal_scope_note: str = ""
    priority: str = ""
    status: str = "seed_first_pass"
    notes: str = ""

    raw_text: str = ""
    cleaned_text: str = ""


@dataclass(slots=True)
class LegalUnit:
    """A structural/legal unit extracted from legal text."""

    unit_id: str
    doc_id: str
    doc_code: str
    chapter: str | None
    section: str | None
    article: str | None
    clause: str | None
    point: str | None
    unit_type: str
    heading: str
    text: str
    parent_context: str
    topic_tag: str | None
    normative_signal: str | None
    is_candidate_rule_sentence: bool
    source_ref: str

    unit_ref_full: str = ""
    sentence_index: int = 1
    subsentence_index: int = 1
    list_item_marker: str | None = None
    deontic_signal: str | None = None
    has_condition_marker: bool = False
    has_deadline_marker: bool = False
    has_document_marker: bool = False
    has_authority_marker: bool = False
    has_exception_marker: bool = False
    has_threshold_marker: bool = False
    has_cross_reference: bool = False
    cross_reference_text: str | None = None
    actor_hint: str | None = None
    action_hint: str | None = None
    object_hint: str | None = None
    rule_density_estimate: str = "thap"
    needs_split: str = "khong"
    split_reason: str | None = None
    notes: str = ""


@dataclass(slots=True)
class NormativeSentence:
    """A candidate sentence/segment that may generate legal frames."""

    ns_id: str
    unit_id: str
    doc_id: str
    source_ref: str
    sentence_text: str
    sentence_type: str
    normative_pattern: str
    subject_span: str | None
    action_span: str | None
    modality_span: str | None
    condition_span: str | None
    time_span: str | None
    document_span: str | None
    authority_span: str | None
    candidate_rule_type: str
    confidence_manual: str

    # Enrichment fields for high-recall rulebase candidate review.
    candidate_id: str = ""
    doc_code: str = ""
    unit_ref_full: str = ""
    source_text: str = ""

    candidate_type: str = ""
    candidate_subtype: str = ""
    candidate_score: str = ""
    trigger_patterns: str = ""

    actor_text: str | None = None
    action_text: str | None = None
    object_text: str | None = None
    condition_text: str | None = None
    deadline_text: str | None = None
    authority_text: str | None = None
    document_text: str | None = None
    exception_text: str | None = None
    threshold_text: str | None = None
    legal_effect_text: str | None = None

    should_extract_rule: str = ""
    extraction_priority: str = ""
    notes: str = ""

    # Context fields (semantic verification in review).
    heading: str = ""
    parent_context: str = ""


@dataclass(slots=True)
class LegalFrame:
    """Extracted legal frame used to construct atomic rules."""

    frame_id: str
    ns_id: str
    candidate_id: str | None
    source_unit_id: str | None
    doc_id: str
    doc_code: str | None
    unit_ref_full: str | None
    source_ref: str
    source_text: str | None
    frame_type: str
    subject_type: str
    subject_role: str
    trigger_event: str | None
    condition_predicates: str | None
    action_predicate: str | None
    modality: str
    deadline_value: str | None
    deadline_unit: str | None
    deadline_anchor: str | None
    required_documents: str | None
    recipient_authority: str | None
    legal_effect: str | None
    exception_text: str | None
    output_status: str

    # Enriched legal-frame slots (grounded-first).
    chu_the: str | None = None
    vai_tro_chu_the: str | None = None
    hanh_vi: str | None = None
    doi_tuong_hanh_vi: str | None = None
    tinh_chat_phap_ly: str | None = None
    dieu_kien_ap_dung: str | None = None
    dieu_kien_dinh_luong: str | None = None
    nguong_so_luong: str | None = None
    nguong_ty_le: str | None = None
    khoang_gia_tri: str | None = None
    thanh_phan_ho_so: str | None = None
    co_quan_tiep_nhan: str | None = None
    co_quan_xu_ly: str | None = None
    ket_qua_thu_tuc: str | None = None
    thoi_han_so: str | None = None
    don_vi_thoi_han: str | None = None
    moc_tinh_thoi_han: str | None = None
    ngoai_le: str | None = None
    van_ban_dan_chieu: str | None = None
    ghi_chu_giai_thich: str | None = None
    muc_do_day_du: str | None = None
    can_tach_them: str | None = None
    ly_do_can_tach: str | None = None
    heading: str = ""
    parent_context: str = ""
    notes: str = ""
    generic_frame: dict[str, Any] | None = None


@dataclass(slots=True)
class PredicateLexiconEntry:
    """One normalized predicate entry for traceable predicate normalization."""

    predicate_id: str
    surface_form: str
    bien_the_ngon_ngu: str
    hanh_vi_chuan: str
    hanh_vi_chuan_chi_tiet: str
    nhom_hanh_vi: str
    chu_the_mac_dinh: str | None
    doi_tuong_mac_dinh: str | None
    co_quan_mac_dinh: str | None
    can_thoi_han: str
    can_ho_so: str
    can_ngoai_le: str
    can_nguong_dinh_luong: str
    ghi_chu_ap_dung: str

    # Backward-compatible fields used by downstream code.
    normalized_predicate: str
    predicate_group: str
    frame_role: str
    modality_hint: str | None
    object_hint: str | None
    source_doc_id: str
    source_ref: str
    example_text: str | None
    status: str
    notes: str = ""


@dataclass(slots=True)
class RuleSeed:
    """One atomic rule seed produced from a legal frame."""

    # A. Nhóm nhận diện
    rule_id: str
    rule_group_id: str
    frame_id: str
    candidate_id: str
    source_unit_id: str
    doc_id: str
    doc_code: str

    # B. Nhóm truy vết nguồn
    source_ref: str
    source_ref_full: str
    heading: str
    parent_context: str
    source_text: str

    # C. Nhóm phân loại rule
    rule_type: str
    tinh_chat_phap_ly: str
    canonical_predicate: str
    typed_predicate: str
    predicate_family: str

    # D. Nhóm nội dung pháp lý cốt lõi
    chu_the: str
    loai_chu_the: str
    vai_tro_chu_the: str
    dieu_kien_ap_dung: str
    bieu_thuc_dieu_kien: str
    hanh_vi_phap_ly: str
    doi_tuong_hanh_vi: str
    he_qua_phap_ly: str

    # E. Nhóm định lượng / ngưỡng
    ten_chi_so: str
    toan_tu_so_sanh: str
    gia_tri_nguong: str
    don_vi_nguong: str
    gia_tri_tu: str
    gia_tri_den: str
    kieu_khoang: str

    # F. Nhóm thời hạn
    thoi_han_so: str
    don_vi_thoi_han: str
    moc_tinh_thoi_han: str
    bieu_thuc_thoi_han: str

    # G. Nhóm thủ tục / hồ sơ / cơ quan
    thanh_phan_ho_so: str
    co_quan_tiep_nhan: str
    co_quan_xu_ly: str
    ket_qua_thu_tuc: str
    phuong_thuc_thuc_hien: str

    # H. Nhóm ngoại lệ / phạm vi
    pham_vi_ap_dung: str
    ngoai_le: str
    van_ban_dan_chieu: str

    # I. Nhóm phục vụ answer / explanation
    answer_template: str
    explanation_template: str
    grounded_summary: str

    # J. Nhóm chất lượng
    muc_do_day_du: str
    do_tin_cay_trich_xuat: str
    can_ra_soat: str
    ly_do_can_ra_soat: str
    extraction_pattern: str
    notes: str = ""

