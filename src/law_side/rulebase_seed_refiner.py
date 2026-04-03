"""Post-process rulebase_seed.xlsx: dedup by legal content, structure thresholds, enrich slots."""

from __future__ import annotations

import hashlib
import re
from typing import Any

import pandas as pd

from law_side.legal_frame_fanout_enricher import (
    dossier_cues_in_text,
    extract_ket_qua_thu_tuc,
    extract_thanh_phan_ho_so,
    norm_space,
)

FINGERPRINT_COLS: tuple[str, ...] = (
    "doc_id",
    "source_ref",
    "rule_type",
    "chu_the",
    "dieu_kien_ap_dung",
    "hanh_vi_phap_ly",
    "doi_tuong_hanh_vi",
    "he_qua_phap_ly",
    "thoi_han_so",
    "don_vi_thoi_han",
    "moc_tinh_thoi_han",
    "thanh_phan_ho_so",
    "co_quan_tiep_nhan",
    "co_quan_xu_ly",
    "ngoai_le",
    "ten_chi_so",
    "toan_tu_so_sanh",
    "gia_tri_nguong",
    "ket_qua_thu_tuc",
    "canonical_predicate",
    "bieu_thuc_thoi_han",
)

_ABSTRACT_HE_QUA = frozenset(
    {
        "phải thực hiện",
        "được xử lý",
        "có kết quả",
        "theo quy định",
        "thực hiện theo quy định",
    }
)

_ABSTRACT_DOSSIER = re.compile(
    r"^(hồ\s+sơ\s+theo\s+quy\s+định|tài\s+liệu\s+liên\s+quan|giấy\s+tờ\s+cần\s+thiết|thành\s+phần\s+hồ\s+sơ)\s*$",
    flags=re.I | re.U,
)


def _s(v: Any) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    t = str(v).strip()
    return "" if t.lower() == "nan" else t


def content_fingerprint(row: pd.Series) -> str:
    parts = [_s(row.get(c)) for c in FINGERPRINT_COLS]
    return hashlib.sha256("\u241e".join(parts).encode("utf-8")).hexdigest()


def _nonempty_count(row: pd.Series, cols: list[str]) -> int:
    return sum(1 for c in cols if _s(row.get(c)))


def _score_keeper(row: pd.Series) -> float:
    """Higher = prefer keeping this row over duplicates."""
    key_cols = [
        "he_qua_phap_ly",
        "thanh_phan_ho_so",
        "ket_qua_thu_tuc",
        "ten_chi_so",
        "gia_tri_nguong",
        "gia_tri_tu",
        "gia_tri_den",
        "dieu_kien_ap_dung",
        "ngoai_le",
    ]
    score = float(_nonempty_count(row, key_cols) * 3)
    score += float(_nonempty_count(row, ["co_quan_xu_ly", "co_quan_tiep_nhan", "moc_tinh_thoi_han"]))
    gs = _s(row.get("grounded_summary"))
    score += min(len(gs), 350) / 70.0
    st = _s(row.get("source_text"))
    score += min(len(st), 500) / 125.0
    if gs.lower().startswith("ngưỡng/điều kiện định lượng:") and len(gs) < 55:
        score -= 2.0
    return score


