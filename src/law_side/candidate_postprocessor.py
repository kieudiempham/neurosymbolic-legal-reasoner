"""Post-process normative candidates to be more frame-ready.

This module ONLY refines fields within the existing `NormativeSentence` schema.
It does not change `source_text` or add new columns.
"""

from __future__ import annotations

import re
from typing import Iterable

from law_side.law_rulebase_models import NormativeSentence


def _norm_space(s: str | None) -> str:
    t = (s or "").replace("\r\n", "\n").replace("\r", "\n")
    t = t.replace("\n", " ")
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _blank(s: str | None) -> bool:
    if s is None:
        return True
    t = str(s).strip()
    return t == "" or t.lower() == "nan"


_AUTHORITY_ENTITY_RE = re.compile(
    r"\b(cơ\s+quan\s+đăng\s+ký\s+kinh\s+doanh(?:\s+cấp\s+tỉnh)?|phòng\s+đăng\s+ký\s+kinh\s+doanh|"
    r"ủy\s+ban\s+nhân\s+dân|cơ\s+quan\s+nhà\s+nước\s+có\s+thẩm\s+quyền|ngân\s+hàng\s+nhà\s+nước)\b",
    re.I | re.U,
)

_CONDITION_HEAD_RE = re.compile(r"\b(nếu|khi|trường\s+hợp|đối\s+với)\b", re.I | re.U)
_EXCEPTION_HEAD_RE = re.compile(r"\b(trừ\s+trường\s+hợp|ngoại\s+trừ|trừ\s+khi|nếu\s+không)\b", re.I | re.U)


def _extract_condition_span(text: str) -> str | None:
    t = _norm_space(text)
    m = _CONDITION_HEAD_RE.search(t)
    if not m:
        return None
    chunk = t[m.start() : m.start() + 220]
    stop = re.search(
        r"[.;]\s+|,\s+(?:phải|được|không\s+được|nghiêm\s+cấm|trong\s+thời\s+hạn|hồ\s+sơ|"
        r"đăng\s*ký|thông\s*báo|gửi|nộp|công\s+bố|lưu\s+giữ)\b",
        chunk,
        flags=re.I | re.U,
    )
    if stop:
        chunk = chunk[: stop.start()]
    chunk = chunk.strip(" ,;:-")
    return chunk if len(chunk) >= 8 else None


def _extract_deadline_span(text: str) -> str | None:
    t = _norm_space(text)
    for pat in [
        r"(trong\s+(?:thời\s+hạn|vòng)\s*\d{1,3}\s*(?:ngày|tháng|năm)(?:\s+làm\s+việc)?[^.;]{0,90})",
        r"(chậm\s+nhất[^.;]{0,120})",
        r"(kể\s+từ\s+ngày[^.;]{0,140})",
        r"(\d{1,3}\s*(?:ngày|tháng|năm)(?:\s+làm\s+việc)?\s*kể\s+từ\s+ngày[^.;]{0,90})",
        r"(trong\s+(?:thời\s+hạn|vòng)[^.;]{0,80}?\bkể\s+từ\s+ngày[^.;]{0,90})",
    ]:
        m = re.search(pat, t, flags=re.I | re.U)
        if m:
            return m.group(1).strip()
    return None


def _extract_document_span(text: str) -> str | None:
    t = _norm_space(text)
    m = re.search(r"(hồ\s+sơ\s+bao\s+gồm[^.;]{0,260}|kèm\s+theo[^.;]{0,260}|thông\s+báo[^.;]{0,60}\bphải\s+bao\s+gồm\b[^.;]{0,220})", t, flags=re.I | re.U)
    if m:
        return m.group(1).strip()
    # Fallback: “gửi/nộp + hồ sơ/tài liệu/giấy tờ …”
    m2 = re.search(
        r"\b((?:gửi|nộp)\s+[^.;]{0,40}?\b(hồ\s+sơ|tài\s+liệu|giấy\s+tờ|danh\s+sách|nghị\s+quyết|quyết\s+định|biên\s+bản)[^.;]{0,180})",
        t,
        flags=re.I | re.U,
    )
    if m2:
        return m2.group(1).strip()
    # Additional procedural-document patterns.
    m3 = re.search(
        r"\b((?:công\s+bố|lưu\s+giữ|thông\s+báo)\s+[^.;]{0,60}?"
        r"\b(hồ\s+sơ|tài\s+liệu|giấy\s+tờ|danh\s+sách|nghị\s+quyết|quyết\s+định|biên\s+bản)\b[^.;]{0,140})",
        t,
        flags=re.I | re.U,
    )
    if m3:
        return m3.group(1).strip()
    # Last-resort: capture a bounded noun phrase centered at a document noun.
    m4 = re.search(
        r"\b((?:hồ\s+sơ|tài\s+liệu|giấy\s+tờ|danh\s+sách|nghị\s+quyết|quyết\s+định|biên\s+bản)"
        r"(?:\s+[^,.;]{1,80})?)\b",
        t,
        flags=re.I | re.U,
    )
    if not m4:
        return None
    s = m4.group(1).strip()
    # Avoid generic fragment "quyết định" alone when no legal doc context.
    if re.fullmatch(r"quyết\s+định", s, flags=re.I | re.U):
        if not re.search(r"\b(hồ\s+sơ|tài\s+liệu|giấy\s+tờ|danh\s+sách|nghị\s+quyết|biên\s+bản)\b", t, flags=re.I | re.U):
            return None
    return s


