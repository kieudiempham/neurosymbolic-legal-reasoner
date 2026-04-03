"""Enrich legal frame slots for fan-out to rulebase (grounded, source-first)."""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Text utils
# ---------------------------------------------------------------------------


def norm_space(s: str | None) -> str:
    t = (s or "").replace("\r\n", "\n").replace("\r", "\n")
    t = t.replace("\n", " ")
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def blank(v: Any) -> bool:
    if v is None:
        return True
    s = str(v).strip()
    return s == "" or s.lower() == "nan"


def _append_note(cur: str, tag: str) -> str:
    tag = tag.strip()
    if not tag:
        return cur
    parts = [p.strip() for p in (cur or "").split(";") if p.strip()]
    if tag not in parts:
        parts.append(tag)
    return ";".join(parts)


# ---------------------------------------------------------------------------
# Context: source_text + structural hints; optional unit text if very short
# ---------------------------------------------------------------------------

SOURCE_SHORT = 55


def build_grounding_text(
    *,
    source_text: str,
    heading: str = "",
    parent_context: str = "",
    unit_ref_full: str = "",
    unit_text_fallback: str = "",
) -> str:
    st = norm_space(source_text)
    if len(st) >= SOURCE_SHORT:
        return st
    bits = [st]
    for x in (heading, parent_context, unit_ref_full):
        xn = norm_space(x)
        if xn and xn not in st:
            bits.append(xn)
    if len(norm_space(" ".join(bits))) < SOURCE_SHORT and unit_text_fallback:
        ut = norm_space(unit_text_fallback)
        if ut and ut not in " ".join(bits):
            bits.append(ut)
    return norm_space(" ".join(bits))


# ---------------------------------------------------------------------------
# Dossier / thành phần hồ sơ
# ---------------------------------------------------------------------------

_DOSSIER_TRIGGER = re.compile(
    r"\b(?:hồ\s+sơ\s+bao\s+gồm|kèm\s+theo|"
    r"bao\s+gồm\s+các\s+(?:giấy\s+tờ|tài\s+liệu)|"
    r"thông\s+báo[^.;]{0,40}phải\s+bao\s+gồm|"
    r"nộp\s+[^.;]{0,60}?(?:hồ\s+sơ|giấy\s+tờ))\b",
    flags=re.I | re.U,
)

_DOC_PHRASES = re.compile(
    r"\b("
    r"Giấy\s+đề\s+nghị(?:\s+đăng\s+ký(?:\s+doanh\s+nghiệp)?)?[^.;]{0,100}"
    r"|điều\s+lệ\s+công\s+ty[^.;]{0,40}"
    r"|văn\s+bản\s+ủy\s+quyền[^.;]{0,100}"
    r"|Bản\s+sao(?:\s+hoặc\s+bản\s+chính)?[^.;]{0,140}"
    r"|Bản\s+chính[^.;]{0,100}"
    r"|bản\s+sao\s+biên\s+bản\s+họp[^.;]{0,120}"
    r"|bản\s+sao\s+quyết\s+định[^.;]{0,120}"
    r"|Danh\s+sách\s+thành\s+viên[^.;]{0,120}"
    r"|Danh\s+sách\s+cổ\s+đông\s+sáng\s+lập[^.;]{0,120}"
    r"|Danh\s+sách\s+chủ\s+sở\s+hữu\s+hưởng\s+lợi[^.;]{0,120}"
    r"|nghị\s+quyết(?:\s+và\s+biên\s+bản\s+họp)?[^.;]{0,100}"
    r"|biên\s+bản\s+họp[^.;]{0,120}"
    r"|quyết\s+định[^.;]{0,100}"
    r"|giấy\s+tờ\s+pháp\s+lý\s+của\s+[^.;]{0,160}"
    r"|hợp\s+đồng[^.;]{0,100}"
    r"|Thông\s+báo\s+thành\s+lập\s+chi\s+nhánh[^.;]{0,120}"
    r"|Giấy\s+chứng\s+nhận\s+đăng\s+ký\s+doanh\s+nghiệp[^.;]{0,40}"
    r"|hồ\s+sơ\s+đăng\s+ký[^.;]{0,120}"
    r")\b",
    flags=re.I | re.U,
)