def deduplicate_by_content(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_fp"] = df.apply(content_fingerprint, axis=1)
    keep_idx: list[int] = []
    merged_notes: dict[int, str] = {}
    for _, grp in df.groupby("_fp", sort=False):
        idxs = grp.index.tolist()
        if len(idxs) == 1:
            keep_idx.append(idxs[0])
            continue
        best_i = max(idxs, key=lambda i: _score_keeper(df.loc[i]))
        keep_idx.append(best_i)
        losers = [i for i in idxs if i != best_i]
        merged_ids = "|".join(sorted(_s(df.loc[i, "rule_id"]) for i in losers))[:1800]
        tag = "dedup_theo_noi_dung;giu_ban_day_du_hon"
        if merged_ids:
            tag += f";merged_rule_ids={merged_ids}"
        prev = _s(df.at[best_i, "notes"])
        parts = [p.strip() for p in prev.split(";") if p.strip()]
        for p in tag.split(";"):
            p = p.strip()
            if p and p not in parts:
                parts.append(p)
        merged_notes[best_i] = ";".join(parts)
    out = df.loc[sorted(keep_idx)].copy()
    for i, note in merged_notes.items():
        if i in out.index:
            out.at[i, "notes"] = note
    out = out.drop(columns=["_fp"], errors="ignore")
    return out.reset_index(drop=True)


def _merge_threshold(dst: dict[str, str], src: dict[str, str]) -> None:
    for k, v in src.items():
        if v and (not dst.get(k)):
            dst[k] = v


def infer_threshold_fields(text: str) -> dict[str, str]:
    """Best-effort extraction for quantitative rules (Vietnamese legal phrasing)."""
    raw = norm_space(text)
    if not raw:
        return {}
    t = raw.lower()
    out: dict[str, str] = {}

    m = re.search(
        r"ít nhất\s+(\d+)\s*%\s*(?:tổng\s+số\s+)?(?:cổ\s+phần\s+phổ\s+thông|cổ\s+phần)",
        raw,
        flags=re.I | re.U,
    )
    if m:
        _merge_threshold(
            out,
            {
                "ten_chi_so": "ty_le_so_huu_co_phan_pho_thong",
                "toan_tu_so_sanh": ">=",
                "gia_tri_nguong": m.group(1),
                "don_vi_nguong": "phan_tram",
            },
        )

    m2 = re.search(r"ít\s+nhất\s+(\d+)\s*%", raw, flags=re.I | re.U)
    if m2 and not out.get("gia_tri_nguong"):
        _merge_threshold(
            out,
            {
                "ten_chi_so": "ty_le",
                "toan_tu_so_sanh": ">=",
                "gia_tri_nguong": m2.group(1),
                "don_vi_nguong": "phan_tram",
            },
        )
        if "phiếu" in t and "biểu quyết" in t:
            out["ten_chi_so"] = "ty_le_phieu_bieu_quyet"

    m3 = re.search(r"(?:trên|lớn hơn)\s+(\d+)\s*%", raw, flags=re.I | re.U)
    if m3 and not out.get("gia_tri_nguong"):
        pct = m3.group(1)
        o = {"toan_tu_so_sanh": ">", "gia_tri_nguong": pct, "don_vi_nguong": "phan_tram"}
        if "vốn điều lệ" in t or "von dieu le" in t:
            o["ten_chi_so"] = "ty_le_von_dieu_le"
        else:
            o["ten_chi_so"] = "ty_le"
        _merge_threshold(out, o)

    m4 = re.search(r"(?:dưới|nhỏ hơn|không quá)\s+(\d+)\s*%", raw, flags=re.I | re.U)
    if m4 and not out.get("toan_tu_so_sanh"):
        o = {"toan_tu_so_sanh": "<=", "gia_tri_nguong": m4.group(1), "don_vi_nguong": "phan_tram", "ten_chi_so": "ty_le"}
        if "thành viên" in t:
            o["ten_chi_so"] = "ty_le_thanh_vien_so_huu"  # rare
        _merge_threshold(out, o)

    m5 = re.search(
        r"không\s+quá\s+(\d+)\s+(thành\s+viên|cổ\s+đông)", raw, flags=re.I | re.U
    )
    if m5:
        unit = "thanh_vien" if "thành" in m5.group(0).lower() else "co_dong"
        key = "so_thanh_vien" if unit == "thanh_vien" else "so_co_dong"
        _merge_threshold(
            out,
            {
                "ten_chi_so": key,
                "toan_tu_so_sanh": "<=",
                "gia_tri_nguong": m5.group(1),
                "don_vi_nguong": unit,
            },
        )

    m6 = re.search(
        r"ít\s+nhất\s+(\d+)\s+(cổ\s+đông|thành\s+viên)", raw, flags=re.I | re.U
    )
    if m6:
        unit = "co_dong" if "cổ" in m6.group(0).lower() else "thanh_vien"
        key = "so_co_dong" if unit == "co_dong" else "so_thanh_vien"
        _merge_threshold(
            out,
            {
                "ten_chi_so": key,
                "toan_tu_so_sanh": ">=",
                "gia_tri_nguong": m6.group(1),
                "don_vi_nguong": unit,
            },
        )

    m7 = re.search(
        r"từ\s+0*(\d+)\s+đến\s+0*(\d+)\s+(thành\s+viên|cổ\s+đông)", raw, flags=re.I | re.U
    )
    if m7:
        unit = "thanh_vien" if "thành" in m7.group(0).lower() else "co_dong"
        _merge_threshold(
            out,
            {
                "ten_chi_so": "so_thanh_vien" if unit == "thanh_vien" else "so_co_dong",
                "gia_tri_tu": m7.group(1),
                "gia_tri_den": m7.group(2),
                "don_vi_nguong": unit,
                "kieu_khoang": "dong",
            },
        )

    m8 = re.search(
        r"thời\s+hạn\s+(\d+)\s+(ngày|tháng)\b", raw, flags=re.I | re.U
    )
    if m8 and not out.get("ten_chi_so") and (
        "thanh toán" in t or "góp vốn" in t or "than toan" in t or "gop von" in t
    ):
        unit = "ngay" if "ngày" in m8.group(0).lower() else "thang"
        _merge_threshold(
            out,
            {
                "ten_chi_so": "thoi_han_thanh_toan",
                "toan_tu_so_sanh": "eq",
                "gia_tri_nguong": m8.group(1),
                "don_vi_nguong": unit,
            },
        )

    m9 = re.search(
        r"trong\s+thời\s+hạn\s+(\d+)\s+ngày(?:\s+làm\s+việc)?", raw, flags=re.I | re.U
    )
    if m9 and not out.get("gia_tri_nguong"):
        key = "thoi_han_xu_ly"
        if "đăng ký chuyển đổi" in t or "dang ky chuyen doi" in t:
            key = "thoi_han_dang_ky_chuyen_doi"
        elif "nhận hồ sơ" in t or "nhan ho so" in t:
            key = "thoi_han_xu_ly_ho_so"
        _merge_threshold(
            out,
            {
                "ten_chi_so": key,
                "toan_tu_so_sanh": "eq",
                "gia_tri_nguong": m9.group(1),
                "don_vi_nguong": "ngay_lam_viec" if "làm việc" in m9.group(0).lower() else "ngay",
            },
        )

    m10 = re.search(r"(\d+)\s+ngày\s+làm\s+việc", raw, flags=re.I | re.U)
    if m10 and not out.get("gia_tri_nguong") and ("gửi" in t or "thông báo" in t):
        _merge_threshold(
            out,
            {
                "ten_chi_so": "thoi_han_thuc_hien",
                "toan_tu_so_sanh": "eq",
                "gia_tri_nguong": m10.group(1),
                "don_vi_nguong": "ngay_lam_viec",
            },
        )

    return {k: v for k, v in out.items() if v}


def _threshold_blurb(row: pd.Series) -> str:
    parts: list[str] = []
    if _s(row.get("ten_chi_so")):
        parts.append(_s(row["ten_chi_so"]))
    if _s(row.get("toan_tu_so_sanh")) and _s(row.get("gia_tri_nguong")):
        dv = _s(row.get("don_vi_nguong"))
        frag = f"{row['toan_tu_so_sanh']} {row['gia_tri_nguong']}" + (f" {dv}" if dv else "")
        parts.append(frag)
    elif _s(row.get("gia_tri_tu")) and _s(row.get("gia_tri_den")):
        parts.append(f"khoảng {row['gia_tri_tu']}–{row['gia_tri_den']} {_s(row.get('don_vi_nguong'))}")
    dk = _s(row.get("dieu_kien_ap_dung"))
    if dk and len(dk) < 120:
        parts.append(dk)
    return "; ".join(p for p in parts if p)[:320]


def refine_quantitative_row(row: pd.Series) -> pd.Series:
    r = row.copy()
    rt = _s(r.get("rule_type"))
    if rt != "quy_tac_nguong_dinh_luong":
        return r
    blob = " ".join(
        [
            _s(r.get("dieu_kien_ap_dung")),
            _s(r.get("source_text")),
            _s(r.get("grounded_summary")),
            _s(r.get("hanh_vi_phap_ly")),
        ]
    )
    inferred = infer_threshold_fields(blob)
    for k, v in inferred.items():
        if not _s(r.get(k)):
            r[k] = v
    if inferred:
        n = _s(r.get("notes"))
        tag = "bo_sung_cau_truc_nguong"
        if tag not in n.split(";"):
            r["notes"] = f"{n};{tag}".strip(";") if n else tag
    blurb = _threshold_blurb(r)
    if inferred and blurb:
        r["answer_template"] = f"Ngưỡng/điều kiện định lượng: {blurb}."
        r["grounded_summary"] = f"Ngưỡng/điều kiện định lượng: {blurb}."[:380]
    return r


def enrich_he_qua_row(row: pd.Series) -> pd.Series:
    r = row.copy()
    he = _s(r.get("he_qua_phap_ly"))
    kq = _s(r.get("ket_qua_thu_tuc"))
    st = _s(r.get("source_text"))
    rt = _s(r.get("rule_type"))

    if he and he.lower() not in _ABSTRACT_HE_QUA:
        return r

    candidate = ""
    if kq and len(kq) >= 12 and kq.lower() not in _ABSTRACT_HE_QUA:
        candidate = kq
    if not candidate:
        ext = extract_ket_qua_thu_tuc(st) if st else None
        if ext:
            candidate = ext
    if candidate and len(candidate) < 400:
        if not he or he.lower() in _ABSTRACT_HE_QUA or len(candidate) > len(he):
            r["he_qua_phap_ly"] = candidate[:380]
            n = _s(r.get("notes"))
            tag = "bo_sung_he_qua_phap_ly"
            if tag not in n.split(";"):
                r["notes"] = f"{n};{tag}".strip(";") if n else tag
    return r


def enrich_thanh_phan_row(row: pd.Series) -> pd.Series:
    r = row.copy()
    tp = _s(r.get("thanh_phan_ho_so"))
    st = _s(r.get("source_text"))
    rt = _s(r.get("rule_type"))

    if tp and not _ABSTRACT_DOSSIER.match(tp):
        return r
    if rt != "quy_tac_ho_so" and not (
        rt in {"quy_tac_thu_tuc", "quy_tac_hanh_dong_co_quan"} and dossier_cues_in_text(st)
    ):
        return r
    if not st:
        return r
    ext = extract_thanh_phan_ho_so(st)
    if ext and (not tp or _ABSTRACT_DOSSIER.match(tp) or len(ext) > len(tp)):
        r["thanh_phan_ho_so"] = ext[:480]
        n = _s(r.get("notes"))
        tag = "bo_sung_thanh_phan_ho_so"
        if tag not in n.split(";"):
            r["notes"] = f"{n};{tag}".strip(";") if n else tag
        if rt == "quy_tac_ho_so":
            r["answer_template"] = f"Hồ sơ gồm: {r['thanh_phan_ho_so']}."
            r["grounded_summary"] = f"Hồ sơ gồm: {r['thanh_phan_ho_so']}".strip()[:380]
    return r


HE_QUA_RULE_TYPES = frozenset(
    {
        "quy_tac_ket_qua_phap_ly",
        "quy_tac_hanh_dong_co_quan",
        "quy_tac_thu_tuc",
        "quy_tac_nghia_vu",
    }
)


def refine_rulebase_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Enrich rows, then drop duplicate legal content (keeping richest row)."""
    out = df.copy().astype(object)
    for i in out.index:
        out.loc[i] = refine_quantitative_row(out.loc[i])
    for i in out.index:
        if _s(out.loc[i, "rule_type"]) in HE_QUA_RULE_TYPES:
            out.loc[i] = enrich_he_qua_row(out.loc[i])
    for i in out.index:
        out.loc[i] = enrich_thanh_phan_row(out.loc[i])
    out = deduplicate_by_content(out)
    return out


__all__ = [
    "FINGERPRINT_COLS",
    "content_fingerprint",
    "deduplicate_by_content",
    "enrich_he_qua_row",
    "enrich_thanh_phan_row",
    "infer_threshold_fields",
    "refine_quantitative_row",
    "refine_rulebase_dataframe",
]
