"""
Logic intermediate representation (sạch) cho rulebase_logic.json — không đụng Excel.

Tách khỏi ProbLog: chỉ cấu trúc head/body/aux/metadata + logic_readiness / canonical_status.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pandas as pd

from law_side.controlled_vocabulary_builder import to_snake_id
from law_side.refine_controlled_vocabulary import split_effect_exception_condition
from law_side.rulebase_vocab_index import NormalizedVocab

RULE_TYPE_TO_LOGIC_FORM: dict[str, str] = {
    "quy_tac_nghia_vu": "obligation",
    "quy_tac_quyen": "permission",
    "quy_tac_cam_doan": "prohibition",
    "quy_tac_thoi_han": "deadline",
    "quy_tac_ho_so": "dossier",
    "quy_tac_hanh_dong_co_quan": "authority_action",
    "quy_tac_ngoai_le": "exception",
    "quy_tac_nguong_dinh_luong": "threshold",
    "quy_tac_ket_qua_phap_ly": "legal_effect",
    "quy_tac_dieu_kien": "applicability_condition",
    "quy_tac_thu_tuc": "procedure_step",
}


def _cell(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    if isinstance(v, str):
        s = v.strip()
        return s if s else None
    return v


def _numish(v: Any) -> Any:
    v = _cell(v)
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return v
    s = str(v).strip().replace(",", ".")
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        return v


def _split_dossier_items(text: str | None) -> list[str]:
    if not text:
        return []
    parts = re.split(r"[;；]\s*", str(text))
    return [p.strip() for p in parts if p.strip()]


_DOSSIER_CUE_MARKERS = (
    "ho_so_gom",
    "bao_gom",
    "thanh_phan_ho_so",
    "giay_to_sau_day",
    "quy_dinh_tai",
    "truong_hop",
    "doi_voi",
)


def _clean_dossier_items(text: str | None) -> list[str]:
    raw_items = _split_dossier_items(text)
    out: list[str] = []
    for it in raw_items:
        slug = _short_anchor_slug(it, max_len=80)
        # Bỏ cue phrase quá procedural, giữ các item có dạng noun legal ổn định.
        if any(m in slug for m in _DOSSIER_CUE_MARKERS):
            continue
        if len(slug) < 4:
            continue
        out.append(slug)
    return out

GENERIC_PREDICATE_SLUGS = frozenset(
    {
        "dang_ky",
        "thong_bao",
        "xem_xet",
        "cap_nhat",
        "nop_ho_so",
        "chuan_bi_ho_so",
    }
)

_PLACEHOLDER_HANH_VI = frozenset(
    {
        "chuẩn bị hồ sơ",
        "chuan_bi_ho_so",
        "nộp hồ sơ",
        "nop_ho_so",
    }
)

_EFFECT_TRUNC_MARKERS: tuple[str, ...] = (
    # Các cụm thường đi kèm ngoại lệ / điều kiện trong slug đã snake_case
    "_tru_truong_hop",
    "tru_truong_hop",
    "_ngoai_tru_",
    "_neu_",
    "_neu_co_",
    "_khi_",
    "_doi_voi_",
    "doi_voi_",
    "_trong_thoi_han_",
    "_theo_",
    "_co_quan_",
    "_gui_",
    "_trao_",
    "_ra_quyet_dinh",
    "_thong_bao",
    "_cong_bo",
    "_tuy_nhien_",
    "ngoai_le",
    "trong_truong_hop",
    "_khoang_",
)


def _truncate_slug_before_markers(slug: str, markers: tuple[str, ...]) -> str:
    s = str(slug).strip()
    if not s:
        return s
    best_idx: int | None = None
    for m in markers:
        idx = s.find(m)
        if idx == -1:
            continue
        if best_idx is None or idx < best_idx:
            best_idx = idx
    if best_idx is None:
        return s
    base = s[:best_idx].rstrip("_")
    return base if len(base) >= 6 else s


def _short_anchor_slug(text: str | None, max_len: int = 80) -> str:
    if not text:
        return "anchor_unresolved"
    t = str(text).strip()
    if len(t) > max_len:
        t = t[: max_len - 1]
    s = to_snake_id(t)
    return s if s else "anchor_unresolved"


def _short_anchor_text(text: str | None, max_len: int = 80) -> str:
    if not text:
        return "anchor_unresolved"
    t = str(text).strip()
    if len(t) > max_len:
        t = t[: max_len - 1]
    return t


def _extract_deadline_value_unit_from_text(row: pd.Series) -> tuple[Any, str | None]:
    """
    Khi Excel thiếu `thoi_han_so`/`don_vi_thoi_han`, cố trích từ `source_text`/`grounded_summary`.
    Trả về (value, unit_slug_or_none).
    """
    # Try multiple fields because some rows miss `thoi_han_so`/`don_vi_thoi_han` in Excel.
    text = (
        _cell(row.get("grounded_summary"))
        or _cell(row.get("source_text"))
        or _cell(row.get("bieu_thuc_thoi_han"))
        or _cell(row.get("moc_tinh_thoi_han"))
        or _cell(row.get("thoi_han_so"))
    )
    if not text:
        return None, None
    slug = to_snake_id(text).lower()

    unit: str | None = None
    if "ngay_lam_viec" in slug:
        unit = "ngay_lam_viec"
    elif "ngay" in slug:
        unit = "ngay"
    elif "thang" in slug:
        unit = "thang"
    elif "nam" in slug:
        unit = "nam"

    m = re.search(r"(\\d+(?:[\\.,]\\d+)?)", str(text))
    if not m:
        return None, unit
    raw_num = m.group(1).replace(",", ".")
    try:
        val = float(raw_num) if "." in raw_num else int(raw_num)
    except ValueError:
        return None, unit
    return val, unit


def _term_clean(predicate: str, args: list[Any]) -> dict[str, Any]:
    return {"predicate": predicate, "args": args}


def _clean_long_text(s: str | None, max_len: int = 120) -> str | None:
    if not s:
        return None
    t = str(s).strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


def infer_predicate_anchor(
    row: pd.Series, norm: NormalizedVocab
) -> tuple[str | None, str]:
    """(predicate_anchor_slug, canonical_status)."""
    raw_cp = _cell(row.get("canonical_predicate"))
    raw_hv = _cell(row.get("hanh_vi_phap_ly"))
    raw_tp = _cell(row.get("typed_predicate"))
    pf = _cell(row.get("predicate_family"))

    if norm.predicate_canonical:
        pc = norm.predicate_canonical
        if pc in GENERIC_PREDICATE_SLUGS:
            # Nếu quá chung mà typed predicate không có đuôi cụ thể thì hạ xuống family-level.
            if raw_tp and ":" in raw_tp:
                tail = to_snake_id(raw_tp.split(":", 1)[-1].strip())
                if tail and len(tail) > len(pc) + 3:
                    return tail, "inferred_from_context"
            # Tránh placeholder dạng `*_level`: nếu có `hanh_vi_phap_ly` cụ thể hơn thì dùng luôn.
            if raw_hv:
                hv_slug = to_snake_id(raw_hv)
                if hv_slug and hv_slug != pc and len(hv_slug) > len(pc) + 3:
                    return hv_slug, "inferred_from_context"
            return pc, "fallback_family_level"
        return pc, "exact_vocab_match"

    if raw_cp:
        s = to_snake_id(raw_cp)
        if s:
            # Tránh neo vào canonical predicate quá dài; ưu tiên dùng typed đuôi cụ thể hơn.
            if len(s) > 80 and raw_tp and ":" in raw_tp:
                tail = to_snake_id(raw_tp.split(":", 1)[-1].strip())
                if tail:
                    return tail, "inferred_from_context"
            return s, "inferred_from_context"

    if raw_tp and ":" in raw_tp:
        tail = to_snake_id(raw_tp.split(":", 1)[-1].strip())
        if tail:
            return tail, "inferred_from_context"

    if raw_hv:
        s = to_snake_id(raw_hv)
        if s and len(s) >= 8:
            if len(s) > 80 and raw_tp and ":" in raw_tp:
                tail = to_snake_id(raw_tp.split(":", 1)[-1].strip())
                if tail:
                    return tail, "inferred_from_context"
            return s, "inferred_from_context"

    if pf:
        return to_snake_id(pf), "fallback_family_level"

    return None, "unresolved"


def _effect_arg_clean(norm: NormalizedVocab, he_raw: str | None) -> tuple[str | None, str | None]:
    """
    Trả về (effect_canonical_for_head, tail_exception_for_body).
    Không đưa câu dài có 'trừ trường hợp' vào head.
    """
    if norm.effect_canonical:
        s = str(norm.effect_canonical).strip()
        base, frags = split_effect_exception_condition(s)
        if frags:
            return base, frags[0][1] if frags else None
        # Nếu effect canonical vẫn chứa marker ngoại lệ/điều kiện chưa tách,
        # cắt sạch phần đuôi để head không bị dính.
        truncated = _truncate_slug_before_markers(s, _EFFECT_TRUNC_MARKERS)
        if truncated and truncated != s:
            tail = s[len(truncated) :].lstrip("_")
            return truncated, tail if tail else None
        if len(s) > 80:
            # Giữ lại fallback cho trường hợp effect dài nhưng không phát hiện marker cụ thể.
            return _short_anchor_slug(s, max_len=80), None
        return s, None
    if not he_raw:
        return None, None
    slug = to_snake_id(he_raw)
    base, frags = split_effect_exception_condition(slug)
    if frags:
        return base if len(base) >= 8 else None, frags[0][1] if frags else None
    if len(slug) > 80:
        # Trường hợp không tìm thấy marker ngoại lệ nhưng chuỗi dài,
        # vẫn cần tạo được head atom ngắn để tránh fallback `_effect_unresolved`.
        truncated = _truncate_slug_before_markers(slug, _EFFECT_TRUNC_MARKERS)
        if truncated and truncated != slug and len(truncated) >= 6:
            tail = slug[len(truncated) :].lstrip("_")
            return truncated, tail if tail else None
        return _short_anchor_slug(slug, max_len=80), slug
    return slug, None


def _metric_slug(row: pd.Series, norm: NormalizedVocab) -> str | None:
    if norm.metric_canonical:
        return norm.metric_canonical
    t = _cell(row.get("ten_chi_so"))
    if t:
        return to_snake_id(t)
    return None


def _unit_slug(row: pd.Series, norm: NormalizedVocab) -> str | None:
    if norm.unit_canonical:
        return norm.unit_canonical
    u = _cell(row.get("don_vi_nguong")) or _cell(row.get("don_vi_thoi_han"))
    if u:
        u_slug = to_snake_id(u)
        return u_slug if u_slug and u_slug != "unknown" else "unspecified_unit"
    return None


def _op_clean(row: pd.Series) -> str | None:
    o = _cell(row.get("toan_tu_so_sanh"))
    if o:
        s = to_snake_id(o)
        return s if s and s != "unknown" else o
    return None


def should_override_threshold_to_deadline(row: pd.Series) -> bool:
    rt = _cell(row.get("rule_type"))
    if rt != "quy_tac_nguong_dinh_luong":
        return False
    # Chỉ override khi có bằng chứng thời hạn đủ rõ để tránh ép nhầm threshold -> deadline.
    if _cell(row.get("thoi_han_so")) is not None and _cell(row.get("don_vi_thoi_han")):
        return True
    text_blob = " ".join(
        str(x)
        for x in (
            _cell(row.get("bieu_thuc_thoi_han")),
            _cell(row.get("moc_tinh_thoi_han")),
            _cell(row.get("grounded_summary")),
            _cell(row.get("source_text")),
        )
        if x
    )
    if text_blob:
        val, unit = _extract_deadline_value_unit_from_text(row)
        if val is not None and unit:
            return True
    t = _cell(row.get("ten_chi_so"))
    if not t:
        return False
    s = to_snake_id(t)
    # Nếu chỉ thấy metric thời hạn nhưng chưa có value/unit rõ thì KHÔNG ép sang deadline.
    return ("thoi_han" in s or s.startswith("han_")) and False


def should_override_obligation_to_dossier(row: pd.Series) -> bool:
    if _cell(row.get("rule_type")) != "quy_tac_nghia_vu":
        return False
    ho_so = _cell(row.get("thanh_phan_ho_so"))
    if not ho_so or len(ho_so) < 15:
        return False
    hanh = (_cell(row.get("hanh_vi_phap_ly")) or "").lower()
    cp = (_cell(row.get("canonical_predicate")) or "").lower()
    if any(
        x in hanh or x in cp
        for x in ("hồ sơ", "giấy tờ", "thành phần", "tài liệu", "mẫu đơn")
    ):
        return True
    return False


def infer_logic_form(
    row: pd.Series, norm: NormalizedVocab, rule_type: str
) -> tuple[str, list[str]]:
    """(logic_form, override_notes)."""
    notes: list[str] = []
    base = RULE_TYPE_TO_LOGIC_FORM.get(str(rule_type), "generic_rule")

    if should_override_threshold_to_deadline(row):
        notes.append("override_threshold_to_deadline_time_metric")
        return "deadline", notes

    if should_override_obligation_to_dossier(row):
        notes.append("override_obligation_to_dossier_core")
        return "dossier", notes

    # Điều kiện nhưng biểu hiện thực chất là ngoại lệ.
    if base == "applicability_condition":
        dk = _cell(row.get("dieu_kien_ap_dung"))
        nl = _cell(row.get("ngoai_le"))
        if (not dk) and nl:
            notes.append("override_condition_to_exception_when_only_exception_text")
            return "exception", notes

    return base, notes


def build_body_clean(
    row: pd.Series,
    norm: NormalizedVocab,
    logic_form: str,
    *,
    effect_tail_slug: str | None,
    expr_slug_moved_to_metadata: bool,
) -> list[dict[str, Any]]:
    """Chỉ predicate/args có cấu trúc; không dùng raw_text dict."""
    body: list[dict[str, Any]] = []
    dieu_kien = _cell(row.get("dieu_kien_ap_dung"))
    ngoai_le = _cell(row.get("ngoai_le"))
    pham_vi = _cell(row.get("pham_vi_ap_dung"))
    anchor, _cs = infer_predicate_anchor(row, norm)

    # Scope → always symbolic applies_to
    if norm.scope_canonical:
        body.append(_term_clean("applies_to", [norm.scope_canonical]))
    elif pham_vi:
        scope_slug = _short_anchor_slug(pham_vi, max_len=80)
        body.append(_term_clean("applies_to", [scope_slug]))

    redundant_cond = False
    if dieu_kien and ngoai_le:
        dk = dieu_kien.strip().lower()
        nl = ngoai_le.strip().lower()
        if dk and dk in nl:
            redundant_cond = True

    # Điều kiện áp dụng → symbolic condition atom (không để raw text trực tiếp)
    if dieu_kien and not redundant_cond:
        cond_slug = _short_anchor_slug(dieu_kien, max_len=120)
        ctx = anchor or norm.scope_canonical or "condition_context_unresolved"
        body.append(_term_clean("applies_if", [ctx, cond_slug]))

    # Ngoại lệ → symbolic unless/exception_applies với slug
    if ngoai_le and logic_form != "exception":
        exc_slug = _short_anchor_slug(ngoai_le, max_len=120)
        body.append(_term_clean("unless", [exc_slug]))

    if effect_tail_slug:
        body.append(_term_clean("exception_applies", [effect_tail_slug]))

    # Không nhét expression_condition vào body (đã ở metadata)
    if expr_slug_moved_to_metadata:
        pass

    return body


def resolve_logic_readiness(
    canonical_status: str,
    logic_form: str,
    head: dict[str, Any],
    threshold_fallback: bool,
) -> str:
    # Chuẩn hóa đúng 3 tầng: reasoning_ready / reasoning_partial / reasoning_fallback
    args = head.get("args") or []
    hard_null = any(a is None or a == "null" for a in args)
    unresolved_in_args = any(
        isinstance(a, str)
        and (
            a.startswith("unresolved_")
            or a in {"_effect_unresolved", "object_or_result_unresolved", "entity_unresolved"}
        )
        for a in args
    )

    if threshold_fallback:
        return "reasoning_fallback"
    if canonical_status == "unresolved":
        return "reasoning_fallback"
    if logic_form == "generic_rule":
        return "reasoning_fallback"

    # Deadlines thiếu đủ thành phần được coi là fallback.
    if logic_form == "deadline" and head.get("predicate") == "deadline":
        if len(args) >= 4:
            if args[1] is None or args[2] in (None, "") or args[3] in (None, ""):
                return "reasoning_fallback"

    if hard_null or unresolved_in_args:
        return "reasoning_partial"
    if canonical_status == "fallback_family_level":
        return "reasoning_partial"
    return "reasoning_ready"


def build_logic_ir_record(
    row: pd.Series,
    norm: NormalizedVocab,
) -> dict[str, Any]:
    """
    Một rule logic IR sạch: rule_type_source, logic_form, logic_readiness,
    head/body/aux/metadata với canonical_status.
    """
    rule_id = _cell(row.get("rule_id")) or "UNKNOWN"
    rule_type_source = _cell(row.get("rule_type")) or "unknown"

    logic_form, lf_notes = infer_logic_form(row, norm, rule_type_source)

    pred_anchor, canonical_status = infer_predicate_anchor(row, norm)
    chu_raw = _cell(row.get("chu_the"))
    hanh_raw = _cell(row.get("hanh_vi_phap_ly")) or _cell(row.get("canonical_predicate"))
    doi_raw = _cell(row.get("doi_tuong_hanh_vi"))
    he_raw = _cell(row.get("he_qua_phap_ly"))
    kt_raw = _cell(row.get("ket_qua_thu_tuc"))
    dieu_kien = _cell(row.get("dieu_kien_ap_dung"))
    bieu_thuc_dk = _cell(row.get("bieu_thuc_dieu_kien"))
    ngoai_le = _cell(row.get("ngoai_le"))

    subj = norm.subject_canonical or (to_snake_id(chu_raw) if chu_raw else None)
    auth = norm.authority_canonical or to_snake_id(
        _cell(row.get("co_quan_xu_ly")) or _cell(row.get("co_quan_tiep_nhan")) or ""
    )
    if not auth:
        auth = None

    eff_head, eff_tail = _effect_arg_clean(norm, he_raw)
    if not eff_head and kt_raw:
        eff_head, eff_tail = _effect_arg_clean(norm, kt_raw)

    head: dict[str, Any]
    threshold_fallback = False
    fallback_kind: str | None = None
    head_cleanup_notes: list[str] = []
    body_cleanup_notes: list[str] = []
    reasoning_notes: list[str] = []

    if logic_form == "obligation":
        obj = norm.object_canonical or (_short_anchor_slug(doi_raw, max_len=80) if doi_raw else None)
        if not obj and norm.effect_canonical:
            obj = _short_anchor_slug(norm.effect_canonical, max_len=80)
            reasoning_notes.append("recovered_object_from_effect_canonical")
        if not obj and kt_raw:
            obj = _short_anchor_slug(kt_raw, max_len=80)
            reasoning_notes.append("recovered_object_from_ket_qua_thu_tuc")
        if not obj:
            ho_so = _cell(row.get("thanh_phan_ho_so"))
            items = _clean_dossier_items(ho_so)
            if items:
                obj = _short_anchor_slug(items[0], max_len=80)
                reasoning_notes.append("recovered_object_from_thanh_phan_ho_so_first_item")
        if isinstance(obj, str) and len(obj) > 80:
            obj = _short_anchor_slug(obj, max_len=80)
        action = pred_anchor
        if isinstance(action, str) and len(action) > 80:
            action = _short_anchor_slug(action, max_len=80)
        head = _term_clean(
            "obligation",
            [
                subj or "unresolved_subject",
                action or "unresolved_predicate",
                obj or "unresolved_object_atom",
            ],
        )
    elif logic_form == "permission":
        obj = norm.object_canonical or (_short_anchor_slug(doi_raw, max_len=80) if doi_raw else None)
        if not obj and norm.effect_canonical:
            obj = _short_anchor_slug(norm.effect_canonical, max_len=80)
            reasoning_notes.append("recovered_object_from_effect_canonical")
        if not obj and kt_raw:
            obj = _short_anchor_slug(kt_raw, max_len=80)
            reasoning_notes.append("recovered_object_from_ket_qua_thu_tuc")
        if not obj:
            ho_so = _cell(row.get("thanh_phan_ho_so"))
            items = _clean_dossier_items(ho_so)
            if items:
                obj = _short_anchor_slug(items[0], max_len=80)
                reasoning_notes.append("recovered_object_from_thanh_phan_ho_so_first_item")
        if isinstance(obj, str) and len(obj) > 80:
            obj = _short_anchor_slug(obj, max_len=80)
        action = pred_anchor
        if isinstance(action, str) and len(action) > 80:
            action = _short_anchor_slug(action, max_len=80)
        head = _term_clean(
            "permission",
            [
                subj or "unresolved_subject",
                action or "unresolved_predicate",
                obj or "unresolved_object_atom",
            ],
        )
    elif logic_form == "prohibition":
        obj = norm.object_canonical or (_short_anchor_slug(doi_raw, max_len=80) if doi_raw else None)
        if not obj and norm.effect_canonical:
            obj = _short_anchor_slug(norm.effect_canonical, max_len=80)
            reasoning_notes.append("recovered_object_from_effect_canonical")
        if not obj and kt_raw:
            obj = _short_anchor_slug(kt_raw, max_len=80)
            reasoning_notes.append("recovered_object_from_ket_qua_thu_tuc")
        if not obj:
            ho_so = _cell(row.get("thanh_phan_ho_so"))
            items = _clean_dossier_items(ho_so)
            if items:
                obj = _short_anchor_slug(items[0], max_len=80)
                reasoning_notes.append("recovered_object_from_thanh_phan_ho_so_first_item")
        if isinstance(obj, str) and len(obj) > 80:
            obj = _short_anchor_slug(obj, max_len=80)
        action = pred_anchor
        if isinstance(action, str) and len(action) > 80:
            action = _short_anchor_slug(action, max_len=80)
        head = _term_clean(
            "prohibition",
            [
                subj or "unresolved_subject",
                action or "unresolved_predicate",
                obj or "unresolved_object_atom",
            ],
        )
    elif logic_form == "deadline":
        raw_thoi_han_so = _cell(row.get("thoi_han_so"))
        raw_moc_tinh_thoi_han = _cell(row.get("moc_tinh_thoi_han"))

        ev = (
            pred_anchor
            or (to_snake_id(hanh_raw) if hanh_raw else None)
            or "deadline_event_unresolved"
        )
        if isinstance(ev, str) and len(ev) > 80:
            ev = _short_anchor_slug(ev, max_len=80)

        value = _numish(row.get("thoi_han_so"))
        unit = _unit_slug(row, norm)
        anchor = _cell(row.get("moc_tinh_thoi_han"))

        restored_deadline_value = False
        restored_deadline_unit = False
        if value is None:
            extracted_val, extracted_unit = _extract_deadline_value_unit_from_text(row)
            value = extracted_val
            restored_deadline_value = value is not None
            if extracted_unit and not unit:
                unit = extracted_unit
                restored_deadline_unit = True

        if not unit:
            u_raw = _cell(row.get("don_vi_thoi_han")) or _cell(row.get("don_vi_nguong"))
            unit = to_snake_id(u_raw) if u_raw else "unspecified_unit"

        if not anchor:
            anchor = _cell(row.get("bieu_thuc_thoi_han")) or _cell(row.get("grounded_summary"))
            anchor = _short_anchor_slug(anchor, max_len=80)

        # Ensure `head.args` never contains `null` for deadline.
        if value is None:
            value = "unresolved_deadline_value_atom"

        deadline_incomplete = (
            value == "unresolved_deadline_value_atom"
            or unit in (None, "", "unspecified_unit")
            or not anchor
            or anchor in ("anchor_unresolved", "anchor_unspecified")
        )
        if deadline_incomplete:
            fallback_kind = fallback_kind or "incomplete_deadline"
            if raw_thoi_han_so is None and not restored_deadline_value:
                reasoning_notes.append("deadline_value_still_unresolved")
            if raw_moc_tinh_thoi_han is None:
                reasoning_notes.append("deadline_anchor_missing_or_derived")

        head = _term_clean(
            "deadline",
            [ev, value, unit, anchor or "anchor_unspecified"],
        )
    elif logic_form == "dossier":
        items = _clean_dossier_items(_cell(row.get("thanh_phan_ho_so")))
        dossier_pred = pred_anchor
        if not dossier_pred or (hanh_raw and hanh_raw.strip().lower() in _PLACEHOLDER_HANH_VI):
            dossier_pred = pred_anchor or "dossier_predicate_missing"
            head_cleanup_notes.append("dossier_predicate_fallback_due_to_placeholder")
        if not items:
            items = ["unresolved_dossier_item_atom"]
            fallback_kind = fallback_kind or "dossier_items_unresolved"
        head = _term_clean("dossier", [dossier_pred, items or []])
    elif logic_form == "authority_action":
        kq = norm.effect_canonical or (to_snake_id(kt_raw) if kt_raw and len(kt_raw) < 100 else None)
        if not kq and kt_raw:
            kq = to_snake_id(kt_raw[:200])
        obj_e = norm.object_canonical or kq or "object_or_result_unresolved"
        if isinstance(obj_e, str):
            base = _truncate_slug_before_markers(obj_e, _EFFECT_TRUNC_MARKERS)
            if base and base != obj_e:
                obj_e = base
            obj_e = _short_anchor_slug(obj_e, max_len=80)
        head = _term_clean(
            "authority_action",
            [
                auth or "unresolved_authority",
                pred_anchor or "unresolved_predicate",
                obj_e,
            ],
        )
    elif logic_form == "exception":
        exc_anchor_short = (
            _short_anchor_slug(ngoai_le, max_len=80)
            if ngoai_le
            else "unresolved_exception_atom"
        )
        if ngoai_le and len(str(ngoai_le)) > 80:
            head_cleanup_notes.append("shortened_exception_anchor_for_head")
        head = _term_clean(
            "exception",
            [pred_anchor or rule_id, exc_anchor_short],
        )
    elif logic_form == "threshold":
        mc = _metric_slug(row, norm)
        uu = _unit_slug(row, norm)
        op = _op_clean(row)
        gv = _numish(row.get("gia_tri_nguong"))
        gt = _numish(row.get("gia_tri_tu"))
        gd = _numish(row.get("gia_tri_den"))
        kk = _cell(row.get("kieu_khoang"))

        if not mc or mc == "unknown_metric":
            t_raw = _cell(row.get("ten_chi_so"))
            mc = to_snake_id(t_raw) if t_raw else None
        if not mc:
            mc = "unspecified_metric"
        value = gv
        # Nếu gia_tri_nguong trống nhưng có cận dưới/cận trên, cố dựng threshold đơn.
        if value is None:
            if gt is not None and gd is None:
                value = gt
                op = op or "ge"
            elif gd is not None and gt is None:
                value = gd
                op = op or "le"

        if value is None and gv is None and gt is None and gd is None:
            threshold_fallback = True
            fallback_kind = "unresolved_threshold"
            value = "threshold_value_unresolved"
            reasoning_notes.append("restored_threshold_value_failed_unresolved")

        if not op and value is not None:
            op = "eq"

        if gt is not None and gd is not None:
            head = _term_clean(
                "threshold_range",
                [mc, gt, gd, uu or "unspecified_unit", kk or "unspecified_interval"],
            )
        else:
            head = _term_clean(
                "threshold",
                [mc, op or "unspecified_op", value, uu or "unspecified_unit"],
            )
    elif logic_form == "legal_effect":
        ent = subj or auth or "unresolved_entity_atom"
        e_arg = eff_head or (norm.effect_canonical if norm.effect_canonical else "unresolved_effect_atom")
        if isinstance(e_arg, str) and len(e_arg) > 120:
            truncated = _truncate_slug_before_markers(e_arg, _EFFECT_TRUNC_MARKERS)
            if truncated and truncated != e_arg:
                e_arg = truncated
                head_cleanup_notes.append("truncated_long_effect_in_head")
        if isinstance(e_arg, str) and len(e_arg) > 80:
            # Capping độ dài để đảm bảo Prolog/ProbLog atom không quá dài.
            e_arg = _short_anchor_slug(e_arg, max_len=80)
            head_cleanup_notes.append("capped_long_effect_in_head")
        head = _term_clean("legal_effect", [ent, e_arg])
    elif logic_form == "applicability_condition":
        anchor = pred_anchor or norm.scope_canonical
        if not anchor or anchor in ("truong_hop", "trường_hợp") or len(anchor) < 6:
            anchor = (
                norm.scope_canonical
                if norm.scope_canonical and len(norm.scope_canonical) >= 6
                else f"anchor_{rule_id[-6:]}"
            )
        cond_raw = dieu_kien or bieu_thuc_dk
        cond_anchor = _short_anchor_slug(cond_raw, max_len=80)
        if isinstance(anchor, str) and len(anchor) > 80:
            anchor = _short_anchor_slug(anchor, max_len=80)
        if cond_raw and len(str(cond_raw)) > 90:
            head_cleanup_notes.append("shortened_condition_anchor_in_head")
        head = _term_clean("applicability_condition", [anchor, cond_anchor])
    elif logic_form == "procedure_step":
        step_pred = pred_anchor or "unresolved_procedure_step"
        step_obj = (
            norm.object_canonical
            or (_short_anchor_slug(doi_raw, max_len=80) if doi_raw else "unresolved_object_atom")
        )
        if isinstance(step_pred, str):
            step_pred = _short_anchor_slug(step_pred, max_len=80)
        if isinstance(step_obj, str):
            step_obj = _short_anchor_slug(step_obj, max_len=80)
        head = _term_clean("procedure_step", [step_pred, step_obj])
    else:
        head = _term_clean("generic_rule", [rule_type_source, rule_id])

    # Fill fallback kinds for unresolved essential slots.
    hpred = head.get("predicate")
    hargs = head.get("args") or []
    if hpred == "legal_effect" and len(hargs) >= 2 and hargs[1] == "unresolved_effect_atom":
        fallback_kind = fallback_kind or "unresolved_effect"
    if hpred in ("obligation", "permission", "prohibition", "authority_action") and len(hargs) >= 3:
        if hargs[2] == "unresolved_object_atom":
            fallback_kind = fallback_kind or "unresolved_object"
    if hpred == "procedure_step" and len(hargs) >= 2:
        if hargs[1] == "unresolved_object_atom":
            fallback_kind = fallback_kind or "unresolved_object"
    if hpred == "exception" and len(hargs) >= 2 and hargs[1] == "unresolved_exception_atom":
        fallback_kind = fallback_kind or "unresolved_exception"

    expr_moved = bool(bieu_thuc_dk)
    body = build_body_clean(
        row,
        norm,
        logic_form,
        effect_tail_slug=eff_tail,
        expr_slug_moved_to_metadata=expr_moved,
    )

    # Bỏ trùng: nếu unless trùng raw_condition — giữ unless, bỏ raw_condition trùng nội dung
    _dedupe_body(body)

    readiness = resolve_logic_readiness(
        canonical_status, logic_form, head, threshold_fallback
    )

    auxiliary = _build_auxiliary_clean(row, norm, logic_form, pred_anchor)

    head_pred = head.get("predicate")
    head_args = head.get("args") or []

    inferred_subject_canonical = norm.subject_canonical or subj
    inferred_authority_canonical = norm.authority_canonical or auth
    inferred_object_canonical = norm.object_canonical
    inferred_effect_canonical = norm.effect_canonical
    inferred_metric_canonical = norm.metric_canonical
    inferred_unit_canonical = norm.unit_canonical

    if head_pred in ("obligation", "permission", "prohibition") and len(head_args) >= 3:
        inferred_object_canonical = head_args[2]
    elif head_pred == "authority_action" and len(head_args) >= 3:
        inferred_object_canonical = head_args[2]
    elif head_pred == "procedure_step" and len(head_args) >= 2:
        inferred_object_canonical = head_args[1]
    elif head_pred == "dossier" and len(head_args) >= 2:
        # dossier head arg2 is list(items); we keep object_canonical as-is
        pass
    elif head_pred == "legal_effect" and len(head_args) >= 2:
        inferred_effect_canonical = head_args[1]

    if head_pred == "deadline" and len(head_args) >= 3:
        inferred_unit_canonical = head_args[2]
    if head_pred == "threshold" and len(head_args) >= 4:
        inferred_metric_canonical = head_args[0]
        inferred_unit_canonical = head_args[3]
    if head_pred == "threshold_range" and len(head_args) >= 5:
        inferred_metric_canonical = head_args[0]
        inferred_unit_canonical = head_args[3]

    # Canonical slug for conditional expression (used as an anchor/fingerprint).
    expression_condition_slug = (
        _short_anchor_slug(bieu_thuc_dk, max_len=120)
        if bieu_thuc_dk
        else (_short_anchor_slug(dieu_kien, max_len=120) if dieu_kien else None)
    )

    norm_notes: list[str] = list(norm.normalization_notes or [])
    # Promote recovery traces into normalization_notes for transparency.
    for rn in reasoning_notes:
        if rn.startswith(("recovered_", "deadline_", "deadline_value_", "restored_")):
            if rn not in norm_notes:
                norm_notes.append(rn)

    norm_status = norm.normalization_status
    if fallback_kind in ("incomplete_deadline", "unresolved_object", "unresolved_effect", "unresolved_exception"):
        norm_status = "partial"

    metadata: dict[str, Any] = {
        "tinh_chat_phap_ly": _cell(row.get("tinh_chat_phap_ly")),
        "extraction_pattern": _cell(row.get("extraction_pattern")),
        "canonical_predicate": pred_anchor,
        "predicate_family": norm.predicate_family or _cell(row.get("predicate_family")),
        "effect_canonical": inferred_effect_canonical,
        "object_canonical": inferred_object_canonical,
        "subject_canonical": inferred_subject_canonical,
        "authority_canonical": inferred_authority_canonical,
        "metric_canonical": inferred_metric_canonical,
        "unit_canonical": inferred_unit_canonical,
        "canonical_status": canonical_status,
        "logic_form_overrides": lf_notes,
        "normalization_status": norm_status,
        "normalization_notes": norm_notes,
        "expression_condition_slug": expression_condition_slug,
        "fallback_kind": fallback_kind,
        "provenance": {
            "doc_id": _cell(row.get("doc_id")),
            "doc_code": _cell(row.get("doc_code")),
            "source_ref": _cell(row.get("source_ref")),
            "source_ref_full": _cell(row.get("source_ref_full")),
            "source_text": _cell(row.get("source_text")),
        },
        "review": {
            "do_tin_cay_trich_xuat": _cell(row.get("do_tin_cay_trich_xuat")),
            "can_ra_soat": _cell(row.get("can_ra_soat")),
            "muc_do_day_du": _cell(row.get("muc_do_day_du")),
        },
        "raw_fields_preserved": {
            "dieu_kien_ap_dung": dieu_kien,
            "ngoai_le": ngoai_le,
            "bieu_thuc_dieu_kien": bieu_thuc_dk,
            "bieu_thuc_thoi_han": _cell(row.get("bieu_thuc_thoi_han")),
            "phuong_thuc_thuc_hien": _cell(row.get("phuong_thuc_thuc_hien")),
            "ket_qua_thu_tuc": kt_raw,
        },
    }

    return {
        "rule_id": rule_id,
        "rule_group_id": _cell(row.get("rule_group_id")),
        "rule_type_source": rule_type_source,
        "logic_form": logic_form,
        "logic_readiness": readiness,
        "head": head,
        "body": body,
        "auxiliary_clauses": auxiliary,
        "metadata": metadata,
        "head_cleanup_notes": head_cleanup_notes,
        "body_cleanup_notes": body_cleanup_notes,
        "fallback_kind": fallback_kind,
        "reasoning_notes": reasoning_notes,
    }


def _dedupe_body(body: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    i = 0
    while i < len(body):
        b = body[i]
        key = json.dumps(b, sort_keys=True, ensure_ascii=False)
        if key in seen:
            body.pop(i)
            continue
        seen.add(key)
        i += 1


def _build_auxiliary_clean(
    row: pd.Series,
    norm: NormalizedVocab,
    logic_form: str,
    pred_anchor: str | None,
) -> list[dict[str, Any]]:
    """Structured auxiliary — không raw_text."""
    aux: list[dict[str, Any]] = []
    rule_id = _cell(row.get("rule_id")) or "UNKNOWN"
    hanh_raw = _cell(row.get("hanh_vi_phap_ly")) or _cell(row.get("canonical_predicate"))

    if logic_form != "deadline" and _cell(row.get("thoi_han_so")):
        aux.append(
            {
                "kind": "deadline_fact",
                "head": _term_clean(
                    "deadline",
                    [
                        pred_anchor or to_snake_id(hanh_raw) if hanh_raw else rule_id,
                        _numish(row.get("thoi_han_so")),
                        to_snake_id(_cell(row.get("don_vi_thoi_han")) or "") or "unspecified",
                        _cell(row.get("moc_tinh_thoi_han")),
                    ],
                ),
                "body": [],
            }
        )
    if logic_form != "dossier" and _cell(row.get("thanh_phan_ho_so")):
        aux.append(
            {
                "kind": "dossier_fact",
                "head": _term_clean(
                    "dossier",
                    [
                        pred_anchor or rule_id,
                        _split_dossier_items(_cell(row.get("thanh_phan_ho_so"))),
                    ],
                ),
                "body": [],
            }
        )
    if logic_form != "threshold" and (
        _cell(row.get("ten_chi_so")) or _numish(row.get("gia_tri_nguong")) is not None
    ):
        aux.append(
            {
                "kind": "threshold_fact",
                "head": _term_clean(
                    "threshold_note",
                    [
                        _metric_slug(row, norm),
                        _op_clean(row),
                        _numish(row.get("gia_tri_nguong")),
                        _unit_slug(row, norm),
                    ],
                ),
                "body": [],
            }
        )
    return aux


__all__ = ["build_logic_ir_record", "infer_logic_form"]
