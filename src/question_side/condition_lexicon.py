"""Canonical condition predicates — Python lexicon (does not modify rulebase JSON).

Rulebase alignment: ``canonical_predicate`` values follow Vietnamese snake_case where
possible, consistent with ``law_side.predicate_normalizer.normalize_surface_to_predicate``.
Legacy English identifiers are kept only where noted for backward compatibility.

Manual sync: there is no automatic import from ``predicate_lexicon.xlsx``; when the
law-side lexicon grows, extend ENTRIES with matching ``trigger_patterns`` / synonyms.
"""

from __future__ import annotations

from typing import Any, TypedDict


class PredicateEntry(TypedDict, total=False):
    trigger_patterns: list[str]
    canonical_predicate: str
    arg_schema: list[str]
    domain: str
    notes: str
    synonyms: list[str]
    priority: int
    examples: list[str]
    generic: bool
    """If True, this is a broad context cue (e.g. shareholder); loses to specific matches."""


# Higher priority breaks ties when scores are close (more specific enterprise events).
DEFAULT_PRIORITY = 5

ENTRIES: list[PredicateEntry] = [
    # --- Đăng ký / thay đổi nội dung (aligned with dang_ky_thay_doi_* in predicate_normalizer)
    {
        "trigger_patterns": [
            "đổi người đại diện theo pháp luật",
            "thay đổi người đại diện theo pháp luật",
            "doi nguoi dai dien theo phap luat",
            "thay doi nguoi dai dien",
        ],
        "synonyms": ["bổ nhiệm lại người đại diện pháp luật", "thay người đại diện pháp luật"],
        "canonical_predicate": "thay_doi_nguoi_dai_dien_theo_phap_luat",
        "arg_schema": ["subject"],
        "domain": "enterprise_registration",
        "priority": 22,
        "notes": "Maps near rulebase behaviors around DDPL; legacy name was change_legal_representative.",
    },
    {
        "trigger_patterns": [
            "thay đổi nội dung đăng ký doanh nghiệp",
            "thay doi noi dung dang ky doanh nghiep",
            "đăng ký thay đổi nội dung",
            "dang ky thay doi noi dung",
            "thay đổi nội dung đăng ký",
        ],
        "synonyms": ["điều chỉnh đăng ký kinh doanh", "cập nhật nội dung đăng ký"],
        "canonical_predicate": "dang_ky_thay_doi_noi_dung_dang_ky_doanh_nghiep",
        "arg_schema": ["subject"],
        "domain": "enterprise_registration",
        "priority": 20,
        "notes": "Was change_registered_content; aligned to normalize_surface_to_predicate branch.",
    },
    {
        "trigger_patterns": [
            "thay đổi tên doanh nghiệp",
            "thay doi ten doanh nghiep",
            "đổi tên công ty",
            "doi ten cong ty",
        ],
        "canonical_predicate": "thay_doi_ten_doanh_nghiep",
        "arg_schema": ["subject"],
        "domain": "enterprise_registration",
        "priority": 18,
    },
    {
        "trigger_patterns": [
            "thay đổi địa chỉ trụ sở",
            "thay doi dia chi tru so",
            "đổi địa chỉ trụ sở chính",
        ],
        "canonical_predicate": "thay_doi_dia_chi_tru_so_chinh",
        "arg_schema": ["subject"],
        "domain": "enterprise_registration",
        "priority": 18,
    },
    {
        "trigger_patterns": [
            "thay đổi ngành nghề kinh doanh",
            "thay doi nganh nghe kinh doanh",
            "bổ sung ngành nghề",
        ],
        "canonical_predicate": "thay_doi_nganh_nghe_kinh_doanh",
        "arg_schema": ["subject"],
        "domain": "enterprise_registration",
        "priority": 17,
    },
    {
        "trigger_patterns": [
            "thay đổi vốn điều lệ",
            "thay doi von dieu le",
            "tăng vốn điều lệ",
            "giam von dieu le",
        ],
        "canonical_predicate": "thay_doi_von_dieu_le",
        "arg_schema": ["subject"],
        "domain": "enterprise_registration",
        "priority": 17,
    },
    {
        "trigger_patterns": [
            "thay đổi thành viên",
            "thay doi thanh vien",
            "thay đổi cổ đông",
            "thay doi co dong",
            "thay đổi danh sách cổ đông",
        ],
        "canonical_predicate": "thay_doi_thanh_vien_co_dong",
        "arg_schema": ["subject"],
        "domain": "corporate",
        "priority": 16,
    },
    # --- Thành lập / đăng ký
    {
        "trigger_patterns": ["thành lập doanh nghiệp", "thanh lap doanh nghiep", "thành lập công ty"],
        "canonical_predicate": "thanh_lap_doanh_nghiep",
        "arg_schema": ["subject"],
        "domain": "enterprise_registration",
        "priority": 15,
    },
    {
        "trigger_patterns": [
            "đăng ký doanh nghiệp",
            "dang ky doanh nghiep",
            "đăng ký thành lập",
        ],
        "synonyms": ["đăng ký lần đầu"],
        "canonical_predicate": "dang_ky_doanh_nghiep",
        "arg_schema": ["subject"],
        "domain": "enterprise_registration",
        "priority": 14,
    },
    {
        "trigger_patterns": ["đăng ký hộ kinh doanh", "dang ky ho kinh doanh", "đăng ký hkd"],
        "canonical_predicate": "dang_ky_ho_kinh_doanh",
        "arg_schema": ["subject"],
        "domain": "registration",
        "priority": 14,
    },
    {
        "trigger_patterns": ["góp vốn khi thành lập", "gop von khi thanh lap", "góp vốn thành lập"],
        "canonical_predicate": "gop_von_thanh_lap",
        "arg_schema": ["subject"],
        "domain": "corporate",
        "priority": 13,
    },
    {
        "trigger_patterns": [
            "đăng ký mua cổ phần",
            "dang ky mua co phan",
            "chào bán cổ phần",
        ],
        "canonical_predicate": "dang_ky_mua_co_phan",
        "arg_schema": ["subject"],
        "domain": "corporate",
        "priority": 12,
    },
    # --- Tạm ngừng / giải thể / chấm dứt
    {
        "trigger_patterns": ["tạm ngừng kinh doanh", "tam ngung kinh doanh", "tạm ngừng hoạt động"],
        "canonical_predicate": "tam_ngung_kinh_doanh",
        "arg_schema": ["subject"],
        "domain": "enterprise_registration",
        "priority": 16,
    },
    {
        "trigger_patterns": [
            "tiếp tục kinh doanh trước thời hạn",
            "tiep tuc kinh doanh truoc thoi han",
        ],
        "canonical_predicate": "tiep_tuc_kinh_doanh_truoc_thoi_han",
        "arg_schema": ["subject"],
        "domain": "enterprise_registration",
        "priority": 14,
    },
    {
        "trigger_patterns": ["giải thể doanh nghiệp", "giai the doanh nghiep", "giải thể công ty"],
        "synonyms": ["quyết định giải thể"],
        "canonical_predicate": "giai_the_doanh_nghiep",
        "arg_schema": ["subject"],
        "domain": "enterprise_registration",
        "priority": 16,
    },
    {
        "trigger_patterns": [
            "chấm dứt hoạt động chi nhánh",
            "cham dut hoat dong chi nhanh",
            "chấm dứt văn phòng đại diện",
            "chấm dứt địa điểm kinh doanh",
        ],
        "canonical_predicate": "cham_dut_chi_nhanh_vpp_ddkd",
        "arg_schema": ["subject"],
        "domain": "enterprise_registration",
        "priority": 15,
    },
    # --- Quản trị / nội bộ
    {
        "trigger_patterns": [
            "họp hội đồng thành viên",
            "hop hoi dong thanh vien",
            "hội đồng thành viên",
        ],
        "canonical_predicate": "hop_hoi_dong_thanh_vien",
        "arg_schema": ["subject"],
        "domain": "corporate_governance",
        "priority": 12,
    },
    {
        "trigger_patterns": [
            "họp đại hội đồng cổ đông",
            "hop dai hoi dong co dong",
            "đại hội đồng cổ đông",
        ],
        "canonical_predicate": "hop_dai_hoi_dong_co_dong",
        "arg_schema": ["subject"],
        "domain": "corporate_governance",
        "priority": 12,
    },
    {
        "trigger_patterns": [
            "lấy ý kiến bằng văn bản",
            "lay y kien bang van ban",
            "lấy ý kiến các thành viên bằng văn bản",
        ],
        "canonical_predicate": "lay_y_kien_bang_van_ban",
        "arg_schema": ["subject"],
        "domain": "corporate_governance",
        "priority": 13,
    },
    {
        "trigger_patterns": [
            "chuyển nhượng phần vốn góp",
            "chuyen nhuong phan von gop",
            "chuyển nhượng cổ phần",
        ],
        "canonical_predicate": "chuyen_nhuong_von_gop_co_phan",
        "arg_schema": ["subject"],
        "domain": "corporate",
        "priority": 14,
    },
    # --- Hồ sơ / thủ tục / thời hạn / ngoại lệ
    {
        "trigger_patterns": ["nộp hồ sơ", "nop ho so", "gửi hồ sơ", "gui ho so"],
        "synonyms": ["hồ sơ đăng ký"],
        "canonical_predicate": "nop_ho_so",
        "arg_schema": ["subject"],
        "domain": "procedure",
        "priority": 11,
    },
    {
        "trigger_patterns": [
            "thông báo thay đổi",
            "thong bao thay doi",
            "thông báo về việc",
        ],
        "canonical_predicate": "thong_bao_thay_doi",
        "arg_schema": ["subject"],
        "domain": "procedure",
        "priority": 11,
    },
    {
        "trigger_patterns": [
            "đăng ký thay đổi trong thời hạn",
            "dang ky thay doi trong thoi han",
            "trong thời hạn quy định",
        ],
        "canonical_predicate": "dang_ky_thay_doi_trong_thoi_han",
        "arg_schema": ["subject"],
        "domain": "procedure",
        "priority": 12,
    },
    {
        "trigger_patterns": ["quá thời hạn", "qua thoi han", "hết thời hạn", "het thoi han"],
        "canonical_predicate": "qua_thoi_han",
        "arg_schema": ["subject"],
        "domain": "deadline",
        "priority": 10,
    },
    {
        "trigger_patterns": ["trong thời hạn", "trong thoi han", "đúng hạn"],
        "canonical_predicate": "trong_thoi_han",
        "arg_schema": ["subject"],
        "domain": "deadline",
        "priority": 9,
        "generic": True,
    },
    {
        "trigger_patterns": ["ngoại lệ", "ngoai le", "trừ trường hợp", "tru truong hop"],
        "canonical_predicate": "truong_hop_ngoai_le",
        "arg_schema": ["subject"],
        "domain": "exception",
        "priority": 10,
    },
    {
        "trigger_patterns": ["thủ tục đăng ký", "thu tuc dang ky", "trình tự thủ tục"],
        "canonical_predicate": "thu_tuc_dang_ky",
        "arg_schema": ["subject"],
        "domain": "procedure",
        "priority": 10,
    },
    {
        "trigger_patterns": [
            "tài liệu phải nộp",
            "tai lieu phai nop",
            "hồ sơ cần có",
            "ho so can co",
            "giấy tờ kèm theo",
        ],
        "canonical_predicate": "tai_lieu_ho_so_bat_buoc",
        "arg_schema": ["subject"],
        "domain": "procedure",
        "priority": 12,
    },
    {
        "trigger_patterns": [
            "xử phạt hành chính",
            "xu phat hanh chinh",
            "bị phạt tiền",
            "bi phat tien",
            "chịu xử phạt",
        ],
        "canonical_predicate": "xu_phat_hanh_chinh",
        "arg_schema": ["subject"],
        "domain": "legal_effect",
        "priority": 11,
    },
    {
        "trigger_patterns": ["từ chối hồ sơ", "tu choi ho so", "bị từ chối đăng ký"],
        "canonical_predicate": "tu_choi_ho_so",
        "arg_schema": ["subject"],
        "domain": "procedure",
        "priority": 11,
    },
    {
        "trigger_patterns": ["phát sinh nghĩa vụ", "phat sinh nghia vu", "nghĩa vụ pháp lý phát sinh"],
        "canonical_predicate": "phat_sinh_nghia_vu",
        "arg_schema": ["subject"],
        "domain": "legal_effect",
        "priority": 9,
    },
    # --- Generic context (low tie-break priority; specific entries should win)
    {
        "trigger_patterns": ["cổ đông", "co dong", "góp vốn", "gop von", "tỷ lệ vốn", "co phan"],
        "canonical_predicate": "shareholder_context",
        "arg_schema": ["subject"],
        "domain": "corporate",
        "priority": 3,
        "generic": True,
        "notes": "Broad cue; prefer thay_doi_thanh_vien_co_dong or chuyen_nhuong_* when matched.",
    },
    {
        "trigger_patterns": ["hộ kinh doanh", "ho kinh doanh"],
        "canonical_predicate": "business_household_context",
        "arg_schema": ["subject"],
        "domain": "registration",
        "priority": 4,
        "generic": True,
    },
    {
        "trigger_patterns": ["cơ quan đăng ký", "co quan dang ky", "sở kế hoạch", "so ke hoach"],
        "canonical_predicate": "authority_registration_body",
        "arg_schema": [],
        "domain": "authority",
        "priority": 8,
    },
]


def all_canonical_predicates() -> list[str]:
    return sorted({e["canonical_predicate"] for e in ENTRIES})


def entry_by_predicate(name: str) -> PredicateEntry | None:
    for e in ENTRIES:
        if e.get("canonical_predicate") == name:
            return e
    return None


def iter_entries_for_tests() -> list[PredicateEntry]:
    """Stable copy for unit tests."""
    return list(ENTRIES)
