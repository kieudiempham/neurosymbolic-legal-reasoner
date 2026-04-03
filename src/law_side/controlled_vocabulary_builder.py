"""
Build controlled vocabulary tables from rulebase_seed.xlsx (read-only).

Outputs Excel with sheets: predicate, object, effect, entity, metric.
See docs/ontology/controlled_vocabulary_spec.md.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


def _cell(v: Any) -> str | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    return s if s else None


def strip_vi_accents(s: str) -> str:
    s = s.replace("đ", "d").replace("Đ", "d")
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def to_snake_id(text: str) -> str:
    """Stable snake_case id from Vietnamese or Latin text."""
    t = strip_vi_accents(text.lower().strip())
    t = re.sub(r"[^a-z0-9]+", "_", t)
    t = re.sub(r"_+", "_", t).strip("_")
    return t or "unknown"


def _agg_rule_ids(series: list[str], limit: int = 5) -> str:
    u: list[str] = []
    for x in series:
        if x and x not in u:
            u.append(x)
        if len(u) >= limit:
            break
    return "; ".join(u)


def _score_to_confidence(score: int) -> str:
    """Map 0..100 score to do_tin_cay label."""
    if score >= 72:
        return "cao"
    if score >= 48:
        return "trung_binh"
    return "thap"


def _predicate_qa(
    *,
    has_typed_predicate: bool,
    predicate_family: str,
    canon_len: int,
    n_rule_types: int,
    max_rt_share: float,
) -> tuple[str, str]:
    """
    Heuristic QA for predicate rows.

    can_ra_soat: 'co' = nên rà soát tay; 'khong' = heuristic ổn định hơn.
    do_tin_cay: cao | trung_binh | thap (độ tin cậy gán tự động).

    Rules (subtract from base score 100):
    - Không có typed_predicate trong nhóm: -42
    - predicate_family == khac: -28
    - canon quá ngắn (< 12 ký tự): -18
    - Nhiều rule_type khác nhau (>=3 loại có mặt): -12
    - Phân bố rule_type phẳng (max share < 0.55 khi >=2 loại): -15
    """
    score = 100
    if not has_typed_predicate:
        score -= 42
    if predicate_family == "khac":
        score -= 28
    if canon_len < 12:
        score -= 18
    if n_rule_types >= 3:
        score -= 12
    if n_rule_types >= 2 and max_rt_share < 0.55:
        score -= 15
    conf = _score_to_confidence(score)
    needs_review = score < 58 or not has_typed_predicate or (predicate_family == "khac" and canon_len < 16)
    can_ra_soat = "co" if needs_review else "khong"
    if can_ra_soat == "khong" and conf == "thap":
        conf = "trung_binh"
    return can_ra_soat, conf


def _object_effect_qa(
    *,
    n_raw_variants: int,
    canon_len: int,
    max_raw_len: int,
    family_is_khac: bool,
) -> tuple[str, str]:
    """
    QA for object / effect aggregation rows.

    - Nhiều biến thể gốc trùng slug: -30 (>=8) / -18 (>=5)
    - Canon quá ngắn: -22 (<6)
    - Một dòng gốc quá dài (câu chứ không phải cụm): -25 (>180)
    - family == khac: -15
    """
    score = 100
    if n_raw_variants >= 8:
        score -= 30
    elif n_raw_variants >= 5:
        score -= 18
    if canon_len < 6:
        score -= 22
    if max_raw_len > 180:
        score -= 25
    if family_is_khac:
        score -= 15
    conf = _score_to_confidence(score)
    needs_review = score < 55 or n_raw_variants >= 6 or max_raw_len > 220
    can_ra_soat = "co" if needs_review else "khong"
    if can_ra_soat == "khong" and conf == "thap":
        conf = "trung_binh"
    return can_ra_soat, conf


def _entity_qa(
    *,
    n_raw_variants: int,
    canon_len: int,
    max_raw_len: int,
) -> tuple[str, str]:
    """QA for subject / authority / scope rows."""
    score = 100
    if n_raw_variants >= 7:
        score -= 32
    elif n_raw_variants >= 4:
        score -= 18
    if canon_len < 4:
        score -= 28
    if max_raw_len > 120:
        score -= 20
    conf = _score_to_confidence(score)
    needs_review = score < 52 or n_raw_variants >= 5 or canon_len < 3
    can_ra_soat = "co" if needs_review else "khong"
    if can_ra_soat == "khong" and conf == "thap":
        conf = "trung_binh"
    return can_ra_soat, conf


def _metric_qa(
    *,
    metric_is_unknown: bool,
    unit_missing: bool,
    n_raw_labels: int,
) -> tuple[str, str]:
    """QA for threshold metric rows."""
    score = 100
    if metric_is_unknown:
        score -= 45
    if unit_missing:
        score -= 22
    if n_raw_labels >= 4:
        score -= 20
    elif n_raw_labels >= 2:
        score -= 10
    conf = _score_to_confidence(score)
    needs_review = score < 55 or metric_is_unknown
    can_ra_soat = "co" if needs_review else "khong"
    if can_ra_soat == "khong" and conf == "thap":
        conf = "trung_binh"
    return can_ra_soat, conf


def build_predicate_vocab(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    # canonical from column or from hanh_vi_phap_ly
    work = df.copy()
    work["_canon"] = work["canonical_predicate"].map(_cell)
    work["_hv"] = work["hanh_vi_phap_ly"].map(_cell)
    work["_pc"] = work["_canon"].where(
        work["_canon"].notna() & (work["_canon"].astype(str).str.strip() != ""),
        work["_hv"].map(lambda x: to_snake_id(x) if x else None),
    )
    work = work[work["_pc"].notna()]

    grouped = work.groupby("_pc", dropna=False)
    for canon, g in grouped:
        if not canon or str(canon) == "nan":
            continue
        fam = g["predicate_family"].dropna().astype(str).str.strip()
        fam = fam[fam != ""]
        predicate_family = fam.mode().iloc[0] if len(fam) else _infer_family(str(canon))

        typed_modes = g["typed_predicate"].dropna().astype(str).str.strip()
        typed_modes = typed_modes[typed_modes != ""]
        rt = g["rule_type"].dropna().astype(str).str.strip().mode()
        rule_type_hint = rt.iloc[0] if len(rt) else "unknown"
        predicate_typed = (
            typed_modes.mode().iloc[0]
            if len(typed_modes)
            else f"{rule_type_hint}:{canon}"
        )

        gs = g["grounded_summary"].map(_cell).dropna()
        mo_ta_ngan = ""
        if len(gs):
            mo_ta_ngan = str(gs.iloc[0])[:200]
        else:
            hv = g["hanh_vi_phap_ly"].map(_cell).dropna()
            if len(hv):
                mo_ta_ngan = str(hv.iloc[0])[:200]

        rt_vc = g["rule_type"].value_counts()
        rt_dist = rt_vc.head(5)
        khi_nao = "; ".join(f"{k}({v})" for k, v in rt_dist.items())
        n_rule_types = int(len(rt_vc))
        max_rt_share = float(rt_vc.iloc[0] / len(g)) if len(g) and len(rt_vc) else 1.0
        can_ra_soat, do_tin_cay = _predicate_qa(
            has_typed_predicate=len(typed_modes) > 0,
            predicate_family=str(predicate_family),
            canon_len=len(str(canon)),
            n_rule_types=n_rule_types,
            max_rt_share=max_rt_share,
        )

        rows.append(
            {
                "predicate_family": predicate_family,
                "predicate_canonical": str(canon),
                "predicate_typed": predicate_typed,
                "mo_ta_ngan": mo_ta_ngan,
                "khi_nao_dung": khi_nao,
                "vi_du_rule_id": _agg_rule_ids(g["rule_id"].astype(str).tolist()),
                "can_ra_soat": can_ra_soat,
                "do_tin_cay": do_tin_cay,
            }
        )
    return pd.DataFrame(rows)


def _infer_family(canon: str) -> str:
    for prefix, fam in (
        ("dang_ky", "dang_ky"),
        ("cap_giay", "cap_giay"),
        ("thu_hoi", "thu_hoi"),
        ("thong_bao", "thong_bao"),
        ("cap_nhat", "cap_nhat"),
        ("nop_ho_so", "nop_ho_so"),
        ("ap_dung", "ap_dung"),
    ):
        if prefix in canon:
            return fam
    return "khac"


def _object_family_from_canon(obj: str) -> str:
    o = obj.lower()
    if any(x in o for x in ("ho_so", "ban", "giay", "mau", "bieu")):
        return "ho_so_tai_lieu"
    if any(x in o for x in ("von", "gop", "phan_von")):
        return "von_gop_von"
    if any(x in o for x in ("co_phan", "co_dong", "thanh_vien")):
        return "co_phan_thanh_vien"
    if any(x in o for x in ("giay_chung_nhan", "gcn")):
        return "giay_chung_nhan"
    return "khac"


def build_object_vocab(df: pd.DataFrame) -> pd.DataFrame:
    canon_to_raws: dict[str, set[str]] = defaultdict(set)
    canon_to_rules: dict[str, list[str]] = defaultdict(list)

    def add(raw: str | None, rid: str) -> None:
        if not raw or len(raw) < 2:
            return
        c = to_snake_id(raw)
        if len(c) < 3:
            return
        canon_to_raws[c].add(raw[:300])
        if rid not in canon_to_rules[c]:
            canon_to_rules[c].append(rid)

    for _, r in df.iterrows():
        rid = str(r.get("rule_id", ""))
        add(_cell(r.get("doi_tuong_hanh_vi")), rid)
        tp = _cell(r.get("thanh_phan_ho_so"))
        if tp:
            for part in re.split(r"[;；]\s*", tp):
                add(part.strip(), rid)

    rows = []
    for canon, raws in sorted(canon_to_raws.items(), key=lambda x: -len(x[1])):
        fam = _object_family_from_canon(canon)
        bieu_hien = " | ".join(sorted(raws)[:4])
        if len(raws) > 4:
            bieu_hien += " | …"
        max_raw_len = max((len(x) for x in raws), default=0)
        can_ra_soat, do_tin_cay = _object_effect_qa(
            n_raw_variants=len(raws),
            canon_len=len(canon),
            max_raw_len=max_raw_len,
            family_is_khac=(fam == "khac"),
        )
        rows.append(
            {
                "object_family": fam,
                "object_canonical": canon,
                "bieu_hien_goc_thuong_gap": bieu_hien[:500],
                "mo_ta_ngan": f"Đối tượng/hồ sơ gom về id `{canon}` ({len(raws)} biến thể gốc).",
                "vi_du_rule_id": _agg_rule_ids(canon_to_rules[canon]),
                "can_ra_soat": can_ra_soat,
                "do_tin_cay": do_tin_cay,
            }
        )
    return pd.DataFrame(rows)


def _effect_family(canon: str) -> str:
    c = canon.lower()
    if c.startswith("duoc_"):
        return "tich_cuc_duoc"
    if c.startswith("bi_"):
        return "tieu_cuc_bi"
    if c.startswith("phai_"):
        return "nghia_vu_phai"
    if "cap_giay" in c or "duoc_cap" in c:
        return "cap_giay"
    if "thu_hoi" in c:
        return "thu_hoi"
    if "cap_nhat" in c or "csdl" in c:
        return "cap_nhat_du_lieu"
    if "cong_bo" in c:
        return "cong_bo"
    return "khac"


def build_effect_vocab(df: pd.DataFrame) -> pd.DataFrame:
    canon_to_raws: dict[str, set[str]] = defaultdict(set)
    canon_to_rules: dict[str, list[str]] = defaultdict(list)

    def add(text: str | None, rid: str) -> None:
        if not text or len(text) < 3:
            return
        c = to_snake_id(text)
        if len(c) < 4:
            return
        canon_to_raws[c].add(text[:400])
        if rid not in canon_to_rules[c]:
            canon_to_rules[c].append(rid)

    for _, r in df.iterrows():
        rid = str(r.get("rule_id", ""))
        add(_cell(r.get("he_qua_phap_ly")), rid)
        add(_cell(r.get("ket_qua_thu_tuc")), rid)

    rows = []
    for canon, raws in sorted(canon_to_raws.items(), key=lambda x: -len(x[1])):
        fam = _effect_family(canon)
        bieu_hien = " | ".join(sorted(raws)[:3])
        max_raw_len = max((len(x) for x in raws), default=0)
        can_ra_soat, do_tin_cay = _object_effect_qa(
            n_raw_variants=len(raws),
            canon_len=len(canon),
            max_raw_len=max_raw_len,
            family_is_khac=(fam == "khac"),
        )
        rows.append(
            {
                "effect_family": fam,
                "effect_canonical": canon,
                "bieu_hien_goc_thuong_gap": bieu_hien[:500],
                "mo_ta_ngan": f"Hậu quả / kết quả thủ tục gom về `{canon}`.",
                "vi_du_rule_id": _agg_rule_ids(canon_to_rules[canon]),
                "can_ra_soat": can_ra_soat,
                "do_tin_cay": do_tin_cay,
            }
        )
    return pd.DataFrame(rows)


def build_entity_vocab(df: pd.DataFrame) -> pd.DataFrame:
    agg: dict[tuple[str, str], dict[str, Any]] = {}

    def add_row(kind: str, raw: str | None, rid: str) -> None:
        if not raw or len(raw) < 2:
            return
        cname = to_snake_id(raw)
        if len(cname) < 2:
            return
        k = (kind, cname)
        if k not in agg:
            agg[k] = {
                "entity_kind": kind,
                "canonical_name": cname,
                "_raws": set(),
                "_rids": [],
            }
        agg[k]["_raws"].add(raw[:400])
        if rid and rid not in agg[k]["_rids"]:
            agg[k]["_rids"].append(rid)

    for _, r in df.iterrows():
        rid = str(r.get("rule_id", ""))
        for val, kind in (
            (_cell(r.get("chu_the")), "subject"),
            (_cell(r.get("loai_chu_the")), "subject_type"),
            (_cell(r.get("vai_tro_chu_the")), "subject_role"),
            (_cell(r.get("co_quan_tiep_nhan")), "authority"),
            (_cell(r.get("co_quan_xu_ly")), "authority"),
            (_cell(r.get("pham_vi_ap_dung")), "scope"),
        ):
            add_row(kind, val, rid)

    rows = []
    for k, v in sorted(agg.items(), key=lambda x: (-len(x[1]["_raws"]), x[0][0])):
        raws_set = v["_raws"]
        raws = " | ".join(sorted(raws_set)[:6])
        if len(raws_set) > 6:
            raws += " | …"
        max_raw_len = max((len(x) for x in raws_set), default=0)
        can_ra_soat, do_tin_cay = _entity_qa(
            n_raw_variants=len(raws_set),
            canon_len=len(v["canonical_name"]),
            max_raw_len=max_raw_len,
        )
        rows.append(
            {
                "entity_kind": v["entity_kind"],
                "canonical_name": v["canonical_name"],
                "raw_variants": raws[:800],
                "mo_ta_ngan": f"Gom {len(raws_set)} biến thể gốc → `{v['canonical_name']}`.",
                "vi_du_rule_id": _agg_rule_ids(v["_rids"], limit=8),
                "can_ra_soat": can_ra_soat,
                "do_tin_cay": do_tin_cay,
            }
        )
    return pd.DataFrame(rows)


def build_metric_vocab(df: pd.DataFrame) -> pd.DataFrame:
    sub = df[df["rule_type"] == "quy_tac_nguong_dinh_luong"].copy()
    if sub.empty:
        sub = df

    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    raw_by_mc: dict[str, set[str]] = defaultdict(set)

    for _, r in sub.iterrows():
        m = _cell(r.get("ten_chi_so"))
        u = _cell(r.get("don_vi_nguong"))
        if not m and not u:
            continue
        mc = to_snake_id(m) if m else "unknown_metric"
        uc = to_snake_id(u) if u else ""
        groups[(mc, uc)].append(str(r.get("rule_id", "")))
        if m:
            raw_by_mc[mc].add(m)

    rows = []
    for (mc, uc), rids in sorted(groups.items(), key=lambda x: -len(x[1])):
        rvs = " | ".join(sorted(raw_by_mc.get(mc, set()))[:6])
        n_raw_labels = len(raw_by_mc.get(mc, set()))
        can_ra_soat, do_tin_cay = _metric_qa(
            metric_is_unknown=(mc == "unknown_metric"),
            unit_missing=(uc == ""),
            n_raw_labels=n_raw_labels,
        )
        rows.append(
            {
                "metric_canonical": mc,
                "raw_variants": rvs[:500],
                "unit_canonical": uc,
                "mo_ta_ngan": f"Chỉ số `{mc}`; đơn vị `{uc or 'khong_ro'}`.",
                "vi_du_rule_id": _agg_rule_ids(rids),
                "can_ra_soat": can_ra_soat,
                "do_tin_cay": do_tin_cay,
            }
        )
    return pd.DataFrame(rows)


def write_controlled_vocabulary_excel(
    rulebase_path: Path,
    out_path: Path,
    predicate_lexicon_path: Path | None = None,
) -> None:
    df = pd.read_excel(rulebase_path)

    pred_df = build_predicate_vocab(df)
    obj_df = build_object_vocab(df)
    eff_df = build_effect_vocab(df)
    ent_df = build_entity_vocab(df)
    met_df = build_metric_vocab(df)

    if predicate_lexicon_path and predicate_lexicon_path.exists():
        lex = pd.read_excel(predicate_lexicon_path)
        existing = set(pred_df["predicate_canonical"].astype(str))
        extra_rows = []
        for _, r in lex.iterrows():
            hc = _cell(r.get("hanh_vi_chuan"))
            if not hc or hc in existing:
                continue
            extra_rows.append(
                {
                    "predicate_family": _cell(r.get("nhom_hanh_vi")) or "tu_lexicon",
                    "predicate_canonical": hc,
                    "predicate_typed": _cell(r.get("hanh_vi_chuan_chi_tiet")) or hc,
                    "mo_ta_ngan": f"Tham chiếu predicate_lexicon; surface: {r.get('surface_form', '')}"[:200],
                    "khi_nao_dung": "tham_chieu_lexicon_chua_xuat_hien_trong_seed",
                    "vi_du_rule_id": "",
                    "can_ra_soat": "co",
                    "do_tin_cay": "thap",
                }
            )
        if extra_rows:
            pred_df = pd.concat([pred_df, pd.DataFrame(extra_rows)], ignore_index=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        pred_df.to_excel(w, sheet_name="predicate_vocabulary", index=False)
        obj_df.to_excel(w, sheet_name="object_vocabulary", index=False)
        eff_df.to_excel(w, sheet_name="effect_vocabulary", index=False)
        ent_df.to_excel(w, sheet_name="subject_authority_scope", index=False)
        met_df.to_excel(w, sheet_name="metric_vocabulary", index=False)


__all__ = [
    "to_snake_id",
    "build_predicate_vocab",
    "build_object_vocab",
    "build_effect_vocab",
    "build_entity_vocab",
    "build_metric_vocab",
    "write_controlled_vocabulary_excel",
]
