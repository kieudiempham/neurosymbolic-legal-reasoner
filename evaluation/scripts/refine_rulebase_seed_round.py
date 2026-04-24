"""
Final refinement pass for data/processed/rulebase/rulebase_seed.xlsx.

Fills structured slots from grounded_summary / source_text / dieu_kien_ap_dung
without modifying source_text, rule_id, or trace columns (frame_id, candidate_id,
source_unit_id, source_ref).

Run from repo root:
  python scripts/refine_rulebase_seed_round.py
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DEFAULT_XLSX = REPO / "data" / "processed" / "rulebase" / "rulebase_seed.xlsx"

ABSTRACT_KQ = frozenset(
    {
        "có kết quả",
        "được xử lý",
        "phải thực hiện",
        "theo quy định",
        "công ty xem xét",
        "doanh nghiệp thực hiện",
    }
)


def _is_empty(v) -> bool:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return True
    s = str(v).strip()
    return s == "" or s.lower() == "nan"


def _cap_sentence(s: str) -> str:
    s = " ".join(s.split())
    if not s:
        return s
    return s[0].upper() + s[1:] if len(s) > 1 else s.upper()


def _blob(row: pd.Series) -> str:
    parts = [
        str(row.get("source_text") or ""),
        str(row.get("dieu_kien_ap_dung") or ""),
        str(row.get("grounded_summary") or ""),
    ]
    return " ".join(parts)


def _fnum(x: str) -> float:
    return float(x.replace(",", ".").replace(" ", ""))


# đến / tới (kể cả gõ thiếu dấu)
_RE_DEN = r"(?:đến|đen|tới|toi)"


def _parse_range_from_text(text: str) -> dict | None:
    """
    Trích khoảng số từ văn bản điều luật (tiếng Việt). Trả về các field:
    gia_tri_tu, gia_tri_den, kieu_khoang, don_vi_nguong, ten_chi_so — hoặc None.

    Các dạng được hỗ trợ (minh họa):
    - "trên 10% đến dưới 35%" / "trên 10 % đến dưới 35 %"
    - "từ 10% đến 35%"
    - "từ 02 đến 50 thành viên"
    - "trong khoảng từ 30 đến 90 ngày" / "trong thời hạn từ 30 đến 90 ngày"
    - "từ X đến dưới Y" / "từ X đến không quá Y"
    """
    t = text.replace("\u00a0", " ")
    t_low = t.lower()

    def _window(start: int, end: int, after: int = 48) -> str:
        return t_low[max(0, start - 8) : min(len(t_low), end + after)]

    # --- trên X% đến dưới Y% (hai đầu mở) ---
    m = re.search(
        r"tr[êe]n\s+(\d+(?:[.,]\d+)?)\s*%?\s*" + _RE_DEN + r"\s+dưới\s+(\d+(?:[.,]\d+)?)\s*%",
        t,
        re.I,
    )
    if m:
        a, b = _fnum(m.group(1)), _fnum(m.group(2))
        return {
            "gia_tri_tu": a,
            "gia_tri_den": b,
            "kieu_khoang": "mo_hai_dau",
            "don_vi_nguong": "phan_tram",
            "ten_chi_so": "ty_le_so_huu",
        }

    # --- từ X% đến Y% (khoảng phần trăm đóng) ---
    m = re.search(
        r"t[uừ]\s+0*(\d+(?:[.,]\d+)?)\s*%\s*" + _RE_DEN + r"\s+0*(\d+(?:[.,]\d+)?)\s*%",
        t,
        re.I,
    )
    if m:
        a, b = _fnum(m.group(1)), _fnum(m.group(2))
        return {
            "gia_tri_tu": a,
            "gia_tri_den": b,
            "kieu_khoang": "dong",
            "don_vi_nguong": "phan_tram",
            "ten_chi_so": "ty_le_so_huu",
        }

    # --- từ X đến không quá Y ---
    m = re.search(
        r"t[uừ]\s+0*(\d+(?:[.,]\d+)?)\s*" + _RE_DEN + r"\s+không\s+quá\s+0*(\d+(?:[.,]\d+)?)",
        t,
        re.I,
    )
    if m:
        a, b = _fnum(m.group(1)), _fnum(m.group(2))
        w = _window(m.start(), m.end())
        unit, tcs = _unit_from_window(w)
        return {
            "gia_tri_tu": a,
            "gia_tri_den": b,
            "kieu_khoang": "mo_phai",
            "don_vi_nguong": unit,
            "ten_chi_so": tcs,
        }

    # --- từ X đến dưới Y (không nhất thiết có %) ---
    m = re.search(
        r"t[uừ]\s+0*(\d+(?:[.,]\d+)?)\s*" + _RE_DEN + r"\s+dưới\s+0*(\d+(?:[.,]\d+)?)",
        t,
        re.I,
    )
    if m:
        a, b = _fnum(m.group(1)), _fnum(m.group(2))
        w = _window(m.start(), m.end())
        unit, tcs = _unit_from_window(w)
        kk = "mo_phai" if "%" in w or "phần trăm" in w else "mo_phai"
        return {
            "gia_tri_tu": a,
            "gia_tri_den": b,
            "kieu_khoang": kk,
            "don_vi_nguong": unit,
            "ten_chi_so": tcs,
        }

    # --- trong thời hạn từ X đến Y ngày ---
    m = re.search(
        r"trong\s+thời\s+hạn\s+t[uừ]\s+0*(\d+(?:[.,]\d+)?)\s*"
        + _RE_DEN
        + r"\s+0*(\d+(?:[.,]\d+)?)\s+ngày",
        t,
        re.I,
    )
    if m:
        a, b = _fnum(m.group(1)), _fnum(m.group(2))
        return {
            "gia_tri_tu": a,
            "gia_tri_den": b,
            "kieu_khoang": "dong",
            "don_vi_nguong": "ngay",
            "ten_chi_so": "thoi_han",
        }

    # --- trong khoảng từ X đến Y (ngày / không đơn vị) ---
    m = re.search(
        r"trong\s+khoảng\s+t[uừ]\s+0*(\d+(?:[.,]\d+)?)\s*"
        + _RE_DEN
        + r"\s+0*(\d+(?:[.,]\d+)?)(?:\s+ngày)?",
        t,
        re.I,
    )
    if m:
        a, b = _fnum(m.group(1)), _fnum(m.group(2))
        w = _window(m.start(), m.end())
        unit = "ngay" if "ngày" in w or "ngay" in w else "khong_xac_dinh_ro"
        tcs = "thoi_han" if unit == "ngay" else "chi_so_dinh_luong"
        return {
            "gia_tri_tu": a,
            "gia_tri_den": b,
            "kieu_khoang": "dong",
            "don_vi_nguong": unit,
            "ten_chi_so": tcs,
        }

    # --- từ X đến Y thành viên (đơn vị sau biên phải) ---
    m = re.search(
        r"t[uừ]\s+0*(\d+(?:[.,]\d+)?)\s*" + _RE_DEN + r"\s+0*(\d+(?:[.,]\d+)?)\s+th[àa]nh\s+vi[êe]n",
        t,
        re.I,
    )
    if m:
        a, b = _fnum(m.group(1)), _fnum(m.group(2))
        return {
            "gia_tri_tu": a,
            "gia_tri_den": b,
            "kieu_khoang": "dong",
            "don_vi_nguong": "thanh_vien",
            "ten_chi_so": "so_thanh_vien",
        }

    # --- từ X đến Y ngày (không có "trong khoảng") ---
    m = re.search(
        r"t[uừ]\s+0*(\d+(?:[.,]\d+)?)\s*" + _RE_DEN + r"\s+0*(\d+(?:[.,]\d+)?)\s+ngày",
        t,
        re.I,
    )
    if m:
        a, b = _fnum(m.group(1)), _fnum(m.group(2))
        return {
            "gia_tri_tu": a,
            "gia_tri_den": b,
            "kieu_khoang": "dong",
            "don_vi_nguong": "ngay",
            "ten_chi_so": "thoi_han",
        }

    # --- từ X đến Y với đơn vị % ngay sau biên phải (một dòng) ---
    m = re.search(
        r"t[uừ]\s+0*(\d+(?:[.,]\d+)?)\s*" + _RE_DEN + r"\s+0*(\d+(?:[.,]\d+)?)\s*%",
        t,
        re.I,
    )
    if m:
        a, b = _fnum(m.group(1)), _fnum(m.group(2))
        return {
            "gia_tri_tu": a,
            "gia_tri_den": b,
            "kieu_khoang": "dong",
            "don_vi_nguong": "phan_tram",
            "ten_chi_so": "ty_le_so_huu",
        }

    # --- Fallback: từ X đến Y (hai số liên tiếp; đơn vị trong cửa sổ sau) ---
    m = re.search(
        r"t[uừ]\s+0*(\d+(?:[.,]\d+)?)\s*" + _RE_DEN + r"\s+(?:dưới\s+)?0*(\d+(?:[.,]\d+)?)",
        t,
        re.I,
    )
    if m:
        a, b = _fnum(m.group(1)), _fnum(m.group(2))
        if m.group(0).lower().find("dưới") >= 0 or m.group(0).lower().find("duoi") >= 0:
            kk = "mo_phai"
        else:
            kk = "khong_xac_dinh_ro"
        w = _window(m.start(), m.end(), after=64)
        unit, tcs = _unit_from_window(w)
        return {
            "gia_tri_tu": a,
            "gia_tri_den": b,
            "kieu_khoang": kk,
            "don_vi_nguong": unit,
            "ten_chi_so": tcs,
        }

    return None


def _unit_from_window(w: str) -> tuple[str, str]:
    """Đơn vị và tên chỉ số gợi ý từ cửa sổ chữ thường quanh khớp."""
    if "thành viên" in w or "thanh vien" in w:
        return "thanh_vien", "so_thanh_vien"
    if "%" in w or "phần trăm" in w or "phan tram" in w:
        return "phan_tram", "ty_le_so_huu"
    if "ngày" in w or "ngay" in w:
        return "ngay", "thoi_han"
    return "khong_xac_dinh_ro", "chi_so_dinh_luong"


def _applicant_from_co_quan_gs(gs: str) -> str | None:
    gs = gs.strip()
    low = gs.lower()
    if not low.startswith("cơ quan đăng ký"):
        return None
    for marker in (" và cấp ", " cấp "):
        pos = low.find(marker)
        if pos != -1:
            after = gs[pos + len(marker) :].strip()
            for stop in (";", "trường hợp", "\n"):
                if stop in after:
                    after = after.split(stop)[0].strip()
            after = after.rstrip("., ")
            if len(after) > 4:
                if after.lower().startswith("được"):
                    return _cap_sentence(after)
                return _cap_sentence(f"được cấp {after}")
    return None


def _fill_ho_so_components(gs: str) -> str | None:
    s = gs.strip()
    if not s.lower().startswith("hồ sơ gồm"):
        return None
    _, _, rest = s.partition(":")
    rest = rest.strip()
    if not rest:
        return None
    parts = re.split(r"[;,]\s*", rest)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        return None
    return "; ".join(parts)


def _infer_pham_vi(blob: str) -> str | None:
    b = blob.lower()
    hits: list[str] = []
    patterns = [
        (r"đối với\s+(công ty cổ phần[^.;,\n]{0,80})", "áp dụng đối với công ty cổ phần"),
        (
            r"đối với\s+(công ty trách nhiệm hữu hạn[^.;,\n]{0,100})",
            None,
        ),
        (r"doanh nghiệp tư nhân", "áp dụng đối với doanh nghiệp tư nhân"),
        (r"công ty trách nhiệm hữu hạn hai thành viên", "áp dụng đối với công ty trách nhiệm hữu hạn hai thành viên trở lên"),
        (r"chi nhánh[,\s]+văn phòng đại diện", "áp dụng đối với chi nhánh, văn phòng đại diện"),
        (r"cổ đông sáng lập", "áp dụng đối với cổ đông sáng lập"),
        (r"doanh nghiệp nhà nước", "áp dụng đối với doanh nghiệp nhà nước"),
    ]
    for pat, fixed in patterns:
        m = re.search(pat, b, re.I)
        if m and fixed:
            if fixed not in hits:
                hits.append(fixed)
        elif m and not fixed:
            phrase = m.group(1).strip()
            if len(phrase) > 5:
                cand = f"áp dụng đối với {phrase}"
                if cand not in hits:
                    hits.append(cand[:120])
    if not hits:
        return None
    return "; ".join(hits[:3])


def _infer_phuong_thuc(blob: str) -> str | None:
    """
    Chỉ gắn phương thức khi văn bản nêu rõ kênh nộp / gửi của chủ thể (DN, cổ đông…),
    không suy từ câu 'cơ quan cập nhật CSDL' vì đó là kết quả xử lý, không phải cách nộp.
    """
    b = blob.lower()
    parts: list[str] = []
    if "nộp qua cổng dịch vụ công" in b or "dịch vụ công trực tuyến" in b or "nộp qua mạng" in b:
        parts.append("nộp qua mạng thông tin điện tử")
    if "nộp trực tiếp" in b or "nộp hồ sơ trực tiếp" in b:
        parts.append("nộp trực tiếp")
    if "bưu chính" in b or "chuyển phát" in b:
        parts.append("nộp qua dịch vụ bưu chính")
    # Gửi phiếu / hồ sơ bằng thư, fax, email (khớp đoạn Luật DN về lấy ý kiến cổ đông)
    if re.search(
        r"(gửi|nộp|trả)\s+[^.;]{0,40}(thư|fax|thư\s+điện\s+tử|email|điện\s+tử)",
        b,
    ):
        parts.append("gửi thông tin bằng thư, fax hoặc thư điện tử")
    # Doanh nghiệp / công ty chủ động công bố (ít gặp; tránh khớp câu cơ quan công bố)
    if re.search(
        r"(doanh\s+nghiệp|công\s+ty|cổ\s+đông)[^.;]{0,80}công\s+bố[^.;]{0,60}cổng\s+thông\s+tin",
        b,
    ):
        parts.append("công bố trên Cổng thông tin quốc gia về đăng ký doanh nghiệp")
    if not parts:
        return None
    return "; ".join(dict.fromkeys(parts))


def _append_note(prev: str, tag: str) -> str:
    prev = (prev or "").strip()
    if not prev:
        return tag
    if tag.lower() in prev.lower():
        return prev
    return f"{prev}; {tag}"


def refine(path: Path, dry_run: bool = False) -> tuple[pd.DataFrame, dict[str, int]]:
    df = pd.read_excel(path)
    notes_col = "notes"
    if notes_col not in df.columns:
        df[notes_col] = ""

    # Tránh gán chuỗi vào cột float (ô trống trong Excel) gây FutureWarning
    _slot_cols = [
        "he_qua_phap_ly",
        "ket_qua_thu_tuc",
        "thanh_phan_ho_so",
        "pham_vi_ap_dung",
        "phuong_thuc_thuc_hien",
        "gia_tri_tu",
        "gia_tri_den",
        "kieu_khoang",
        "don_vi_nguong",
        "ten_chi_so",
        notes_col,
    ]
    for c in _slot_cols:
        if c in df.columns:
            df[c] = df[c].astype(object)

    stats = {
        "range_filled": 0,
        "ket_qua_filled": 0,
        "he_qua_filled": 0,
        "thanh_phan_filled": 0,
        "pham_vi_filled": 0,
        "phuong_thuc_filled": 0,
    }

    for i in df.index:
        row = df.loc[i]
        blob = _blob(row)
        gs = str(row.get("grounded_summary") or "").strip()

        # --- B. Range (only when clearly a range; do not touch single-threshold rows) ---
        if row.get("rule_type") == "quy_tac_nguong_dinh_luong":
            if _is_empty(row.get("gia_tri_tu")) and _is_empty(row.get("gia_tri_den")):
                parsed = _parse_range_from_text(blob)
                if parsed:
                    for k, v in parsed.items():
                        df.at[i, k] = v
                    df.at[i, notes_col] = _append_note(
                        str(df.at[i, notes_col]), "bo_sung_khoang_nguong"
                    )
                    stats["range_filled"] += 1

        # --- C/D/E/F enrichments ---
        rt = str(row.get("rule_type") or "")

        # ket_qua from cơ quan ... (procedure outcome)
        if _is_empty(row.get("ket_qua_thu_tuc")) and gs.lower().startswith(
            "cơ quan đăng ký"
        ):
            if len(gs) > 15 and gs.lower() not in ABSTRACT_KQ:
                df.at[i, "ket_qua_thu_tuc"] = _cap_sentence(gs)
                df.at[i, notes_col] = _append_note(
                    str(df.at[i, notes_col]), "bo_sung_ket_qua_thu_tuc"
                )
                stats["ket_qua_filled"] += 1

        # he_qua: agency rules → applicant-facing; nghia_vu / thu_tuc from grounded text
        if _is_empty(row.get("he_qua_phap_ly")):
            filled = False
            if rt in (
                "quy_tac_hanh_dong_co_quan",
                "quy_tac_thu_tuc",
            ):
                cand = _applicant_from_co_quan_gs(gs)
                if cand:
                    df.at[i, "he_qua_phap_ly"] = cand
                    filled = True
            elif rt == "quy_tac_nghia_vu" and gs and len(gs) > 12:
                low = gs.lower().strip()
                if low not in ABSTRACT_KQ and not low.startswith("cơ quan"):
                    df.at[i, "he_qua_phap_ly"] = _cap_sentence(gs)
                    filled = True
            if filled:
                df.at[i, notes_col] = _append_note(
                    str(df.at[i, notes_col]), "bo_sung_he_qua_phap_ly"
                )
                stats["he_qua_filled"] += 1

        # Mirror ket_qua to he_qua when ket_qua was set this round but he_qua still empty
        if _is_empty(df.at[i, "he_qua_phap_ly"]) and not _is_empty(
            df.at[i, "ket_qua_thu_tuc"]
        ):
            kq = str(df.at[i, "ket_qua_thu_tuc"]).strip()
            alt = _applicant_from_co_quan_gs(gs) if gs else None
            if alt:
                df.at[i, "he_qua_phap_ly"] = alt
                df.at[i, notes_col] = _append_note(
                    str(df.at[i, notes_col]), "bo_sung_he_qua_phap_ly"
                )
                stats["he_qua_filled"] += 1
            elif len(kq) > 15 and kq.lower() not in ABSTRACT_KQ:
                df.at[i, "he_qua_phap_ly"] = kq
                df.at[i, notes_col] = _append_note(
                    str(df.at[i, notes_col]), "bo_sung_he_qua_phap_ly"
                )
                stats["he_qua_filled"] += 1

        # thanh_phan_ho_so
        if _is_empty(row.get("thanh_phan_ho_so")):
            comp = _fill_ho_so_components(gs)
            if comp:
                df.at[i, "thanh_phan_ho_so"] = comp
                df.at[i, notes_col] = _append_note(
                    str(df.at[i, notes_col]), "bo_sung_thanh_phan_ho_so"
                )
                stats["thanh_phan_filled"] += 1

        # pham_vi_ap_dung
        if _is_empty(row.get("pham_vi_ap_dung")):
            pv = _infer_pham_vi(blob)
            if pv:
                df.at[i, "pham_vi_ap_dung"] = pv
                df.at[i, notes_col] = _append_note(
                    str(df.at[i, notes_col]), "bo_sung_pham_vi_ap_dung"
                )
                stats["pham_vi_filled"] += 1

        # phuong_thuc_thuc_hien
        if _is_empty(row.get("phuong_thuc_thuc_hien")):
            pm = _infer_phuong_thuc(blob)
            if pm:
                df.at[i, "phuong_thuc_thuc_hien"] = pm
                df.at[i, notes_col] = _append_note(
                    str(df.at[i, notes_col]), "bo_sung_phuong_thuc_thuc_hien"
                )
                stats["phuong_thuc_filled"] += 1

    if not dry_run:
        backup = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, backup)
        df.to_excel(path, index=False)

    return df, stats


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Refine rulebase_seed.xlsx (structured slots).")
    p.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_XLSX,
        help="Path to rulebase_seed.xlsx",
    )
    p.add_argument("--dry-run", action="store_true", help="Do not write file.")
    args = p.parse_args()
    df, stats = refine(args.path, dry_run=args.dry_run)
    print("rows:", len(df))
    print("stats:", stats)
    if not args.dry_run:
        print("backup:", args.path.with_suffix(args.path.suffix + ".bak"))


if __name__ == "__main__":
    main()
