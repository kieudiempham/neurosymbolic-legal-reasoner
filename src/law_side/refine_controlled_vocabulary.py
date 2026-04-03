"""
Tinh chỉnh controlled_vocabulary.xlsx: tách effect/exception, lọc object/effect,
bổ sung metric và subject_authority_scope — không đụng rulebase_seed.

Chạy: python scripts/refine_controlled_vocabulary.py
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from law_side.controlled_vocabulary_builder import to_snake_id


def _cell(v: Any) -> str | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    return s if s else None


# --- Tách phần điều kiện / ngoại lệ khỏi effect_canonical (slug) ---
_EFFECT_TRUNC_MARKERS: tuple[tuple[str, str], ...] = (
    ("_tru_truong_hop", "exception"),
    ("_ngoai_tru_", "exception"),
    ("_neu_", "condition"),
    ("_khi_", "condition"),
    ("_doi_voi_", "scope"),
    ("_trong_thoi_han_", "condition"),
    ("_ke_tu_", "condition"),
    ("_theo_yeu_cau_", "condition"),
    ("_gia_su_", "condition"),
    ("_tru_khi_", "condition"),
)


def split_effect_exception_condition(effect_canonical: str) -> tuple[str, list[tuple[str, str]]]:
    """
    Trả về (base_canonical, [(kind, tail_snippet), ...]).
    tail_snippet là phần slug sau marker (để notes / sheet phụ).
    """
    s = effect_canonical.strip()
    fragments: list[tuple[str, str]] = []
    best_idx: int | None = None
    best_marker: str | None = None
    best_kind: str = "mixed"

    for marker, kind in _EFFECT_TRUNC_MARKERS:
        if marker in s:
            idx = s.index(marker)
            if idx >= 20 and (best_idx is None or idx < best_idx):
                best_idx = idx
                best_marker = marker
                best_kind = kind

    if best_idx is None or best_marker is None:
        return s, []

    base = s[:best_idx].rstrip("_")
    tail = s[best_idx:].lstrip("_")
    if len(base) < 10:
        return s, []

    fragments.append((best_kind, tail))
    return base, fragments


def refined_effect_family(canon: str) -> str:
    """Nhóm kết quả (outcome), không phản ánh hành động."""
    c = canon.lower()
    if "thu_hoi" in c:
        return "thu_hoi"
    if "cham_dut" in c and "hoat_dong" in c:
        return "cham_dut"
    if "chuyen_doi" in c:
        return "chuyen_doi"
    if "mat_tu_cach" in c or "khong_con_tu_cach" in c:
        return "mat_tu_cach"
    if "tro_thanh" in c and ("chu_so_huu" in c or "thanh_vien" in c):
        return "xac_lap_tu_cach"
    if "cong_bo" in c:
        return "cong_bo"
    if "dieu_chinh" in c:
        return "dieu_chinh"
    if "cap_nhat" in c or "csdl" in c or "co_so_du_lieu" in c:
        return "cap_nhat"
    if "duoc_cap" in c or "cap_giay" in c or c.startswith("duoc_"):
        return "cap_giay"
    if c.startswith("bi_"):
        return "tieu_cuc_bi"
    if c.startswith("phai_") and len(c) < 48:
        return "nghia_vu_phai"
    if c.startswith("khoi_phuc"):
        return "khoi_phuc"
    if "chap_thuan" in c[:20]:
        return "chap_thuan"
    return "khac"


def is_action_obligation_effect_slug(canon: str) -> bool:
    """Hành vi / thủ tục / nghĩa vụ — không phải outcome-state."""
    c = canon.lower()
    if canon.startswith("cong_ty_"):
        return True
    if canon.startswith("nguoi_") and any(
        x in c for x in ("nop_", "dang_ky_", "thuc_hien_", "gui_")
    ):
        return True
    if canon.startswith("co_quan_dang_ky_kinh_doanh_") and any(
        x in c
        for x in (
            "xem_xet",
            "trao_giay_tiep_nhan",
            "cap_thong_tin_duoc_luu",
            "ra_quyet_dinh",
            "gui_thong_tin",
        )
    ):
        return True
    if canon.startswith("co_quan_") and len(canon) > 95:
        return True
    if "cap_nhat_kip_thoi" in c or "theo_yeu_cau_cua" in c:
        return True
    return False


def should_drop_object_row(object_canonical: str) -> bool:
    """Condition / scope / discourse — không phải NP đối tượng."""
    c = object_canonical.lower()
    bad_prefix = (
        "khi_",
        "neu_",
        "tru_truong_hop",
        "ap_dung_",
        "phai_co_cac_giay",
        "trong_thoi_han_",
        "theo_quy_dinh",
        "truong_hop_",
        "doi_voi_",
        "dang_ky_thanh_lap",  # VP fragment
    )
    if any(c.startswith(p) for p in bad_prefix):
        return True
    bad_in = (
        "tru_truong_hop",
        "khi_dang_ky",
        "khi_thay_doi",
        "khi_ho_so",
        "khi_trinh",
        "ap_dung_doi_voi",
        "hop_dong_da_ky_voi_khach_hang",
    )
    if any(x in c for x in bad_in):
        return True
    if c.startswith("tru_") and "truong" in c:
        return True
    return False


def _merge_rule_ids(a: str, b: str, limit: int = 8) -> str:
    parts: list[str] = []
    for chunk in (a, b):
        for x in str(chunk).replace(";", ",").split(","):
            x = x.strip()
            if x and x not in parts:
                parts.append(x)
            if len(parts) >= limit:
                break
        if len(parts) >= limit:
            break
    return "; ".join(parts[:limit])


def _merge_raw_texts(a: str, b: str, limit: int = 8) -> str:
    """Gộp chuỗi mô tả / nhãn gốc (phân tách | hoặc ;)."""
    parts: list[str] = []
    for chunk in (a, b):
        for piece in re.split(r"\s*[|;]\s*", str(chunk)):
            x = piece.strip()
            if x and x not in parts:
                parts.append(x)
            if len(parts) >= limit:
                return " | ".join(parts)
    return " | ".join(parts)


def _dedupe_effects(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    groups: dict[str, dict[str, Any]] = {}
    for _, r in df.iterrows():
        k = str(r["effect_canonical"])
        if k not in groups:
            groups[k] = r.to_dict()
            continue
        g = groups[k]
        g["bieu_hien_goc_thuong_gap"] = _merge_rule_ids(
            str(g.get("bieu_hien_goc_thuong_gap", "")),
            str(r.get("bieu_hien_goc_thuong_gap", "")),
            limit=6,
        )
        g["vi_du_rule_id"] = _merge_rule_ids(
            str(g.get("vi_du_rule_id", "")),
            str(r.get("vi_du_rule_id", "")),
            limit=8,
        )
        g["notes"] = _merge_notes(str(g.get("notes", "")), str(r.get("notes", "")))
    out = pd.DataFrame(list(groups.values()))
    return out.sort_values("effect_canonical").reset_index(drop=True)


def _merge_notes(a: str, b: str) -> str:
    xs = [x.strip() for x in f"{a}; {b}".split(";") if x.strip()]
    seen: set[str] = set()
    out: list[str] = []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return "; ".join(out[:6])


STATIC_METRIC_ROWS: list[dict[str, str]] = [
    {"metric_canonical": "so_thanh_vien", "unit_canonical": "thanh_vien", "mo_ta_ngan": "Số lượng thành viên (domain DN)."},
    {"metric_canonical": "so_co_dong", "unit_canonical": "co_dong", "mo_ta_ngan": "Số cổ đông."},
    {"metric_canonical": "ty_le_so_huu_co_phan", "unit_canonical": "phan_tram", "mo_ta_ngan": "Tỷ lệ sở hữu cổ phần."},
    {"metric_canonical": "ty_le_von_gop", "unit_canonical": "phan_tram", "mo_ta_ngan": "Tỷ lệ vốn góp."},
    {"metric_canonical": "thoi_han_xu_ly_ho_so", "unit_canonical": "ngay_lam_viec", "mo_ta_ngan": "Thời hạn xử lý hồ sơ."},
    {"metric_canonical": "thoi_han_dang_ky_chuyen_doi", "unit_canonical": "ngay", "mo_ta_ngan": "Thời hạn đăng ký chuyển đổi."},
    {"metric_canonical": "thoi_han_thanh_toan", "unit_canonical": "ngay", "mo_ta_ngan": "Thời hạn thanh toán."},
    {"metric_canonical": "thoi_han_gop_von", "unit_canonical": "ngay", "mo_ta_ngan": "Thời hạn góp vốn."},
    {"metric_canonical": "thoi_han_thong_bao", "unit_canonical": "ngay", "mo_ta_ngan": "Thời hạn thông báo."},
    {"metric_canonical": "thoi_han_cap_giay", "unit_canonical": "ngay_lam_viec", "mo_ta_ngan": "Thời hạn cấp giấy."},
    {"metric_canonical": "thoi_han_cong_bo", "unit_canonical": "ngay", "mo_ta_ngan": "Thời hạn công bố."},
]

STATIC_ENTITY_ROWS: list[dict[str, str]] = [
    {"entity_kind": "subject", "canonical_name": "cong_ty", "raw_variants": "công ty"},
    {"entity_kind": "subject", "canonical_name": "doanh_nghiep", "raw_variants": "doanh nghiệp"},
    {"entity_kind": "subject", "canonical_name": "cong_ty_co_phan", "raw_variants": "công ty cổ phần"},
    {"entity_kind": "subject", "canonical_name": "cong_ty_tnhh_mot_thanh_vien", "raw_variants": "công ty TNHH một thành viên"},
    {"entity_kind": "subject", "canonical_name": "cong_ty_tnhh_hai_thanh_vien_tro_len", "raw_variants": "công ty TNHH hai thành viên trở lên"},
    {"entity_kind": "subject", "canonical_name": "cong_ty_hop_danh", "raw_variants": "công ty hợp danh"},
    {"entity_kind": "subject", "canonical_name": "doanh_nghiep_tu_nhan", "raw_variants": "doanh nghiệp tư nhân"},
    {"entity_kind": "subject", "canonical_name": "co_dong_sang_lap", "raw_variants": "cổ đông sáng lập"},
    {"entity_kind": "subject", "canonical_name": "co_dong", "raw_variants": "cổ đông"},
    {"entity_kind": "subject", "canonical_name": "thanh_vien_hop_danh", "raw_variants": "thành viên hợp danh"},
    {"entity_kind": "subject", "canonical_name": "thanh_vien_gop_von", "raw_variants": "thành viên góp vốn"},
    {"entity_kind": "subject", "canonical_name": "nguoi_dai_dien_theo_phap_luat", "raw_variants": "người đại diện theo pháp luật"},
    {"entity_kind": "subject", "canonical_name": "nguoi_mua_doanh_nghiep_tu_nhan", "raw_variants": "người mua doanh nghiệp tư nhân"},
    {"entity_kind": "subject", "canonical_name": "chu_doanh_nghiep_tu_nhan", "raw_variants": "chủ doanh nghiệp tư nhân"},
    {"entity_kind": "authority", "canonical_name": "co_quan_dang_ky_kinh_doanh", "raw_variants": "cơ quan đăng ký kinh doanh"},
    {"entity_kind": "authority", "canonical_name": "cong_thong_tin_quoc_gia_ve_dang_ky_doanh_nghiep", "raw_variants": "Cổng thông tin quốc gia về đăng ký doanh nghiệp"},
    {"entity_kind": "authority", "canonical_name": "co_so_du_lieu_quoc_gia_ve_dang_ky_doanh_nghiep", "raw_variants": "Cơ sở dữ liệu quốc gia về đăng ký doanh nghiệp"},
    {"entity_kind": "scope", "canonical_name": "ap_dung_cho_cong_ty_co_phan", "raw_variants": "áp dụng cho công ty cổ phần"},
    {"entity_kind": "scope", "canonical_name": "ap_dung_cho_cong_ty_tnhh_mot_thanh_vien", "raw_variants": "áp dụng cho công ty TNHH một thành viên"},
    {"entity_kind": "scope", "canonical_name": "ap_dung_cho_cong_ty_tnhh_hai_thanh_vien_tro_len", "raw_variants": "áp dụng cho công ty TNHH hai thành viên trở lên"},
    {"entity_kind": "scope", "canonical_name": "ap_dung_cho_cong_ty_hop_danh", "raw_variants": "áp dụng cho công ty hợp danh"},
    {"entity_kind": "scope", "canonical_name": "ap_dung_cho_doanh_nghiep_tu_nhan", "raw_variants": "áp dụng cho doanh nghiệp tư nhân"},
    {"entity_kind": "scope", "canonical_name": "ap_dung_cho_co_dong_sang_lap", "raw_variants": "áp dụng cho cổ đông sáng lập"},
    {"entity_kind": "scope", "canonical_name": "ap_dung_cho_thanh_vien_hop_danh", "raw_variants": "áp dụng cho thành viên hợp danh"},
    {"entity_kind": "scope", "canonical_name": "ap_dung_cho_thanh_vien_gop_von", "raw_variants": "áp dụng cho thành viên góp vốn"},
]


def refine_controlled_vocabulary_workbook(
    vocab_path: Path,
    rulebase_seed_path: Path,
    out_path: Path | None = None,
) -> None:
    out_path = out_path or vocab_path
    pred = pd.read_excel(vocab_path, sheet_name="predicate_vocabulary")
    obj = pd.read_excel(vocab_path, sheet_name="object_vocabulary")
    eff = pd.read_excel(vocab_path, sheet_name="effect_vocabulary")
    ent = pd.read_excel(vocab_path, sheet_name="subject_authority_scope")
    met = pd.read_excel(vocab_path, sheet_name="metric_vocabulary")

    seed = pd.read_excel(rulebase_seed_path)

    fragments_rows: list[dict[str, Any]] = []
    predicates_extra: list[dict[str, Any]] = []

    # --- Effects: strip + reclassify ---
    new_eff_rows: list[dict[str, Any]] = []
    for _, r in eff.iterrows():
        canon = str(r["effect_canonical"]).strip()
        base, frags = split_effect_exception_condition(canon)
        raw_bieu = str(r.get("bieu_hien_goc_thuong_gap", ""))
        rid = str(r.get("vi_du_rule_id", ""))

        for kind, tail in frags:
            fragments_rows.append(
                {
                    "fragment_kind": kind,
                    "split_from": "effect_vocabulary",
                    "original_canonical": canon,
                    "tail_slug": tail[:400],
                    "raw_context": raw_bieu[:500],
                    "notes": "tach_exception_condition_khoi_effect",
                    "vi_du_rule_id": rid[:500],
                }
            )

        target = base if frags else canon

        if is_action_obligation_effect_slug(target):
            predicates_extra.append(
                {
                    "predicate_family": "hanh_vi",
                    "predicate_canonical": target,
                    "predicate_typed": f"chuyen_tu_effect:{target}",
                    "mo_ta_ngan": f"Diễn đạt hành vi/thủ tục (đưa khỏi effect). Gốc: `{canon}`."[:220],
                    "khi_nao_dung": "mapping_hanh_vi_khong_phai_ket_qua",
                    "vi_du_rule_id": rid,
                    "can_ra_soat": "co",
                    "do_tin_cay": "trung_binh",
                    "notes": "chuyen_action_ra_khoi_effect",
                }
            )
            continue

        if frags:
            notes = "tach_exception_khoi_effect" if any(f[0] == "exception" for f in frags) else "tach_condition_khoi_effect"
            if any(f[0] == "exception" for f in frags) and any(f[0] == "condition" for f in frags):
                notes = "tach_exception_khoi_effect; tach_condition_khoi_effect"
        else:
            notes = str(r.get("notes", "") or "")

        new_eff_rows.append(
            {
                "effect_family": refined_effect_family(target),
                "effect_canonical": target,
                "bieu_hien_goc_thuong_gap": raw_bieu[:500],
                "mo_ta_ngan": f"Kết quả/hậu quả (đã tách điều kiện/ngoại lệ nếu có). `{target}`."[:240],
                "vi_du_rule_id": rid,
                "can_ra_soat": "co" if frags else r.get("can_ra_soat", "khong"),
                "do_tin_cay": "trung_binh" if frags else r.get("do_tin_cay", "cao"),
                "notes": _merge_notes(notes, str(r.get("notes", "") or "")),
            }
        )

    eff2 = _dedupe_effects(pd.DataFrame(new_eff_rows))

    # --- Objects: drop cue/condition ---
    obj_kept: list[dict[str, Any]] = []
    for _, r in obj.iterrows():
        cn = str(r["object_canonical"]).strip()
        if should_drop_object_row(cn):
            fragments_rows.append(
                {
                    "fragment_kind": "discourse_or_condition",
                    "split_from": "object_vocabulary",
                    "original_canonical": cn,
                    "tail_slug": "",
                    "raw_context": str(r.get("bieu_hien_goc_thuong_gap", ""))[:500],
                    "notes": "loai_condition_hoac_scope_khoi_object",
                    "vi_du_rule_id": str(r.get("vi_du_rule_id", "")),
                }
            )
            continue
        row = r.to_dict()
        row["notes"] = str(row.get("notes", "") or "")
        obj_kept.append(row)
    obj2 = pd.DataFrame(obj_kept)

    # --- Predicates: merge extras ---
    if "notes" not in pred.columns:
        pred["notes"] = ""
    if predicates_extra:
        pe = pd.DataFrame(predicates_extra)
        for col in pred.columns:
            if col not in pe.columns:
                pe[col] = ""
        pe = pe.reindex(columns=list(pred.columns))
        pred2 = pd.concat([pred, pe], ignore_index=True)
        pred2 = pred2.drop_duplicates(subset=["predicate_canonical"], keep="first")
    else:
        pred2 = pred

    # --- Metrics: seed + static ---
    metric_keys: dict[tuple[str, str], dict[str, Any]] = {}
    for _, r in met.iterrows():
        mc = str(r["metric_canonical"]).strip()
        uc = str(r.get("unit_canonical", "") or "").strip()
        k = (mc, uc)
        if k not in metric_keys:
            metric_keys[k] = r.to_dict()

    for _, r in seed.iterrows():
        m = _cell(r.get("ten_chi_so"))
        u = _cell(r.get("don_vi_nguong"))
        if not m and not u:
            continue
        mc = to_snake_id(m) if m else "unknown_metric"
        uc = to_snake_id(u) if u else ""
        k = (mc, uc)
        rid = str(r.get("rule_id", ""))
        if k not in metric_keys:
            metric_keys[k] = {
                "metric_canonical": mc,
                "raw_variants": m or "",
                "unit_canonical": uc,
                "mo_ta_ngan": f"Chỉ số `{mc}`; đơn vị `{uc or 'khong_ro'}`.",
                "vi_du_rule_id": rid,
                "can_ra_soat": "co" if mc == "unknown_metric" else "khong",
                "do_tin_cay": "thap" if mc == "unknown_metric" else "cao",
                "notes": "bo_sung_metric",
            }
        else:
            ex = metric_keys[k]
            ex["raw_variants"] = _merge_raw_texts(str(ex.get("raw_variants", "")), m or "", limit=6)
            ex["vi_du_rule_id"] = _merge_rule_ids(str(ex.get("vi_du_rule_id", "")), rid, limit=8)
            ex["notes"] = _merge_notes(str(ex.get("notes", "")), "bo_sung_metric")

    for sm in STATIC_METRIC_ROWS:
        k = (sm["metric_canonical"], sm["unit_canonical"])
        if k not in metric_keys:
            metric_keys[k] = {
                "metric_canonical": sm["metric_canonical"],
                "raw_variants": sm["metric_canonical"].replace("_", " "),
                "unit_canonical": sm["unit_canonical"],
                "mo_ta_ngan": sm["mo_ta_ngan"],
                "vi_du_rule_id": "",
                "can_ra_soat": "khong",
                "do_tin_cay": "cao",
                "notes": "bo_sung_metric",
            }

    met2 = pd.DataFrame(list(metric_keys.values()))
    if "notes" not in met2.columns:
        met2["notes"] = ""

    # --- Entities: static + seed scan ---
    ent_keys: dict[tuple[str, str], dict[str, Any]] = {}
    for _, r in ent.iterrows():
        ek = (str(r["entity_kind"]), str(r["canonical_name"]))
        ent_keys[ek] = r.to_dict()

    for se in STATIC_ENTITY_ROWS:
        ek = (se["entity_kind"], se["canonical_name"])
        if ek not in ent_keys:
            ent_keys[ek] = {
                "entity_kind": se["entity_kind"],
                "canonical_name": se["canonical_name"],
                "raw_variants": se["raw_variants"],
                "mo_ta_ngan": f"Mục cốt lõi domain DN — `{se['canonical_name']}`.",
                "vi_du_rule_id": "",
                "can_ra_soat": "khong",
                "do_tin_cay": "cao",
                "notes": "bo_sung_subject_authority_scope",
            }

    for _, r in seed.iterrows():
        rid = str(r.get("rule_id", ""))
        for col, kind in (
            ("chu_the", "subject"),
            ("loai_chu_the", "subject_type"),
            ("vai_tro_chu_the", "subject_role"),
            ("co_quan_tiep_nhan", "authority"),
            ("co_quan_xu_ly", "authority"),
            ("pham_vi_ap_dung", "scope"),
        ):
            raw = _cell(r.get(col))
            if not raw:
                continue
            cname = to_snake_id(raw)
            if len(cname) < 2:
                continue
            ek = (kind, cname)
            if ek not in ent_keys:
                ent_keys[ek] = {
                    "entity_kind": kind,
                    "canonical_name": cname,
                    "raw_variants": raw[:400],
                    "mo_ta_ngan": f"Gom từ rulebase_seed (`{col}`).",
                    "vi_du_rule_id": rid,
                    "can_ra_soat": "khong",
                    "do_tin_cay": "cao",
                    "notes": "bo_sung_subject_authority_scope",
                }
            else:
                ex = ent_keys[ek]
                ex["raw_variants"] = _merge_raw_texts(str(ex.get("raw_variants", "")), raw, limit=6)[:800]
                ex["vi_du_rule_id"] = _merge_rule_ids(str(ex.get("vi_du_rule_id", "")), rid, limit=8)

    ent2 = pd.DataFrame(list(ent_keys.values()))

    frag_df = pd.DataFrame(fragments_rows) if fragments_rows else pd.DataFrame(
        columns=[
            "fragment_kind",
            "split_from",
            "original_canonical",
            "tail_slug",
            "raw_context",
            "notes",
            "vi_du_rule_id",
        ]
    )

    # Column order / ensure notes on sheets
    for df_, name in (
        (pred2, "predicate"),
        (obj2, "object"),
        (eff2, "effect"),
        (ent2, "entity"),
        (met2, "metric"),
    ):
        if "notes" not in df_.columns:
            df_["notes"] = ""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        pred2.to_excel(w, sheet_name="predicate_vocabulary", index=False)
        obj2.to_excel(w, sheet_name="object_vocabulary", index=False)
        eff2.to_excel(w, sheet_name="effect_vocabulary", index=False)
        ent2.to_excel(w, sheet_name="subject_authority_scope", index=False)
        met2.to_excel(w, sheet_name="metric_vocabulary", index=False)
        frag_df.to_excel(w, sheet_name="modifier_fragments", index=False)


__all__ = ["refine_controlled_vocabulary_workbook"]