def _list_items_after_dossier(t: str) -> list[str]:
    items: list[str] = []
    m = re.search(
        r"(?:hồ\s+sơ\s+bao\s+gồm|kèm\s+theo|bao\s+gồm\s+các\s+(?:giấy\s+tờ|tài\s+liệu))\s*:?\s*",
        t,
        flags=re.I | re.U,
    )
    if not m:
        return items
    chunk = t[m.end() : m.end() + 450]
    chunk = re.split(r"\b(?:phải|được|trong\s+thời\s+hạn|Cơ\s+quan)\b", chunk, maxsplit=1, flags=re.I | re.U)[0]
    for sep_pat in [r"(?m)(?:^|\n)\s*[a-zđ]\)\s+", r";\s+", r"\d+\.\s+"]:
        if re.search(sep_pat, chunk, flags=re.I | re.U):
            parts = re.split(sep_pat, chunk)
            for p in parts:
                s = norm_space(p).strip(" ,;-–")
                if 8 <= len(s) <= 200:
                    items.append(s)
            break
    return items


def extract_thanh_phan_ho_so(text: str) -> str | None:
    t = norm_space(text)
    if not t or not _DOSSIER_TRIGGER.search(t) and not _DOC_PHRASES.search(t):
        return None
    found: list[str] = []
    for m in _DOC_PHRASES.finditer(t):
        s = norm_space(m.group(1)).strip(" ,;-–")
        if len(s) >= 8 and s not in found:
            found.append(s)
    for it in _list_items_after_dossier(t):
        if it not in found:
            found.append(it)
    if not found:
        # Single-line kèm theo / hồ sơ clause
        m2 = re.search(
            r"\b(kèm\s+theo[^.;]{0,220}|hồ\s+sơ\s+bao\s+gồm[^.;]{0,260})\b",
            t,
            flags=re.I | re.U,
        )
        if m2:
            found.append(norm_space(m2.group(1)).strip(" ,;-–"))
    if not found:
        return None
    joined = "; ".join(found[:10])
    if len(joined) > 480:
        joined = joined[:477].rsplit(";", 1)[0] + "…"
    return joined


def dossier_cues_in_text(text: str) -> bool:
    t = norm_space(text)
    return bool(_DOSSIER_TRIGGER.search(t) or _DOC_PHRASES.search(t))


# ---------------------------------------------------------------------------
# Đối tượng hành vi
# ---------------------------------------------------------------------------

_VAGUE_OBJECTS = re.compile(
    r"^(?:thông\s+tin|hồ\s+sơ|tài\s+liệu|nội\s+dung|văn\s+bản|quy\s+định|"
    r"doanh\s+nghiệp|công\s+ty|đối\s+tượng|trường\s+hợp)\s*$",
    flags=re.I | re.U,
)

_OBJECT_PATS = [
    r"\bGiấy\s+chứng\s+nhận\s+đăng\s+ký\s+doanh\s+nghiệp\b",
    r"\bnội\s+dung\s+đăng\s+ký\s+doanh\s+nghiệp\b",
    r"\bhồ\s+sơ\s+đăng\s+ký(?:(?:\s+hoạt\s+động)?\s+chi\s+nhánh)?\b",
    r"\bvốn\s+điều\s+lệ\b",
    r"\bphần\s+vốn\s+góp\b",
    r"\bcổ\s+phần\s+phổ\s+thông\b",
    r"\bthông\s+tin\s+(?:về\s+)?chủ\s+sở\s+hữu\s+hưởng\s+lợi\b",
    r"\bdanh\s+sách\s+thành\s+viên\b",
    r"\bdanh\s+sách\s+cổ\s+đông\s+sáng\s+lập\b",
    r"\bđịa\s+điểm\s+kinh\s+doanh\b",
    r"\bchi\s+nhánh\b(?:\s*,\s*văn\s+phòng\s+đại\s+diện)?",
    r"\bvăn\s+phòng\s+đại\s+diện\b",
    r"\bsổ\s+đăng\s+ký\s+cổ\s+đông\b",
    r"\btài\s+liệu\s+của\s+doanh\s+nghiệp\b",
    r"\bĐiều\s+lệ\s+công\s+ty\b",
    r"\bngười\s+đại\s+diện\s+theo\s+pháp\s+luật\b",
    r"\bđăng\s+ký\s+doanh\s+nghiệp\b",
]


