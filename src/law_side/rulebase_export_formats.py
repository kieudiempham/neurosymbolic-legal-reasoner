"""
Export `rulebase_seed.xlsx` to rich JSONL and structured logic JSON.

Does not modify the Excel file. See docs/rulebase_export_formats.md.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

# All columns expected in rulebase_seed (ground truth for export shape).
JSONL_BLOCKS = {
    "identity": [
        "rule_id",
        "rule_group_id",
        "frame_id",
        "candidate_id",
        "source_unit_id",
    ],
    "provenance": [
        "doc_id",
        "doc_code",
        "source_ref",
        "source_ref_full",
        "heading",
        "parent_context",
        "source_text",
        "van_ban_dan_chieu",
    ],
    "classification": [
        "rule_type",
        "tinh_chat_phap_ly",
        "canonical_predicate",
        "typed_predicate",
        "predicate_family",
    ],
    "core_legal_content": [
        "chu_the",
        "loai_chu_the",
        "vai_tro_chu_the",
        "pham_vi_ap_dung",
        "dieu_kien_ap_dung",
        "bieu_thuc_dieu_kien",
        "hanh_vi_phap_ly",
        "doi_tuong_hanh_vi",
        "he_qua_phap_ly",
    ],
    "threshold": [
        "ten_chi_so",
        "toan_tu_so_sanh",
        "gia_tri_nguong",
        "don_vi_nguong",
        "gia_tri_tu",
        "gia_tri_den",
        "kieu_khoang",
    ],
    "deadline": [
        "thoi_han_so",
        "don_vi_thoi_han",
        "moc_tinh_thoi_han",
        "bieu_thuc_thoi_han",
    ],
    "dossier": ["thanh_phan_ho_so"],
    "authority": [
        "co_quan_tiep_nhan",
        "co_quan_xu_ly",
        "ket_qua_thu_tuc",
        "phuong_thuc_thuc_hien",
    ],
    "exception": ["ngoai_le"],
    "generation_support": [
        "grounded_summary",
        "answer_template",
        "explanation_template",
    ],
    "quality": [
        "muc_do_day_du",
        "do_tin_cay_trich_xuat",
        "can_ra_soat",
        "ly_do_can_ra_soat",
        "extraction_pattern",
        "notes",
    ],
}


RULE_TYPE_TO_LOGIC_FORM: dict[str, str] = {
    "quy_tac_nghia_vu": "obligation",
    "quy_tac_quyen": "permission",
    "quy_tac_cam_doan": "prohibition",
    "quy_tac_thoi_han": "deadline",
    "quy_tac_ho_so": "dossier",
    "quy_tac_hanh_dong_co_quan": "authority_action",
    "quy_tac_ngoai_le": "exception_rule",
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


def _term(predicate: str, args: list[Any]) -> dict[str, Any]:
    return {"predicate": predicate, "args": args}


def _raw_clause(field: str, text: str | None) -> dict[str, Any] | None:
    t = _cell(text)
    if not t:
        return None
    return {"type": "raw_text", "field": field, "text": t}


def row_to_jsonl_object(row: pd.Series) -> dict[str, Any]:
    """Nested JSON object with stable keys (null for empty)."""
    out: dict[str, Any] = {}
    for block, keys in JSONL_BLOCKS.items():
        out[block] = {k: _cell(row.get(k)) for k in keys}
    return out


def row_to_logic_record(row: pd.Series) -> dict[str, Any]:
    """
    One logic record per Excel row: primary representation + optional auxiliary
    clauses + full metadata for partial / failed atomization.
    """
    rule_id = _cell(row.get("rule_id")) or "UNKNOWN"
    rule_type = _cell(row.get("rule_type")) or "unknown"
    logic_form = RULE_TYPE_TO_LOGIC_FORM.get(str(rule_type), "generic_rule")

    chu_the = _cell(row.get("chu_the"))
    hanh_vi = _cell(row.get("hanh_vi_phap_ly")) or _cell(row.get("canonical_predicate"))
    doi_tuong = _cell(row.get("doi_tuong_hanh_vi"))
    dieu_kien = _cell(row.get("dieu_kien_ap_dung"))
    bieu_thuc_dk = _cell(row.get("bieu_thuc_dieu_kien"))
    he_qua = _cell(row.get("he_qua_phap_ly"))
    ngoai_le = _cell(row.get("ngoai_le"))
    pham_vi = _cell(row.get("pham_vi_ap_dung"))

    head: dict[str, Any]
    body: list[Any] = []

    # Shared body atoms from conditions / scope / exception hooks
    if logic_form != "exception_rule":
        for pred, val in (
            ("applies_when", dieu_kien),
            ("applies_scope", pham_vi),
            ("unless_exception_text", ngoai_le),
        ):
            c = _raw_clause(pred, val) if val else None
            if c:
                body.append(c)
    else:
        if dieu_kien:
            body.append(_raw_clause("applies_when", dieu_kien))
        if pham_vi:
            body.append(_raw_clause("applies_scope", pham_vi))
    if bieu_thuc_dk:
        body.append(_raw_clause("expression_condition", bieu_thuc_dk))

    if logic_form == "obligation":
        head = _term("obligation", [chu_the or "_subject", hanh_vi or "_action"])
    elif logic_form == "permission":
        head = _term("permission", [chu_the or "_subject", hanh_vi or "_action"])
    elif logic_form == "prohibition":
        head = _term("prohibition", [chu_the or "_subject", hanh_vi or "_action"])
    elif logic_form == "deadline":
        head = _term(
            "deadline",
            [
                hanh_vi or _cell(row.get("canonical_predicate")) or "_event",
                _numish(row.get("thoi_han_so")),
                _cell(row.get("don_vi_thoi_han")),
                _cell(row.get("moc_tinh_thoi_han")),
            ],
        )
    elif logic_form == "dossier":
        items = _split_dossier_items(_cell(row.get("thanh_phan_ho_so")))
        head = _term("dossier", [hanh_vi or rule_id, items])
    elif logic_form == "authority_action":
        head = _term(
            "authority_action",
            [
                _cell(row.get("co_quan_xu_ly")) or _cell(row.get("co_quan_tiep_nhan")) or "_authority",
                hanh_vi or "_action",
                _cell(row.get("ket_qua_thu_tuc")),
            ],
        )
    elif logic_form == "exception_rule":
        head = _term("exception", [rule_id, ngoai_le or "_exception_content"])
    elif logic_form == "threshold":
        gt = _numish(row.get("gia_tri_tu"))
        gd = _numish(row.get("gia_tri_den"))
        kk = _cell(row.get("kieu_khoang"))
        if gt is not None and gd is not None:
            head = _term(
                "threshold_range",
                [
                    _cell(row.get("ten_chi_so")) or "_metric",
                    kk or "unspecified_interval_kind",
                    gt,
                    gd,
                    _cell(row.get("don_vi_nguong")),
                ],
            )
        else:
            head = _term(
                "threshold",
                [
                    _cell(row.get("ten_chi_so")) or "_metric",
                    _cell(row.get("toan_tu_so_sanh")) or "_op",
                    _numish(row.get("gia_tri_nguong")),
                    _cell(row.get("don_vi_nguong")),
                ],
            )
    elif logic_form == "legal_effect":
        head = _term("legal_effect", [chu_the or "_entity", he_qua or "_effect"])
    elif logic_form == "applicability_condition":
        head = _term("applicability_condition", [dieu_kien or bieu_thuc_dk or "_condition"])
    elif logic_form == "procedure_step":
        head = _term("procedure_step", [hanh_vi or "_step", doi_tuong or "_object"])
    else:
        head = _term("generic_rule", [rule_type, rule_id])

    auxiliary: list[dict[str, Any]] = []

    # Enrich: separate structured facts when primary type is not dedicated but slots are filled
    if logic_form != "deadline" and _cell(row.get("thoi_han_so")):
        auxiliary.append(
            {
                "kind": "deadline_fact",
                "head": _term(
                    "deadline",
                    [
                        hanh_vi or rule_id,
                        _numish(row.get("thoi_han_so")),
                        _cell(row.get("don_vi_thoi_han")),
                        _cell(row.get("moc_tinh_thoi_han")),
                    ],
                ),
                "body": [],
            }
        )
    if logic_form != "dossier" and _cell(row.get("thanh_phan_ho_so")):
        auxiliary.append(
            {
                "kind": "dossier_fact",
                "head": _term(
                    "dossier",
                    [rule_id, _split_dossier_items(_cell(row.get("thanh_phan_ho_so")))],
                ),
                "body": [],
            }
        )
    if logic_form != "authority_action" and (
        _cell(row.get("co_quan_tiep_nhan")) or _cell(row.get("co_quan_xu_ly"))
    ):
        auxiliary.append(
            {
                "kind": "authority_fact",
                "head": _term(
                    "authority_context",
                    [
                        _cell(row.get("co_quan_tiep_nhan")),
                        _cell(row.get("co_quan_xu_ly")),
                        _cell(row.get("ket_qua_thu_tuc")),
                    ],
                ),
                "body": [],
            }
        )
    if logic_form != "threshold" and (
        _cell(row.get("ten_chi_so")) or _numish(row.get("gia_tri_nguong")) is not None
    ):
        auxiliary.append(
            {
                "kind": "threshold_fact",
                "head": _term(
                    "threshold_note",
                    [
                        _cell(row.get("ten_chi_so")),
                        _cell(row.get("toan_tu_so_sanh")),
                        _numish(row.get("gia_tri_nguong")),
                        _cell(row.get("don_vi_nguong")),
                    ],
                ),
                "body": [],
            }
        )
    if logic_form != "exception_rule" and ngoai_le and logic_form in (
        "obligation",
        "permission",
        "prohibition",
        "legal_effect",
        "applicability_condition",
    ):
        auxiliary.append(
            {
                "kind": "exception_attachment",
                "head": _term("unless", [ngoai_le]),
                "body": [],
            }
        )

    metadata = {
        "tinh_chat_phap_ly": _cell(row.get("tinh_chat_phap_ly")),
        "canonical_predicate": _cell(row.get("canonical_predicate")),
        "typed_predicate": _cell(row.get("typed_predicate")),
        "predicate_family": _cell(row.get("predicate_family")),
        "extraction_pattern": _cell(row.get("extraction_pattern")),
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
            "bieu_thuc_thoi_han": _cell(row.get("bieu_thuc_thoi_han")),
            "phuong_thuc_thuc_hien": _cell(row.get("phuong_thuc_thuc_hien")),
        },
    }

    return {
        "rule_id": rule_id,
        "rule_group_id": _cell(row.get("rule_group_id")),
        "rule_type": rule_type,
        "logic_form": logic_form,
        "head": head,
        "body": body,
        "auxiliary_clauses": auxiliary,
        "metadata": metadata,
    }


def export_rulebase_formats(
    xlsx_path: Path,
    out_jsonl: Path,
    out_logic_json: Path,
) -> tuple[int, int]:
    """
    Write JSONL (one object per line) and a single JSON array file for logic.

    Returns (n_rows_jsonl, n_rows_logic).
    """
    df = pd.read_excel(xlsx_path)
    n = len(df)

    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    out_logic_json.parent.mkdir(parents=True, exist_ok=True)

    logic_rows: list[dict[str, Any]] = []
    with out_jsonl.open("w", encoding="utf-8") as fj:
        for _, row in df.iterrows():
            obj = row_to_jsonl_object(row)
            fj.write(json.dumps(obj, ensure_ascii=False) + "\n")
            logic_rows.append(row_to_logic_record(row))

    payload = {
        "version": 1,
        "source_file": str(xlsx_path.as_posix()),
        "rule_count": n,
        "rule_type_to_logic_form": RULE_TYPE_TO_LOGIC_FORM,
        "rules": logic_rows,
    }
    out_logic_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return n, n


__all__ = [
    "RULE_TYPE_TO_LOGIC_FORM",
    "JSONL_BLOCKS",
    "row_to_jsonl_object",
    "row_to_logic_record",
    "export_rulebase_formats",
]
