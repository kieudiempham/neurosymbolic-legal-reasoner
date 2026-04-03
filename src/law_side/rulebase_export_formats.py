"""
Export `rulebase_seed.xlsx` to rich JSONL and structured logic JSON.

Does not modify the Excel file. See docs/rulebase_export_formats.md.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import pandas as pd

from law_side.rulebase_logic_ir import build_logic_ir_record
from law_side.rulebase_vocab_index import NormalizedVocab, VocabIndex, normalize_row_with_vocab
from law_side.controlled_vocabulary_builder import to_snake_id
import hashlib
from collections import defaultdict

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
    if logic_form != "exception":
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
    elif logic_form == "exception":
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
    if logic_form != "exception" and ngoai_le and logic_form in (
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


def build_rich_jsonl_object(row: pd.Series, norm: NormalizedVocab) -> dict[str, Any]:
    """JSONL giàu cấu trúc: raw + normalized_vocab + quality."""
    identity = {
        k: _cell(row.get(k))
        for k in (
            "rule_id",
            "rule_group_id",
            "frame_id",
            "candidate_id",
            "source_unit_id",
        )
    }
    provenance = {
        k: _cell(row.get(k))
        for k in (
            "doc_id",
            "doc_code",
            "source_ref",
            "source_ref_full",
            "source_text",
            "van_ban_dan_chieu",
        )
    }
    classification = {
        "rule_type": _cell(row.get("rule_type")),
        "tinh_chat_phap_ly": _cell(row.get("tinh_chat_phap_ly")),
    }
    normalized_vocab = {
        "predicate_family": norm.predicate_family,
        "predicate_canonical": norm.predicate_canonical,
        "predicate_typed": norm.predicate_typed,
        "object_canonical": norm.object_canonical,
        "object_family": norm.object_family,
        "effect_canonical": norm.effect_canonical,
        "effect_family": norm.effect_family,
        "subject_canonical": norm.subject_canonical,
        "subject_type_canonical": norm.subject_type_canonical,
        "authority_canonical": norm.authority_canonical,
        "scope_canonical": norm.scope_canonical,
        "metric_canonical": norm.metric_canonical,
        "unit_canonical": norm.unit_canonical,
    }
    raw_legal_content = {
        "canonical_predicate_raw": _cell(row.get("canonical_predicate")),
        "typed_predicate_raw": _cell(row.get("typed_predicate")),
        "predicate_family_raw": _cell(row.get("predicate_family")),
        "chu_the": _cell(row.get("chu_the")),
        "loai_chu_the": _cell(row.get("loai_chu_the")),
        "vai_tro_chu_the": _cell(row.get("vai_tro_chu_the")),
        "pham_vi_ap_dung": _cell(row.get("pham_vi_ap_dung")),
        "dieu_kien_ap_dung": _cell(row.get("dieu_kien_ap_dung")),
        "bieu_thuc_dieu_kien": _cell(row.get("bieu_thuc_dieu_kien")),
        "hanh_vi_phap_ly": _cell(row.get("hanh_vi_phap_ly")),
        "doi_tuong_hanh_vi": _cell(row.get("doi_tuong_hanh_vi")),
        "he_qua_phap_ly": _cell(row.get("he_qua_phap_ly")),
    }
    threshold = {
        k: _cell(row.get(k))
        for k in (
            "ten_chi_so",
            "toan_tu_so_sanh",
            "gia_tri_nguong",
            "don_vi_nguong",
            "gia_tri_tu",
            "gia_tri_den",
            "kieu_khoang",
        )
    }
    deadline = {
        k: _cell(row.get(k))
        for k in (
            "thoi_han_so",
            "don_vi_thoi_han",
            "moc_tinh_thoi_han",
            "bieu_thuc_thoi_han",
        )
    }
    dossier = {"thanh_phan_ho_so": _cell(row.get("thanh_phan_ho_so"))}
    authority = {
        k: _cell(row.get(k))
        for k in (
            "co_quan_tiep_nhan",
            "co_quan_xu_ly",
            "ket_qua_thu_tuc",
            "phuong_thuc_thuc_hien",
        )
    }
    exception = {"ngoai_le": _cell(row.get("ngoai_le"))}
    generation_support = {
        k: _cell(row.get(k))
        for k in ("grounded_summary", "answer_template", "explanation_template")
    }
    quality = {
        "muc_do_day_du": _cell(row.get("muc_do_day_du")),
        "do_tin_cay_trich_xuat": _cell(row.get("do_tin_cay_trich_xuat")),
        "can_ra_soat": _cell(row.get("can_ra_soat")),
        "ly_do_can_ra_soat": _cell(row.get("ly_do_can_ra_soat")),
        "extraction_pattern": _cell(row.get("extraction_pattern")),
        "notes": _cell(row.get("notes")),
        "normalization_status": norm.normalization_status,
        "normalization_notes": "; ".join(norm.normalization_notes) if norm.normalization_notes else None,
    }
    return {
        "identity": identity,
        "provenance": provenance,
        "classification": classification,
        "normalized_vocab": normalized_vocab,
        "raw_legal_content": raw_legal_content,
        "threshold": threshold,
        "deadline": deadline,
        "dossier": dossier,
        "authority": authority,
        "exception": exception,
        "generation_support": generation_support,
        "quality": quality,
    }


_PROBLOG_SAFE = re.compile(r"^[a-z][a-z0-9_]*$")


def _pl_atom(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(v)
    s = str(v).strip()
    if not s:
        return "null"
    if _PROBLOG_SAFE.match(s):
        return s
    esc = s.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{esc}'"


def row_to_problog_clause(row: pd.Series, norm: NormalizedVocab) -> str:
    """Một rule ProbLog: comment + clause hoặc fact."""
    logic = build_logic_ir_record(row, norm)
    rule_id = _cell(row.get("rule_id")) or "UNKNOWN"
    lines: list[str] = [
        f"% rule_id: {rule_id}",
        f"% rule_group_id: {_cell(row.get('rule_group_id')) or ''}",
        f"% doc_code: {_cell(row.get('doc_code')) or ''}",
        f"% source_ref: {_cell(row.get('source_ref')) or ''}",
        f"% predicate_canonical: {norm.predicate_canonical or ''}",
        f"% normalization_status: {norm.normalization_status}",
    ]
    st = _cell(row.get("source_text"))
    if st:
        one = st.replace("\n", " ").strip()[:240]
        lines.append(f"% source_text: {one}")

    lf = logic["logic_form"]
    h = logic["head"]
    pred = h["predicate"]
    args = [_pl_atom(a) for a in h["args"]]
    head_txt = f"{pred}({', '.join(args)})"

    body_atoms: list[str] = []
    for b in logic["body"]:
        if isinstance(b, dict) and b.get("type") == "raw_text":
            field = b.get("field", "raw")
            t = _pl_atom(b.get("text"))
            body_atoms.append(f"{field}({t})")
        elif isinstance(b, dict) and "predicate" in b:
            p = b["predicate"]
            ba = [_pl_atom(x) for x in b.get("args", [])]
            body_atoms.append(f"{p}({', '.join(ba)})")

    if body_atoms:
        lines.append(f"{head_txt} :-")
        lines.append("    " + ",\n    ".join(body_atoms) + ".")
    else:
        lines.append(f"{head_txt}.")

    return "\n".join(lines) + "\n"


def export_rulebase_formats(
    xlsx_path: Path,
    out_jsonl: Path,
    out_logic_json: Path,
    vocab_path: Path | None = None,
    out_problog: Path | None = None,
) -> tuple[int, int, dict[str, Any]]:
    """
    Ghi JSONL + logic JSON; nếu có controlled_vocabulary.xlsx thì join vocab + ProbLog.

    Returns (n_rows_jsonl, n_rows_logic, stats).
    """
    df = pd.read_excel(xlsx_path)
    n = len(df)

    default_vocab = xlsx_path.parent.parent / "ontology" / "controlled_vocabulary.xlsx"
    vpath = vocab_path or (default_vocab if default_vocab.exists() else None)

    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    out_logic_json.parent.mkdir(parents=True, exist_ok=True)
    if out_problog:
        out_problog.parent.mkdir(parents=True, exist_ok=True)

    stats: dict[str, Any] = {
        "rule_count": n,
        "predicate_mapped": 0,
        "effect_mapped": 0,
        "object_mapped": 0,
        "threshold_rules": 0,
        "threshold_range_rules": 0,
        "dossier_rules": 0,
        "legal_effect_rules": 0,
        "authority_action_rules": 0,
        "body_used_raw_condition": 0,
        "body_used_raw_scope": 0,
    }

    logic_rows: list[dict[str, Any]] = []
    idx: VocabIndex | None = None
    if vpath and Path(vpath).exists():
        idx = VocabIndex(Path(vpath))

    def _relative_display_path(p: Path | None) -> str | None:
        if p is None:
            return None
        try:
            return Path(os.path.relpath(str(p), start=str(Path.cwd()))).as_posix()
        except ValueError:
            # Fallback for different drives on Windows.
            return p.as_posix()

    with out_jsonl.open("w", encoding="utf-8") as fj:
        prob_lines: list[str] = []
        for _, row in df.iterrows():
            if idx is not None:
                norm = normalize_row_with_vocab(row, idx)
                if norm.predicate_canonical:
                    stats["predicate_mapped"] += 1
                if norm.effect_canonical:
                    stats["effect_mapped"] += 1
                if norm.object_canonical:
                    stats["object_mapped"] += 1
                obj = build_rich_jsonl_object(row, norm)
                lr = build_logic_ir_record(row, norm)
                if out_problog:
                    prob_lines.append(row_to_problog_clause(row, norm))
            else:
                norm = NormalizedVocab(normalization_status="unmapped", normalization_notes=["no_vocabulary_file"])
                obj = build_rich_jsonl_object(row, norm)
                lr = build_logic_ir_record(row, norm)
                if out_problog:
                    prob_lines.append(row_to_problog_clause(row, norm))

            fj.write(json.dumps(obj, ensure_ascii=False) + "\n")
            logic_rows.append(lr)

            lf = lr.get("logic_form")
            if lf == "threshold":
                stats["threshold_rules"] += 1
                h = lr.get("head", {})
                if h.get("predicate") == "threshold_range":
                    stats["threshold_range_rules"] += 1
            if lf == "dossier":
                stats["dossier_rules"] += 1
            if lf == "legal_effect":
                stats["legal_effect_rules"] += 1
            if lf == "authority_action":
                stats["authority_action_rules"] += 1

            for b in lr.get("body") or []:
                if isinstance(b, dict) and b.get("predicate") == "raw_condition":
                    stats["body_used_raw_condition"] += 1
                if isinstance(b, dict) and b.get("predicate") == "raw_scope":
                    stats["body_used_raw_scope"] += 1

        def _core_arg(a: Any) -> str:
            if a is None:
                return "<null>"
            if isinstance(a, (int, float)) and not isinstance(a, bool):
                return str(a)
            s = str(a).strip()
            if not s:
                return "<empty>"
            sl = s.lower()
            # Các placeholder/anchor unresolved làm seed cluster gần giống nhau.
            if (
                sl in ("unknown", "null")
                or sl.startswith("unresolved_")
                or sl.startswith("anchor_")
                or sl.startswith("unspecified_")
                or "_unresolved" in sl
            ):
                return "<unresolved>"
            if len(s) > 60:
                parts = [p for p in s.split("_") if p]
                if len(parts) >= 3:
                    return "_".join(parts[:4])
                return s[:60]
            return s

        def _term_sig(term: Any, core: bool) -> str:
            if isinstance(term, dict) and "predicate" in term:
                p = str(term.get("predicate"))
                args = term.get("args") or []
                args2 = [_core_arg(x) if core else str(x) for x in args]
                return f"{p}({','.join(args2)})"
            return str(term)

        def _head_sig(head: dict[str, Any], core: bool) -> str:
            p = head.get("predicate") or "generic_rule"
            args = head.get("args") or []
            args2 = [_core_arg(x) if core else str(x) for x in args]
            return f"{p}({','.join(args2)})"

        def _body_sigs(body: list[Any], core: bool) -> str:
            terms = []
            for b in body or []:
                terms.append(_term_sig(b, core=core))
            terms.sort()
            return "|".join(terms)

        def _sha_tag(s: str, n: int) -> str:
            h = hashlib.sha256(s.encode("utf-8")).hexdigest()
            return h[:n]

        # Semantic clustering: gắn nhãn nhóm trùng/gần trùng để dedup downstream.
        # Không làm thay đổi head/body; chỉ thêm metadata.
        READINESS_W = {"reasoning_ready": 3, "reasoning_partial": 2, "reasoning_fallback": 1}
        exact_groups: dict[tuple[str, str, str, str], list[int]] = defaultdict(list)

        # Precompute signatures once.
        for i, lr in enumerate(logic_rows):
            lf = lr.get("logic_form") or "generic_rule"
            head = lr.get("head") or {}
            body = lr.get("body") or []
            prov = (lr.get("metadata") or {}).get("provenance") or {}
            source_ref_full = prov.get("source_ref_full") or prov.get("source_ref") or ""
            source_text = prov.get("source_text") or ""
            source_slug = to_snake_id(source_text) if source_text else ""
            source_key = source_ref_full or source_slug[:50] or lr.get("rule_id", "rule")

            head_exact = _head_sig(head, core=False)
            body_exact = _body_sigs(body, core=False)
            head_core = _head_sig(head, core=True)
            body_core = _body_sigs(body, core=True)

            sig_exact = f"{lf}|{source_ref_full}|{head_exact}|{body_exact}"
            sig_core = f"{lf}|{source_ref_full}|{head_core}|{body_core}"

            lr.setdefault("metadata", {})
            lr["metadata"]["normalized_signature"] = "sig_" + _sha_tag(sig_exact, 16)
            lr["metadata"]["semantic_fingerprint"] = "fp_" + _sha_tag(sig_core, 16)

            cluster_key = f"{lf}|{(head.get('predicate') or 'generic')}|{source_key}"
            lr["metadata"]["semantic_cluster_id"] = "cluster_" + _sha_tag(cluster_key, 12)
            lr["metadata"]["variant_source"] = (
                "source_ref_full" if prov.get("source_ref_full") else ("source_ref" if prov.get("source_ref") else "source_text")
            )

            exact_key = (str(lf), str(source_ref_full), head_exact, body_exact)
            exact_groups[exact_key].append(i)

        # Assign primary / redundant for exact duplicates (same head+body+source_ref).
        for _key, idxs in exact_groups.items():
            if not idxs:
                continue
            def _readiness_score(rule_index: int) -> tuple[int, str]:
                r = logic_rows[rule_index]
                lrst = r.get("logic_readiness") or "reasoning_fallback"
                w = READINESS_W.get(lrst, 1)
                rid = r.get("rule_id") or str(rule_index)
                return (w, rid)

            idxs_sorted = sorted(idxs, key=lambda j: (-_readiness_score(j)[0], _readiness_score(j)[1], j))
            if len(idxs_sorted) == 1:
                j = idxs_sorted[0]
                logic_rows[j]["metadata"]["duplicate_role"] = "unique_variant"
                logic_rows[j]["metadata"]["is_primary_variant"] = True
                logic_rows[j]["metadata"]["variant_source"] = logic_rows[j]["metadata"].get("variant_source")
                logic_rows[j]["metadata"]["variant_source_detail"] = "unique_exact_signature"
            else:
                primary = idxs_sorted[0]
                for k_pos, j in enumerate(idxs_sorted):
                    if j == primary:
                        logic_rows[j]["metadata"]["duplicate_role"] = "primary_variant"
                        logic_rows[j]["metadata"]["is_primary_variant"] = True
                        logic_rows[j]["metadata"]["variant_source_detail"] = "primary_by_exact_head_body_source_ref"
                    else:
                        logic_rows[j]["metadata"]["duplicate_role"] = "redundant_variant"
                        logic_rows[j]["metadata"]["is_primary_variant"] = False
                        logic_rows[j]["metadata"]["variant_source_detail"] = "redundant_duplicate_by_exact_head_body_source_ref"

        def _iter_term_args(term: Any) -> list[Any]:
            if isinstance(term, dict) and "args" in term:
                args = term.get("args") or []
                return args if isinstance(args, list) else [args]
            return []

        def _has_bad_atom(v: Any) -> bool:
            if v is None:
                return True
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return False
            if isinstance(v, list):
                return any(_has_bad_atom(x) for x in v)
            s = str(v).strip()
            if not s:
                return True
            sl = s.lower()
            if sl in {"unknown", "null"}:
                return True
            if sl.startswith("unresolved_"):
                return True
            if sl.endswith("_"):
                return True
            if " " in s:
                return True
            return False

        exportable_ids: list[str] = []
        traceability_ids: list[str] = []
        for lr in logic_rows:
            meta = lr.setdefault("metadata", {})
            blockers = list(meta.get("export_blockers") or [])
            duplicate_role = meta.get("duplicate_role")
            fallback_kind = lr.get("fallback_kind")
            readiness = lr.get("logic_readiness")

            head = lr.get("head") or {}
            body = lr.get("body") or []
            aux = lr.get("auxiliary_clauses") or []

            # Hard blockers from structure quality.
            if _has_bad_atom(head.get("args") or []):
                blockers.append("head_has_unresolved_or_invalid_atom")
            for b in body:
                if isinstance(b, dict) and b.get("type") == "raw_text":
                    blockers.append("body_contains_raw_text_clause")
                if _has_bad_atom(_iter_term_args(b)):
                    blockers.append("body_has_unresolved_or_invalid_atom")
            for a in aux:
                h = a.get("head") if isinstance(a, dict) else None
                if _has_bad_atom(_iter_term_args(h)):
                    blockers.append("aux_has_unresolved_or_invalid_atom")

            # Semantic dedup for reasoning set.
            if duplicate_role == "redundant_variant":
                blockers.append("redundant_variant_not_selected_for_reasoning")

            if fallback_kind:
                blockers.append(f"fallback_kind:{fallback_kind}")

            # de-dup blockers (stable)
            if blockers:
                seen: set[str] = set()
                uniq: list[str] = []
                for b in blockers:
                    if b in seen:
                        continue
                    seen.add(b)
                    uniq.append(b)
                blockers = uniq

            # partial but logic-safe marker:
            hard_shape_block = any(
                b in {
                    "head_has_unresolved_or_invalid_atom",
                    "body_contains_raw_text_clause",
                    "body_has_unresolved_or_invalid_atom",
                    "aux_has_unresolved_or_invalid_atom",
                }
                for b in blockers
            )
            reasoning_safe_partial = (
                readiness == "reasoning_partial"
                and not hard_shape_block
                and fallback_kind is None
                and duplicate_role in ("primary_variant", "unique_variant")
            )

            # Final partition criteria (strict by user request):
            is_exportable_clean = (
                readiness == "reasoning_ready"
                and duplicate_role in ("primary_variant", "unique_variant")
                and fallback_kind is None
                and len(blockers) == 0
            )

            lr["reasoning_partition"] = "exportable_clean" if is_exportable_clean else "traceability_only"
            lr["selected_for_reasoning"] = bool(is_exportable_clean)
            meta["reasoning_safe_partial"] = bool(reasoning_safe_partial)
            meta["export_blockers"] = blockers
            meta["problog_exportable"] = bool(is_exportable_clean)

            rid = lr.get("rule_id")
            if isinstance(rid, str):
                if is_exportable_clean:
                    exportable_ids.append(rid)
                else:
                    traceability_ids.append(rid)

        if out_problog and prob_lines:
            header = (
                "% Neuro-symbolic rulebase — ProbLog-style view\n"
                f"% source_seed: {_relative_display_path(xlsx_path)}\n"
            )
            if vpath:
                header += f"% vocabulary: {_relative_display_path(Path(vpath))}\n"
            out_problog.write_text(header + "\n".join(prob_lines), encoding="utf-8")

    payload = {
        "version": 3,
        "logic_ir_schema": "rulebase_logic_ir_v1",
        "source_file": _relative_display_path(xlsx_path),
        "vocabulary_file": _relative_display_path(Path(vpath))
        if vpath and Path(vpath).exists()
        else None,
        "rule_count": n,
        "rule_type_to_logic_form": RULE_TYPE_TO_LOGIC_FORM,
        "rules_exportable_clean_count": len(exportable_ids),
        "rules_traceability_only_count": len(traceability_ids),
        "rules_exportable_clean_ids": exportable_ids,
        "rules_traceability_only_ids": traceability_ids,
        "rules": logic_rows,
    }
    out_logic_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    stats["vocabulary_loaded"] = bool(idx)
    return n, n, stats


__all__ = [
    "RULE_TYPE_TO_LOGIC_FORM",
    "JSONL_BLOCKS",
    "row_to_jsonl_object",
    "row_to_logic_record",
    "build_rich_jsonl_object",
    "row_to_problog_clause",
    "export_rulebase_formats",
    "build_logic_ir_record",
]