def _object_after_verb(t: str, hanh_vi: str | None) -> str | None:
    if not hanh_vi or blank(hanh_vi):
        return None
    hv = norm_space(hanh_vi)
    if len(hv) < 4:
        return None
    try:
        esc = re.escape(hv)
    except re.error:
        return None
    m = re.search(esc + r"\s+([^.;]{6,140}?)(?=\s*[.;,]|$)", t, flags=re.I | re.U)
    if not m:
        return None
    chunk = norm_space(m.group(1))
    chunk = re.sub(r"^(cho|với|đối\s+với|theo|trong|về)\s+", "", chunk, flags=re.I | re.U)
    if len(chunk) < 6 or _VAGUE_OBJECTS.match(chunk):
        return None
    return chunk[:200]


def extract_doi_tuong_hanh_vi(text: str, hanh_vi: str | None, current: str | None) -> str | None:
    t = norm_space(text)
    if not t:
        return None
    cur = norm_space(current) if current else ""
    best: str | None = None
    if (
        cur
        and not _VAGUE_OBJECTS.match(cur)
        and len(cur) >= 8
        and not re.match(r"^(điều\s+lệ|yêu\s+cầu|quyết\s+định|hồ\s+sơ)\s*$", cur, flags=re.I | re.U)
    ):
        best = cur[:200]
    for pat in _OBJECT_PATS:
        m = re.search(pat, t, flags=re.I | re.U)
        if m:
            cand = m.group(0).strip()[:200]
            if best is None or len(cand) > len(best):
                best = cand
    oa = _object_after_verb(t, hanh_vi)
    if oa and (best is None or len(oa) > len(best)):
        best = oa
    return best


def should_clear_vague_object(current: str | None) -> bool:
    if blank(current):
        return False
    s = norm_space(current)
    if len(s) < 6:
        return True
    return bool(_VAGUE_OBJECTS.match(s))


# ---------------------------------------------------------------------------
# Kết quả thủ tục / hậu quả pháp lý
# ---------------------------------------------------------------------------

_ABSTRACT_KET_QUA = frozenset(
    {
        "phải thực hiện",
        "được xử lý",
        "có kết quả",
        "thực hiện theo quy định",
        "được phép thực hiện",
        "không được thực hiện",
    }
)


def _is_abstract_kq(s: str) -> bool:
    low = norm_space(s).lower()
    if low in _ABSTRACT_KET_QUA:
        return True
    if len(low) < 12 and "thực hiện" in low:
        return True
    return False


_KET_QUA_PATTERNS = [
    r"\bđược\s+cấp\s+Giấy\s+chứng\s+nhận\s+đăng\s+ký\s+doanh\s+nghiệp[^.;]{0,80}",
    r"\b(?:bị\s+)?thu\s+hồi\s+Giấy\s+chứng\s+nhận[^.;]{0,120}",
    r"\bđược\s+cập\s+nhật\s+trong\s+Cơ\s+sở\s+dữ\s+liệu\s+quốc\s+gia[^.;]{0,140}",
    r"\bđược\s+công\s+bố\s+trên\s+Cổng\s+thông\s+tin\s+quốc\s+gia[^.;]{0,160}",
    r"\bphải\s+đăng\s+ký\s+điều\s+chỉnh\s+vốn\s+điều\s+lệ[^.;]{0,80}",
    r"\bchấm\s+dứt\s+hoạt\s+động(?:\s+chi\s+nhánh)?[^.;]{0,100}",
    r"\bchuyển\s+đổi\s+thành\s+[^.;]{0,120}",
    r"\bđược\s+ghi\s+nhận[^.;]{0,120}",
    r"\bđược\s+xóa(?:\s+tên)?[^.;]{0,120}",
    r"\bkhông\s+còn\s+tư\s+cách[^.;]{0,120}",
    r"\bcó\s+hiệu\s+lực[^.;]{0,100}",
    r"\bhết\s+hiệu\s+lực[^.;]{0,100}",
    r"\bđược\s+cấp[^.;]{0,160}",
    r"\bđược\s+cập\s+nhật[^.;]{0,160}",
    r"\bđược\s+công\s+bố[^.;]{0,160}",
    r"\bbị\s+chấm\s+dứt[^.;]{0,120}",
    r"\bchấp\s+thuận[^.;]{0,160}",
    r"\bkhôi\s+phục[^.;]{0,120}",
    r"\bbị\s+tạm\s+ngừng[^.;]{0,120}",
]

