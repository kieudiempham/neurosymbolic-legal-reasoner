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
        if pc in GENERIC_PREDICATE_SLUGS and raw_tp and ":" in raw_tp:
            tail = to_snake_id(raw_tp.split(":", 1)[-1].strip())
            if tail and len(tail) > len(pc) + 3:
                return tail, "inferred_from_context"
        return pc, "exact_vocab_match"

    if raw_cp:
        s = to_snake_id(raw_cp)
        if s:
            return s, "inferred_from_context"

    if raw_tp and ":" in raw_tp:
        tail = to_snake_id(raw_tp.split(":", 1)[-1].strip())
        if tail:
            return tail, "inferred_from_context"

    if raw_hv:
        s = to_snake_id(raw_hv)
        if s and len(s) >= 8:
            return s, "inferred_from_context"

    if pf:
        return f"{to_snake_id(pf)}_level", "fallback_family_level"

    return None, "unresolved"


def _effect_arg_clean(norm: NormalizedVocab, he_raw: str | None) -> tuple[str | None, str | None]:
    """
    Trả về (effect_canonical_for_head, tail_exception_for_body).
    Không đưa câu dài có 'trừ trường hợp' vào head.
    """
    if norm.effect_canonical:
        return norm.effect_canonical, None
    if not he_raw:
        return None, None
    slug = to_snake_id(he_raw)
    base, frags = split_effect_exception_condition(slug)
    if frags:
        return base if len(base) >= 8 else None, frags[0][1] if frags else None
    if len(slug) > 80:
        return None, slug
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
        return to_snake_id(u)
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
    t = _cell(row.get("ten_chi_so"))
    if not t:
        return False
    s = to_snake_id(t)
    return "thoi_han" in s or s.startswith("han_")


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

    if norm.scope_canonical:
        body.append(_term_clean("applies_to", [norm.scope_canonical]))
    elif pham_vi:
        body.append(_term_clean("raw_scope", [pham_vi]))

    redundant_cond = False
    if dieu_kien and ngoai_le:
        dk = dieu_kien.strip().lower()
        nl = ngoai_le.strip().lower()
        if dk and dk in nl:
            redundant_cond = True

    if dieu_kien and not redundant_cond:
        if norm.normalization_status == "full" and anchor:
            body.append(_term_clean("applies_if", [anchor, dieu_kien]))
        else:
            body.append(_term_clean("raw_condition", [dieu_kien]))

    if ngoai_le and logic_form != "exception":
        body.append(_term_clean("unless", [ngoai_le]))

    if effect_tail_slug:
        body.append(_term_clean("raw_exception", [effect_tail_slug]))

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
    if threshold_fallback:
        return "fallback_threshold"
    if canonical_status == "unresolved":
        return "fallback_raw"
    pred = head.get("predicate")
    args = head.get("args") or []
    if any(a is None or a == "null" or a == "_metric" or a == "_op" for a in args):
        return "reasoning_partial"
    if logic_form == "generic_rule":
        return "fallback_raw"
    if canonical_status in ("fallback_family_level", "inferred_from_context"):
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

    if logic_form == "obligation":
        obj = norm.object_canonical or (to_snake_id(doi_raw) if doi_raw else None)
        head = _term_clean(
            "obligation",
            [subj or "_subject", pred_anchor or "_action", obj or "_object"],
        )
    elif logic_form == "permission":
        obj = norm.object_canonical or (to_snake_id(doi_raw) if doi_raw else None)
        head = _term_clean(
            "permission",
            [subj or "_subject", pred_anchor or "_action", obj or "_object"],
        )
    elif logic_form == "prohibition":
        obj = norm.object_canonical or (to_snake_id(doi_raw) if doi_raw else None)
        head = _term_clean(
            "prohibition",
            [subj or "_subject", pred_anchor or "_action", obj or "_object"],
        )
    elif logic_form == "deadline":
        ev = pred_anchor or to_snake_id(hanh_raw) if hanh_raw else pred_anchor
        head = _term_clean(
            "deadline",
            [
                ev or rule_id,
                _numish(row.get("thoi_han_so")),
                _unit_slug(row, norm) or to_snake_id(_cell(row.get("don_vi_thoi_han")) or "")
                or "unspecified_unit",
                _cell(row.get("moc_tinh_thoi_han")),
            ],
        )
    elif logic_form == "dossier":
        items = _split_dossier_items(_cell(row.get("thanh_phan_ho_so")))
        dossier_pred = pred_anchor
        if not dossier_pred or (hanh_raw and hanh_raw.strip().lower() in _PLACEHOLDER_HANH_VI):
            dossier_pred = pred_anchor or "dossier_requirement"
        head = _term_clean("dossier", [dossier_pred, items])
    elif logic_form == "authority_action":
        kq = norm.effect_canonical or (to_snake_id(kt_raw) if kt_raw and len(kt_raw) < 100 else None)
        if not kq and kt_raw:
            kq = to_snake_id(kt_raw[:200])
        obj_e = norm.object_canonical or kq or "_object_or_result"
        head = _term_clean(
            "authority_action",
            [auth or "_authority", pred_anchor or "_action", obj_e],
        )
    elif logic_form == "exception":
        head = _term_clean(
            "exception",
            [pred_anchor or rule_id, ngoai_le or "_exception_content"],
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
            mc = to_snake_id(_cell(row.get("ten_chi_so")) or "") or None
        if not mc:
            mc = "unspecified_metric"
            threshold_fallback = True
        if not op and gv is not None:
            op = "eq"
        elif not op:
            op = "unspecified_op"
            if gv is None and gt is None and gd is None:
                threshold_fallback = True

        if gt is not None and gd is not None:
            head = _term_clean(
                "threshold_range",
                [mc, gt, gd, uu or "unspecified_unit", kk or "unspecified_interval"],
            )
        else:
            head = _term_clean("threshold", [mc, op, gv, uu or "unspecified_unit"])
            if gv is None and not threshold_fallback:
                threshold_fallback = True
    elif logic_form == "legal_effect":
        ent = subj or auth or "_entity"
        e_arg = eff_head or "_effect_unresolved"
        head = _term_clean("legal_effect", [ent, e_arg])
    elif logic_form == "applicability_condition":
        anchor = pred_anchor or norm.scope_canonical
        if not anchor or anchor in ("truong_hop", "trường_hợp") or len(anchor) < 6:
            anchor = norm.scope_canonical or pred_anchor or f"anchor_{rule_id[-12:]}"
        cond = dieu_kien or bieu_thuc_dk or "_condition"
        head = _term_clean("applicability_condition", [anchor, cond])
    elif logic_form == "procedure_step":
        head = _term_clean(
            "procedure_step",
            [pred_anchor or "_step", norm.object_canonical or to_snake_id(doi_raw) if doi_raw else "_object"],
        )
    else:
        head = _term_clean("generic_rule", [rule_type_source, rule_id])

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

    metadata: dict[str, Any] = {
        "tinh_chat_phap_ly": _cell(row.get("tinh_chat_phap_ly")),
        "extraction_pattern": _cell(row.get("extraction_pattern")),
        "canonical_predicate": pred_anchor,
        "predicate_family": norm.predicate_family or _cell(row.get("predicate_family")),
        "effect_canonical": norm.effect_canonical,
        "object_canonical": norm.object_canonical,
        "subject_canonical": norm.subject_canonical,
        "authority_canonical": norm.authority_canonical,
        "metric_canonical": norm.metric_canonical,
        "unit_canonical": norm.unit_canonical,
        "canonical_status": canonical_status,
        "logic_form_overrides": lf_notes,
        "normalization_status": norm.normalization_status,
        "normalization_notes": norm.normalization_notes,
        "expression_condition_slug": bieu_thuc_dk,
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