def _extract_exception_span(text: str) -> str | None:
    t = _norm_space(text)
    m = re.search(r"((?:trừ\s+trường\s+hợp|ngoại\s+trừ|trừ\s+khi|nếu\s+không)[^.;]{0,220})", t, flags=re.I | re.U)
    return m.group(1).strip() if m else None


def _extract_threshold_span(text: str) -> str | None:
    t = _norm_space(text)
    m = re.search(
        r"((?:không\s+quá|ít\s+nhất|trở\s+lên|từ)\s+[^.;]{0,120}|"
        r"\b\d{1,3}\s*%[^.;]{0,80}|\btỷ\s+lệ[^.;]{0,100}|\bphần\s+trăm[^.;]{0,100}|"
        r"\btừ\s+[^.;]{0,10}\s+đến\s+[^.;]{0,10}[^.;]{0,60})",
        t,
        flags=re.I | re.U,
    )
    return m.group(1).strip() if m else None


def _extract_legal_effect(text: str) -> str | None:
    t = _norm_space(text)
    m = re.search(
        r"\b(được\s+cấp[^.;]{0,160}|bị\s+thu\s+hồi[^.;]{0,160}|thu\s+hồi\s+Giấy[^.;]{0,160}|"
        r"được\s+công\s+bố[^.;]{0,160}|có\s+hiệu\s+lực[^.;]{0,160}|hết\s+hiệu\s+lực[^.;]{0,160}|"
        r"bị\s+tạm\s+ng(?:ừ|ư)ng[^.;]{0,160}|khôi\s+phục[^.;]{0,160}|chấp\s+thuận[^.;]{0,160}|"
        r"phải\s+đăng\s+ký\s+điều\s+chỉnh[^.;]{0,160}|bị\s+giải\s+thể[^.;]{0,160})",
        t,
        flags=re.I | re.U,
    )
    return m.group(1).strip() if m else None


def _extract_object_from_action(text: str, action_text: str | None) -> str | None:
    t = _norm_space(text)
    if action_text and not _blank(action_text):
        a = _norm_space(action_text)
        m = re.search(re.escape(a) + r"\s+([^.;]{5,120}?)(?=,|;|\.|$)", t, flags=re.I | re.U)
        if m:
            chunk = _norm_space(m.group(1))
            # Trim common lead-in noise
            chunk = re.sub(r"^(theo|trong|khi|nếu|đối\s+với)\s+", "", chunk, flags=re.I | re.U)
            if 5 <= len(chunk) <= 120 and not re.match(r"^(là|và|hoặc)\b", chunk, flags=re.I | re.U):
                return chunk
    # Known strong objects
    for pat in [
        r"\bGiấy\s+chứng\s+nhận\s+đăng\s+ký\s+doanh\s+nghiệp\b",
        r"\bnội\s+dung\s+đăng\s+ký\s+doanh\s+nghiệp\b",
        r"\bhồ\s+sơ\s+đăng\s+ký\s+doanh\s+nghiệp\b",
        r"\bĐiều\s+lệ\s+công\s+ty\b",
        r"\bvốn\s+điều\s+lệ\b",
        r"\bphần\s+vốn\s+góp\b",
        r"\bsổ\s+sách\s+kế\s+toán\b",
        r"\bcổ\s+đông\s+sáng\s+lập\b",
    ]:
        m = re.search(pat, t, flags=re.I | re.U)
        if m:
            return m.group(0)
    return None