_KET_QUA_RX = [re.compile(p, flags=re.I | re.U) for p in _KET_QUA_PATTERNS]


def ket_qua_cue_present(text: str) -> bool:
    t = norm_space(text)
    return any(rx.search(t) for rx in _KET_QUA_RX)


def extract_ket_qua_thu_tuc(text: str) -> str | None:
    t = norm_space(text)
    if not t:
        return None
    best: str | None = None
    for rx in _KET_QUA_RX:
        m = rx.search(t)
        if not m:
            continue
        cand = norm_space(m.group(0)).strip(" ,;")
        if _is_abstract_kq(cand):
            continue
        if best is None or len(cand) > len(best):
            best = cand
    if best and len(best) > 320:
        best = best[:317].rsplit(" ", 1)[0] + "…"
    return best


def extract_ket_qua_variants(text: str, *, max_n: int = 8) -> list[str]:
    """Non-overlapping grounded outcome spans (longest-first), for multi-rule fan-out."""
    t = norm_space(text)
    if not t:
        return []
    spans: list[tuple[int, int, str]] = []
    for rx in _KET_QUA_RX:
        for m in rx.finditer(t):
            cand = norm_space(m.group(0)).strip(" ,;")
            if _is_abstract_kq(cand) or len(cand) < 12:
                continue
            spans.append((m.start(), m.end(), cand))
    spans.sort(key=lambda x: (-(x[1] - x[0]), x[0]))
    picked: list[str] = []
    used: list[tuple[int, int]] = []
    for s, e, c in spans:
        if any(not (e <= us or s >= ue) for us, ue in used):
            continue
        if c in picked:
            continue
        picked.append(c)
        used.append((s, e))
        if len(picked) >= max_n:
            break
    return picked


# ---------------------------------------------------------------------------
# Fan-out hints
# ---------------------------------------------------------------------------

FRAME_FANOUT_PROC = frozenset(
    {
        "khung_ho_so",
        "khung_thu_tuc",
        "khung_hanh_dong_co_quan",
        "khung_ket_qua_phap_ly",
        "khung_nghia_vu",
    }
)


def suggest_fanout_flags(
    *,
    frame_type: str,
    thanh_phan: str,
    ket_qua: str,
    hanh_vi: str,
    source_text: str,
) -> tuple[str, str | None]:
    ft = (frame_type or "").strip().lower()
    if ft not in FRAME_FANOUT_PROC:
        return "khong", None
    reasons: list[str] = []
    t = norm_space(source_text)
    hs = bool(thanh_phan and str(thanh_phan).strip())
    kq = bool(ket_qua and str(ket_qua).strip())
    hv = bool(hanh_vi and str(hanh_vi).strip())
    if hs and kq and hv:
        reasons.append("vua_ho_so_vua_ket_qua")
    elif hv and kq and ket_qua_cue_present(t) and not hs:
        reasons.append("vua_hanh_vi_vua_ket_qua")
    if hs and thanh_phan and str(thanh_phan).count(";") >= 2:
        reasons.append("co_nhieu_thanh_phan_ho_so")
    if kq:
        if sum(1 for rx in _KET_QUA_RX if rx.search(t)) >= 2:
            reasons.append("co_nhieu_ket_qua")
    if not reasons:
        return "khong", None
    return "co", ";".join(dict.fromkeys(reasons))


def enrich_frame_row(
    row: dict[str, Any],
    *,
    grounding_text: str,
) -> dict[str, Any]:
    """Return patch dict (only keys to update)."""
    patch: dict[str, Any] = {}
    notes_add: list[str] = []
    ft = str(row.get("frame_type") or "").strip().lower()
    st_frame = norm_space(str(row.get("source_text") or ""))
    g = grounding_text if grounding_text else st_frame

    # --- thanh_phan_ho_so ---
    cur_tp = row.get("thanh_phan_ho_so")
    need_dossier = ft == "khung_ho_so" or (
        ft in {"khung_thu_tuc", "khung_nghia_vu"} and blank(cur_tp) and dossier_cues_in_text(g)
    )
    if need_dossier or (blank(cur_tp) and ft == "khung_ho_so" and dossier_cues_in_text(g)):
        ext = extract_thanh_phan_ho_so(g)
        if ext and (blank(cur_tp) or len(ext) > len(str(cur_tp or ""))):
            patch["thanh_phan_ho_so"] = ext
            notes_add.append("bo_sung_thanh_phan_ho_so_tu_source_text")

    # --- doi_tuong ---
    prev_dt = row.get("doi_tuong_hanh_vi")
    if should_clear_vague_object(str(prev_dt) if prev_dt is not None else None):
        patch["doi_tuong_hanh_vi"] = ""
        prev_dt = None
        notes_add.append("xoa_doi_tuong_mo_ho")
    hv = str(row.get("hanh_vi") or "").strip() or None
    prev_s = norm_space(str(prev_dt)) if prev_dt is not None else ""
    dt = extract_doi_tuong_hanh_vi(g, hv, prev_s or None)
    if dt and dt != prev_s:
        patch["doi_tuong_hanh_vi"] = dt
        notes_add.append("phuc_hoi_doi_tuong_hanh_vi_tu_source_text")

    # --- ket_qua ---
    cur_kq = row.get("ket_qua_thu_tuc")
    if blank(cur_kq) or _is_abstract_kq(str(cur_kq)):
        kq = extract_ket_qua_thu_tuc(g)
        if kq and norm_space(str(cur_kq)) != norm_space(kq):
            patch["ket_qua_thu_tuc"] = kq
            notes_add.append("bo_sung_ket_qua_thu_tuc_tu_source_text")

    # --- mismatch: khung_ho_so sans dossier ---
    if ft == "khung_ho_so" and dossier_cues_in_text(st_frame):
        tp_final = str(patch.get("thanh_phan_ho_so", row.get("thanh_phan_ho_so") or "") or "")
        if blank(tp_final):
            patch["muc_do_day_du"] = "thieu_vai_slot"
            notes_add.append("chua_phuc_hoi_duoc_thanh_phan_ho_so")

    # --- empty object note when hanh_vi strong ---
    hv_ok = bool(hv and len(hv) >= 8)
    dt_final = str(patch.get("doi_tuong_hanh_vi", row.get("doi_tuong_hanh_vi") or "") or "")
    if hv_ok and blank(dt_final) and not dossier_cues_in_text(g):
        notes_add.append("chua_phuc_hoi_duoc_slot_quan_trong")

    # --- fan-out ---
    tp_f = str(patch.get("thanh_phan_ho_so", row.get("thanh_phan_ho_so") or "") or "")
    kq_f = str(patch.get("ket_qua_thu_tuc", row.get("ket_qua_thu_tuc") or "") or "")
    hv_f = str(row.get("hanh_vi") or "").strip()
    can, ly = suggest_fanout_flags(
        frame_type=ft,
        thanh_phan=tp_f,
        ket_qua=kq_f,
        hanh_vi=hv_f,
        source_text=g,
    )
    if can == "co" and ly:
        existing_ly = str(row.get("ly_do_can_tach") or "").strip()
        parts = [p.strip() for p in existing_ly.split(";") if p.strip()]
        for p in ly.split(";"):
            p = p.strip()
            if p and p not in parts:
                parts.append(p)
        merged_ly = ";".join(parts)
        prev_can = str(row.get("can_tach_them") or "").strip().lower()
        if prev_can != "co" or merged_ly != existing_ly:
            patch["can_tach_them"] = "co"
            patch["ly_do_can_tach"] = merged_ly
            notes_add.append("can_tach_them_de_fan_out_rule")

    if notes_add:
        gcur = str(row.get("ghi_chu_giai_thich") or "")
        for tag in notes_add:
            gcur = _append_note(gcur, tag)
        patch["ghi_chu_giai_thich"] = gcur

    return patch


__all__ = [
    "build_grounding_text",
    "enrich_frame_row",
    "extract_doi_tuong_hanh_vi",
    "extract_ket_qua_thu_tuc",
    "extract_ket_qua_variants",
    "extract_thanh_phan_ho_so",
    "dossier_cues_in_text",
    "ket_qua_cue_present",
    "norm_space",
    "blank",
]