def _score_and_extract(ns: NormativeSentence) -> None:
    """Update slots + score/decision in-place."""
    sent = _norm_space(ns.sentence_text)
    ctype = (ns.candidate_type or "").strip()

    # Fill condition/exception/threshold/deadline/document/legal_effect
    if _blank(ns.condition_text) and ctype in {"dieu_kien_ap_dung", "nguong_so_luong", "ngoai_le"}:
        ns.condition_text = _extract_condition_span(sent)
    if _blank(ns.condition_text) and _CONDITION_HEAD_RE.search(sent):
        # Allow conditional grounding for procedural/deadline candidates too.
        ns.condition_text = _extract_condition_span(sent)

    if _blank(ns.exception_text) and ctype == "ngoai_le":
        ns.exception_text = _extract_exception_span(sent)
    if _blank(ns.exception_text) and _EXCEPTION_HEAD_RE.search(sent):
        ns.exception_text = _extract_exception_span(sent)

    if _blank(ns.threshold_text) and ctype == "nguong_so_luong":
        ns.threshold_text = _extract_threshold_span(sent)

    if _blank(ns.deadline_text) and ctype == "thoi_han":
        ns.deadline_text = _extract_deadline_span(sent)

    if _blank(ns.document_text) and ctype in {"thanh_phan_ho_so", "thu_tuc"}:
        ns.document_text = _extract_document_span(sent)
    if _blank(ns.document_text) and re.search(r"\b(hồ\s+sơ|tài\s+liệu|giấy\s+tờ|danh\s+sách|nghị\s+quyết|quyết\s+định|biên\s+bản)\b", sent, flags=re.I | re.U):
        # Safe fallback: only fill when a document noun is present.
        ns.document_text = _extract_document_span(sent)

    if _blank(ns.legal_effect_text) and ctype == "ket_qua_phap_ly":
        ns.legal_effect_text = _extract_legal_effect(sent)
    if _blank(ns.legal_effect_text) and re.search(r"\b(được\s+cấp|bị\s+thu\s+hồi|có\s+hiệu\s+lực|hết\s+hiệu\s+lực|phải\s+đăng\s+ký\s+điều\s+chỉnh)\b", sent, flags=re.I | re.U):
        ns.legal_effect_text = _extract_legal_effect(sent)

    # authority_text: for authority-action candidates, require an entity mention
    if _blank(ns.authority_text) and ctype == "hanh_dong_co_quan":
        m = _AUTHORITY_ENTITY_RE.search(sent)
        if m:
            ns.authority_text = m.group(1).strip()

    # object_text: fill when possible
    if _blank(ns.object_text):
        ns.object_text = _extract_object_from_action(sent, ns.action_text)

    # candidate_score / should_extract_rule refinement
    strong_slot = False
    if ctype == "thoi_han":
        strong_slot = not _blank(ns.deadline_text)
    elif ctype == "thanh_phan_ho_so":
        strong_slot = not _blank(ns.document_text)
    elif ctype == "hanh_dong_co_quan":
        strong_slot = not _blank(ns.authority_text) and not _blank(ns.action_text)
    elif ctype == "ngoai_le":
        strong_slot = not _blank(ns.exception_text)
    elif ctype == "nguong_so_luong":
        strong_slot = not _blank(ns.threshold_text)
    elif ctype == "ket_qua_phap_ly":
        strong_slot = not _blank(ns.legal_effect_text)

    if strong_slot:
        ns.candidate_score = "rat_cao" if ns.candidate_score in {"", "thap", "trung_binh"} else ns.candidate_score
        ns.should_extract_rule = "co"
        ns.extraction_priority = ns.extraction_priority or "cao"
    else:
        # Keep existing labels if already set by detector; otherwise conservative.
        if not ns.candidate_score:
            ns.candidate_score = "trung_binh"
        if not ns.should_extract_rule:
            ns.should_extract_rule = "can_nhac"

    # Notes: keep short
    if ns.notes:
        if "post_slot_fill" not in ns.notes:
            ns.notes = ns.notes + "; post_slot_fill"
    else:
        ns.notes = "post_slot_fill"


def postprocess_candidates(normative_sentences: Iterable[NormativeSentence]) -> list[NormativeSentence]:
    out: list[NormativeSentence] = []
    for ns in normative_sentences:
        _score_and_extract(ns)
        out.append(ns)
    return out

