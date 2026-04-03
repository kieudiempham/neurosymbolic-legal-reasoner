"""Rule-based legal frame extraction (Stage 3).

Input: `NormativeSentence` candidates.
Output: `LegalFrame` objects aligned with review Excel schemas.

Precision-first tuning:
- better subject/action trimming
- deadline/doc extraction focused
- permission/status action predicate extracted near permission marker
"""

from __future__ import annotations

import re
from typing import Any

from law_side import candidate_postprocessor as _cp
from law_side.law_rulebase_models import LegalFrame, NormativeSentence
from law_side.rule_patterns import (
    AUTHORITY_TRIGGERS,
    CONDITION_TRIGGERS,
    DEADLINE_TRIGGERS,
    DOSSIER_TRIGGERS,
    OBLIGATION_TRIGGERS,
    PERMISSION_TRIGGERS,
    PROHIBITION_TRIGGERS,
    classify_modality,
)
from utils.ids import stable_hash
from utils.logger import get_logger


_COND_START_RE = re.compile(
    r"^\s*(nếu|khi|trường\s+hợp|đối\s+với|trừ\s+trường\s+hợp)\b",
    re.I | re.U,
)

_FORBIDDEN_ACTION_START_RE = re.compile(
    r"^\s*(luật|nghị\s*định|thông\s*tư|điều|khoản|trường\s+hợp|trong\s+thời\s+hạn|kể\s+từ\s+ngày|đối\s+với|sau\s+khi|trước\s+khi|nội\s+dung|hồ\s+sơ|bản\s+sao|giấy\s+tờ|thông\s+tin|cơ\s+quan|Luật\s+này|Nghị\s+định\s+này)\b",
    re.I | re.U,
)


# `candidate_type` (review sheet) → review `frame_type` (section D).
_CANDIDATE_TYPE_TO_VI_FRAME: dict[str, str] = {
    "thoi_han": "khung_thoi_han",
    "thanh_phan_ho_so": "khung_ho_so",
    "hanh_dong_co_quan": "khung_hanh_dong_co_quan",
    "ngoai_le": "khung_ngoai_le",
    "nguong_so_luong": "khung_nguong_dinh_luong",
    "ket_qua_phap_ly": "khung_ket_qua_phap_ly",
    "nghia_vu": "khung_nghia_vu",
    "quyen": "khung_quyen",
    "cam_doan": "khung_cam_doan",
    "thu_tuc": "khung_thu_tuc",
    "dieu_kien_ap_dung": "khung_dieu_kien",
}

# When internal typing returns `drop`, recover from `candidate_type` (English-ish internal types for extractors).
_CANDIDATE_TYPE_INTERNAL_RESCUE: dict[str, str] = {
    "ket_qua_phap_ly": "status_rule",
    "ngoai_le": "duty_rule",
    "nguong_so_luong": "duty_rule",
    "dieu_kien_ap_dung": "condition_rule",
    "thu_tuc": "procedure_rule",
    "thoi_han": "duty_rule",
    "thanh_phan_ho_so": "document_rule",
}


_ENTERPRISE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("công ty cổ phần", re.compile(r"\bcông\s+ty\s+cổ\s+phần\b", re.I | re.U)),
    ("công ty trách nhiệm hữu hạn", re.compile(r"\bcông\s+ty\s+trách\s+nhiệm\s+hữu\s+hạn\b", re.I | re.U)),
    ("người thành lập doanh nghiệp", re.compile(r"\bngười\s+thành\s+lập\s+doanh\s+nghiệp\b", re.I | re.U)),
    ("văn phòng đại diện", re.compile(r"\bvăn\s+phòng\s+đại\s+diện\b", re.I | re.U)),
    ("chi nhánh", re.compile(r"\bchi\s+nhánh\b", re.I | re.U)),
    ("công ty", re.compile(r"\bcông\s+ty\b", re.I | re.U)),
    ("doanh nghiệp", re.compile(r"\bdoanh\s+nghiệp\b", re.I | re.U)),
    ("người nộp", re.compile(r"\bngười\s+nộp\b", re.I | re.U)),
]

_AUTHORITY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("cơ quan đăng ký kinh doanh cấp tỉnh", re.compile(r"\bcơ\s+quan\s+đăng\s+ký\s+kinh\s+doanh\s+cấp\s+tỉnh\b", re.I | re.U)),
    ("cơ quan đăng ký kinh doanh", re.compile(r"\bcơ\s+quan\s+đăng\s+ký\s+kinh\s+doanh\b", re.I | re.U)),
    ("cơ quan thuế", re.compile(r"\bcơ\s+quan\s+thuế\b", re.I | re.U)),
]


def _first_regex_match(text: str, patterns: list[re.Pattern[str]]) -> re.Match[str] | None:
    best: re.Match[str] | None = None
    for rx in patterns:
        m = rx.search(text)
        if not m:
            continue
        if best is None or m.start() < best.start():
            best = m
    return best


def _truncate_at_first_stop(
    text: str,
    stop_patterns: list[re.Pattern[str]],
    *,
    fallback_max_chars: int,
) -> str:
    if len(text) > fallback_max_chars:
        text = text[:fallback_max_chars]
    best_pos: int | None = None
    for rx in stop_patterns:
        m = rx.search(text)
        if not m:
            continue
        if best_pos is None or m.start() < best_pos:
            best_pos = m.start()
    if best_pos is not None:
        return text[:best_pos].strip(" ,;:-")
    return text.strip(" ,;:-")


def _strip_leading_non_action(action: str | None) -> str | None:
    if not action:
        return None
    a = action.strip(" ,;:-")
    # Remove common explanatory lead-ins that rubric considers "not a central legal action".
    a2 = re.sub(
        r"^(quy\s+định|theo\s+quy\s+định)\s+(tại|của)\s+[^,.;]{0,90}[,.;]?\s*",
        "",
        a,
        flags=re.I | re.U,
    ).strip()
    # Remove "theo quy định của pháp luật ..." lead-in.
    a3 = re.sub(
        r"^(theo\s+quy\s+định\s+(của\s+)?pháp\s+luật)\s+[^,.;]{0,120}[,.;]?\s*",
        "",
        a2,
        flags=re.I | re.U,
    ).strip()
    # If the surface action is actually just the lead-in, reject.
    low = a3.lower()
    if low.startswith(("quy định", "theo quy định")):
        return None
    return a3 or None


def _clean_action_head(action: str | None) -> str | None:
    """Trim action to a central legal verb phrase."""
    if not action:
        return None
    a = re.sub(r"\s+", " ", action).strip(" ,;:-")
    if not a:
        return None
    # Drop common lead-in starts.
    a = re.sub(r"^(về\s+[^,.;]{0,140}[,.;]?\s*)", "", a, flags=re.I | re.U).strip(" ,;:-")
    a = re.sub(r"^(chính\s+xác\s+của\s+|tính\s+trung\s+thực,\s*chính\s+xác\s+của\s+)", "", a, flags=re.I | re.U).strip(" ,;:-")
    a = re.sub(r"^(đối\s+với\s+[^,.;]{0,120}[,.;]?\s*)", "", a, flags=re.I | re.U).strip(" ,;:-")
    a = re.sub(r"^(trong\s+thời\s+hạn[^,.;]{0,120}[,.;]?\s*)", "", a, flags=re.I | re.U).strip(" ,;:-")
    a = re.sub(r"^(kể\s+từ\s+ngày[^,.;]{0,120}[,.;]?\s*)", "", a, flags=re.I | re.U).strip(" ,;:-")

    # Re-anchor to first legal verb/action cue when action starts from complement phrase.
    head_patterns = [
        re.compile(r"\b(đăng\s*ký(\s+thay\s+đổi)?|thông\s*báo(\s+bằng\s+văn\s+bản)?|gửi(\s+hồ\s+sơ)?|cấp(\s+giấy\s+chứng\s+nhận)?|xem\s*xét(\s+tính\s+hợp\s+lệ\s+của\s+hồ\s+sơ)?|cập\s+nhật(\s+thông\s+tin)?|lưu\s+giữ|thu\s+hồi|khôi\s+phục|công\s+bố|tra\s+cứu|cung\s+cấp\s+thông\s+tin|ủy\s+quyền|yêu\s+cầu)\b", re.I | re.U),
        re.compile(r"\bchịu\s+trách\s+nhiệm\b", re.I | re.U),
    ]
    best = None
    for rx in head_patterns:
        m = rx.search(a)
        if m and (best is None or m.start() < best.start()):
            best = m
    if best and best.start() > 0:
        a = a[best.start() :].strip(" ,;:-")

    # Keep only before common trailing junk.
    for rx in [
        re.compile(r"\b(theo\s+quy\s+định|quy\s+định\s+tại)\b", re.I | re.U),
        re.compile(r"\b(là|bao\s+gồm)\b", re.I | re.U),
    ]:
        m = rx.search(a)
        if m:
            a = a[: m.start()].strip(" ,;:-")
    # Cut at punctuation boundaries to keep one central action.
    a = re.split(r"\s*[,;]\s*", a)[0].strip(" ,;:-")
    # Avoid conjunction tails and non-action tails.
    a = re.sub(r"\s+(và|hoặc)\s*$", "", a, flags=re.I | re.U).strip(" ,;:-")
    a = re.sub(r":\s*$", "", a).strip(" ,;:-")
    a = re.sub(r"\s+đã\s*$", "", a, flags=re.I | re.U).strip(" ,;:-")
    a = re.sub(r"\s+theo(\s+nguyên\s+tắc)?\s*$", "", a, flags=re.I | re.U).strip(" ,;:-")
    # False action: "cấp xã ..." is level adjective, not legal action head.
    if re.match(r"^cấp\s+xã\b", a, flags=re.I | re.U):
        return None
    if not a or len(a) < 6:
        return None
    return a


_ACTION_INTERNAL_CUTOFF_RE = re.compile(
    r"\b(quy\s+định|theo\s+quy\s+định)\s+(tại|của)\b",
    flags=re.I | re.U,
)


def _action_is_plausible(action: str | None) -> bool:
    if not action:
        return False
    low = action.lower().strip()
    # Rubric hard-triggers for wrong_action.
    if "luật" in low or "điều" in low:
        return False
    if re.match(r"^(trường\s+hợp|trong\s+thời\s+hạn|kể\s+từ\s+ngày)\b", low, flags=re.I | re.U):
        return False
    if re.match(r"^(về|đối\s+với|theo|nội\s+dung|thông\s+tin|hồ\s+sơ|phiếu|giấy\s+tờ)\b", low, flags=re.I | re.U):
        return False
    if low.endswith((" và", " hoặc")):
        return False
    if low.endswith((" đã", " theo", " theo nguyên tắc")):
        return False
    if re.search(r"\b(là|bao gồm)\b", low, flags=re.I | re.U):
        return False
    return True


def _extract_action_from_anchor(
    sentence_text: str,
    anchor_patterns: list[re.Pattern[str]],
    stop_patterns: list[re.Pattern[str]],
    *,
    max_chars: int,
) -> str | None:
    """Extract a short action phrase starting at the earliest anchor match."""
    earliest: re.Match[str] | None = None
    for rx in anchor_patterns:
        m = rx.search(sentence_text)
        if not m:
            continue
        if earliest is None or m.start() < earliest.start():
            earliest = m
    if not earliest:
        return None
    start = earliest.start()
    chunk = sentence_text[start : start + max_chars].strip()
    if not chunk:
        return None
    # Truncate at first stop cue inside the chunk.
    for stop_rx in stop_patterns:
        sm = stop_rx.search(chunk)
        if sm:
            chunk = chunk[: sm.start()].strip(" ,;:-")
            break
    chunk = _strip_leading_non_action(chunk)
    return chunk if _action_is_plausible(chunk) else None


def _clean_text(s: str | None, *, max_chars: int) -> str | None:
    if not s:
        return None
    s2 = re.sub(r"\s+", " ", s).strip()
    if len(s2) > max_chars:
        s2 = s2[: max_chars].rsplit(" ", 1)[0].strip() if " " in s2[: max_chars] else s2[:max_chars].strip()
    return s2 or None


class LegalFrameExtractor:
    """Extracts `LegalFrame` objects from `NormativeSentence` candidates."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or {}
        self._log = get_logger(self.__class__.__name__)

        self._max_condition_chars = int(self._config.get("max_condition_chars", 220))
        self._max_action_chars = int(self._config.get("max_action_chars", 220))
        self._max_required_docs_chars = int(self._config.get("max_required_docs_chars", 380))

        self._condition_triggers = [t.regex for t in CONDITION_TRIGGERS]
        self._deadline_triggers = [t.regex for t in DEADLINE_TRIGGERS]
        self._dossier_triggers = [t.regex for t in DOSSIER_TRIGGERS]
        self._authority_triggers = [t.regex for t in AUTHORITY_TRIGGERS]

        # Action extraction stops (precision-first): avoid swallowing deadlines/conditions/docs
        # and avoid lead-in phrases that rubric marks as wrong_action.
        self._action_stop_patterns: list[re.Pattern[str]] = [
            re.compile(r"\b(trong\s+(thời\s+hạn|vòng)|kể\s+từ\s+ngày|chậm\s+nhất)\b", re.I | re.U),
            re.compile(r"\b(trường\s+hợp|nếu)\b", re.I | re.U),
            re.compile(r"\b(kèm\s+theo|hồ\s+sơ\s+bao\s+gồm|bao\s+gồm\s+các\s+giấy\s+tờ|bao\s+gồm\s+các\s+tài\s+liệu)\b", re.I | re.U),
            re.compile(r"\b(đến\s+cơ\s+quan|cho\s+doanh\s+nghiệp)\b", re.I | re.U),
            re.compile(r"\btheo\s+quy\s+định\b", re.I | re.U),
        ]

        # Desired legal action anchors (from your rubric prompt).
        self._action_anchors_common: list[re.Pattern[str]] = [
            re.compile(r"\bđăng\s*ký\b", re.I | re.U),
            re.compile(r"\bthông\s*báo\s+bằng\s*văn\s+bản\b", re.I | re.U),
            re.compile(r"\bthông\s*báo\b", re.I | re.U),
            re.compile(r"\bgửi\s*hồ\s+sơ\b", re.I | re.U),
            re.compile(r"\bcấp\s+giấy\s+chứng\s+nhận\b", re.I | re.U),
            re.compile(r"\bcấp\b", re.I | re.U),
            re.compile(r"\bcập\s+nhật\s+thông\s+tin\b", re.I | re.U),
            re.compile(r"\bcập\s+nhật\b", re.I | re.U),
            re.compile(r"\blưu\s+giữ\b", re.I | re.U),
            re.compile(r"\byêu\s+cầu\b", re.I | re.U),
            re.compile(r"\bthu\s+hồi\b", re.I | re.U),
            re.compile(r"\bkhôi\s+phục\b", re.I | re.U),
            re.compile(r"\bxem\s+xét\s+tính\s+hợp\s+lệ\s+của\s+hồ\s+sơ\b", re.I | re.U),
            re.compile(r"\bxem\s*xét\s+tính\s+hợp\s*lệ\b", re.I | re.U),
        ]

        self._action_anchors_authority: list[re.Pattern[str]] = [
            re.compile(r"\bxem\s*xét\s+tính\s+hợp\s*lệ\s+của\s+hồ\s+sơ\b", re.I | re.U),
            re.compile(r"\bcấp\s+giấy\s+chứng\s+nhận\b", re.I | re.U),
            re.compile(r"\bthông\s*báo\s+bằng\s*văn\s+bản\b", re.I | re.U),
            re.compile(r"\bcập\s+nhật\s+thông\s+tin\b", re.I | re.U),
            re.compile(r"\bcập\s+nhật\b", re.I | re.U),
            re.compile(r"\bxem\s*xét\b", re.I | re.U),
        ]

        self._action_anchors_status: list[re.Pattern[str]] = [
            # In permission/status frames, the desired legal action is usually still one
            # of the common central anchors.
            re.compile(r"\bđăng\s*ký\b", re.I | re.U),
            re.compile(r"\bthông\s*báo\b", re.I | re.U),
            re.compile(r"\bgửi\s*hồ\s+sơ\b", re.I | re.U),
            re.compile(r"\bcấp\s+giấy\s+chứng\s+nhận\b", re.I | re.U),
            re.compile(r"\bcập\s+nhật\s+thông\s+tin\b", re.I | re.U),
            re.compile(r"\blưu\s+giữ\b", re.I | re.U),
            re.compile(r"\bxem\s*xét\s+tính\s+hợp\s*lệ\b", re.I | re.U),
        ]

    def _grounded_extraction_text(self, ns: NormativeSentence) -> str:
        s = (getattr(ns, "source_text", None) or "").strip()
        raw = s if s else (ns.sentence_text or "")
        return re.sub(r"\s+", " ", raw).strip()

    def _canonical_source_for_review(self, ns: NormativeSentence) -> str:
        st = (getattr(ns, "source_text", None) or "").strip()
        return st if st else (ns.sentence_text or "").strip()

    def _deadline_context_action(self, sentence_text: str) -> str | None:
        m = re.search(
            r"([^.;]{12,180}?)\s+(?:trong\s+(?:thời\s+hạn|vòng)|chậm\s+nhất|kể\s+từ\s+ngày)\b",
            sentence_text,
            flags=re.I | re.U,
        )
        if not m:
            return None
        cand = _clean_action_head(m.group(1).strip())
        return _clean_text(cand, max_chars=self._max_action_chars) if _action_is_plausible(cand) else None

    def _grounded_ket_qua(self, ns: NormativeSentence, sentence_text: str) -> str | None:
        raw = (getattr(ns, "legal_effect_text", None) or "").strip()
        if raw and not self._is_abstract_ket_qua(raw):
            return _clean_text(raw, max_chars=320)
        fx = _cp._extract_legal_effect(sentence_text)
        if fx:
            return _clean_text(fx, max_chars=320)
        return None

    def _is_abstract_ket_qua(self, s: str) -> bool:
        low = s.strip().lower()
        return low in {
            "phải thực hiện",
            "được xử lý",
            "có kết quả",
            "được phép thực hiện",
            "không được thực hiện",
            "trạng thái có thể thay đổi",
        } or ("thực hiện" in low and len(low) < 28)

    def _resolve_object_text(
        self,
        ns: NormativeSentence,
        sentence_text: str,
        action_predicate: str | None,
    ) -> str | None:
        obj0 = getattr(ns, "object_text", None)
        s0 = (str(obj0).strip() if obj0 is not None else "") or ""
        weak = (len(s0) < 5) or bool(
            re.fullmatch(
                r"(?:điều\s+lệ|yêu\s+cầu|nội\s+dung|quyết\s+định)",
                s0,
                flags=re.I | re.U,
            )
        )
        if not weak and s0:
            return _clean_text(s0, max_chars=200)
        from_act = _cp._extract_object_from_action(sentence_text, action_predicate)
        if from_act:
            return _clean_text(from_act, max_chars=200)
        return self._extract_object_from_text(sentence_text)

    def _merge_threshold_from_candidate(
        self,
        ns: NormativeSentence,
        *,
        nguong_so_luong: str | None,
        nguong_ty_le: str | None,
        khoang_gia_tri: str | None,
        dieu_kien_dinh_luong: str | None,
    ) -> tuple[str | None, str | None, str | None, str | None]:
        th = (getattr(ns, "threshold_text", None) or "").strip()
        if not th:
            return nguong_so_luong, nguong_ty_le, khoang_gia_tri, dieu_kien_dinh_luong
        if nguong_so_luong or nguong_ty_le or khoang_gia_tri:
            return nguong_so_luong, nguong_ty_le, khoang_gia_tri, dieu_kien_dinh_luong
        dieu_kien_dinh_luong = dieu_kien_dinh_luong or th
        if "%" in th or re.search(r"tỷ\s+lệ|phần\s+trăm", th, flags=re.I | re.U):
            nguong_ty_le = th
        elif re.search(r"\btừ\b.*\bđến\b", th, flags=re.I | re.U):
            khoang_gia_tri = th
        else:
            nguong_so_luong = th
        return nguong_so_luong, nguong_ty_le, khoang_gia_tri, dieu_kien_dinh_luong

    def _co_quan_split(
        self,
        recipient_authority: str | None,
        subject_type: str,
        sentence_text: str,
        frame_type: str,
    ) -> tuple[str | None, str | None]:
        tiep = recipient_authority
        xu_ly: str | None = None
        st = sentence_text or ""
        low_subj = (subject_type or "").lower()
        if "cơ quan" in low_subj:
            xu_ly = subject_type
        if recipient_authority:
            if re.search(r"\b(gửi|nộp|tiếp\s+nhận|đến)\b", st, flags=re.I | re.U):
                tiep = recipient_authority
            if re.search(
                r"\b(cấp|thu\s+hồi|xem\s+xét|từ\s+chối|cập\s+nhật|giải\s+quyết)\b",
                st,
                flags=re.I | re.U,
            ):
                xu_ly = recipient_authority
        if frame_type == "authority_action":
            xu_ly = xu_ly or (subject_type if "cơ quan" in low_subj else recipient_authority)
        return tiep, xu_ly

    def extract(self, candidates: list[NormativeSentence]) -> list[LegalFrame]:
        out: list[LegalFrame] = []
        for ns in candidates:
            sentence_text = self._grounded_extraction_text(ns)
            if not sentence_text:
                continue
            canonical_source = self._canonical_source_for_review(ns)
            ct = (ns.candidate_type or "").strip().lower()

            frame_type = self._map_candidate_rule_type_to_frame_type(ns.candidate_rule_type, sentence_text)
            if frame_type == "drop":
                frame_type = _CANDIDATE_TYPE_INTERNAL_RESCUE.get(ct, "drop")
            if frame_type == "drop":
                continue

            subject_type, subject_role = self._extract_subject(ns, sentence_text, frame_type)
            frame_type = self._normalize_frame_type_by_subject(frame_type, subject_type, sentence_text)
            modality = self._infer_modality(frame_type, sentence_text)

            trigger_event = self._extract_trigger_event(ns, frame_type)
            condition_predicates = self._extract_condition_predicates(ns, sentence_text)
            deadline_value, deadline_unit, deadline_anchor = self._extract_deadline(sentence_text)
            required_documents = self._extract_required_documents(ns, sentence_text, frame_type)
            action_predicate = self._extract_action_predicate(ns, sentence_text, frame_type)
            if not action_predicate and ct == "thoi_han":
                action_predicate = self._deadline_context_action(sentence_text)
            recipient_authority = self._extract_recipient_authority(ns, sentence_text, frame_type)

            exception_text = self._extract_exception(sentence_text)
            if not exception_text and getattr(ns, "exception_text", None):
                ex0 = str(ns.exception_text).strip()
                if ex0 and len(ex0) >= 8:
                    exception_text = ex0
                else:
                    exception_text = _cp._extract_exception_span(sentence_text)

            legal_effect_abstract = self._infer_legal_effect(frame_type, modality)
            ket_qua_grounded = self._grounded_ket_qua(ns, sentence_text)
            ket_qua_slot = ket_qua_grounded or (None if self._is_abstract_ket_qua(legal_effect_abstract) else legal_effect_abstract)

            doi_tuong = self._resolve_object_text(ns, sentence_text, action_predicate)

            nguong_so_luong, nguong_ty_le, khoang_gia_tri, dieu_kien_dinh_luong = self._extract_quantitative_slots(sentence_text)
            nguong_so_luong, nguong_ty_le, khoang_gia_tri, dieu_kien_dinh_luong = self._merge_threshold_from_candidate(
                ns,
                nguong_so_luong=nguong_so_luong,
                nguong_ty_le=nguong_ty_le,
                khoang_gia_tri=khoang_gia_tri,
                dieu_kien_dinh_luong=dieu_kien_dinh_luong,
            )

            ng_ok = bool(nguong_so_luong or nguong_ty_le or khoang_gia_tri or (dieu_kien_dinh_luong and ct == "nguong_so_luong"))
            output_status, quality_note = self._assess_frame_quality(
                ns=ns,
                frame_type=frame_type,
                subject_type=subject_type,
                action_predicate=action_predicate,
                deadline_value=deadline_value,
                sentence_text=sentence_text,
                required_documents=required_documents,
                exception_text=exception_text,
                condition_predicates=condition_predicates,
                candidate_type=ct,
                ket_qua_grounded=ket_qua_slot,
                nguong_ok=ng_ok,
            )
            if output_status == "dropped":
                continue

            frame_type_out = self._to_vi_frame_type(frame_type)
            if ct in _CANDIDATE_TYPE_TO_VI_FRAME:
                frame_type_out = _CANDIDATE_TYPE_TO_VI_FRAME[ct]
            modality_out = self._to_vi_modality(modality)
            if frame_type_out == "khung_cam_doan":
                modality_out = "bi_cam"
            frame_id = self._make_frame_id(
                unit_ref_full=getattr(ns, "unit_ref_full", "") or "",
                candidate_id=getattr(ns, "candidate_id", "") or ns.ns_id,
                frame_type=frame_type_out,
                action_predicate=action_predicate,
                doc_code=getattr(ns, "doc_code", "") or "",
                suffix="",
            )
            van_ban_dan_chieu = self._extract_van_ban_dan_chieu(sentence_text)
            can_tach_them, ly_do_can_tach = self._split_flags(sentence_text, action_predicate, required_documents, deadline_value, exception_text)
            co_tiep, co_xu_ly = self._co_quan_split(recipient_authority, subject_type, sentence_text, frame_type)
            notes_bits = [quality_note]
            if ct:
                notes_bits.append(f"candidate_type={ct}")
            if canonical_source != sentence_text:
                notes_bits.append("grounded_on_source_text")
            ghi_chu = "; ".join(x for x in notes_bits if x)
            muc_do_day_du = self._muc_do_day_du_rich(
                chu_the=subject_type,
                hanh_vi=action_predicate,
                doi_tuong=doi_tuong,
                tinh_chat=self._to_tinh_chat_phap_ly(modality_out, frame_type_out),
                dieu_kien_ap_dung=condition_predicates,
                thanh_phan_ho_so=required_documents,
                thoi_han_so=deadline_value,
                co_quan=recipient_authority,
                ngoai_le=exception_text,
                ket_qua=ket_qua_slot,
            )

            heading = (getattr(ns, "heading", None) or "").strip()
            parent_context = (getattr(ns, "parent_context", None) or "").strip()

            main_frame = LegalFrame(
                frame_id=frame_id,
                ns_id=ns.ns_id,
                candidate_id=getattr(ns, "candidate_id", "") or ns.ns_id,
                source_unit_id=ns.unit_id,
                doc_id=ns.doc_id,
                doc_code=getattr(ns, "doc_code", ""),
                unit_ref_full=getattr(ns, "unit_ref_full", ""),
                source_ref=ns.source_ref,
                heading=heading,
                parent_context=parent_context,
                source_text=canonical_source,
                frame_type=frame_type_out,
                subject_type=subject_type,
                subject_role=subject_role,
                trigger_event=trigger_event,
                condition_predicates=condition_predicates,
                action_predicate=action_predicate,
                modality=modality_out,
                deadline_value=deadline_value,
                deadline_unit=deadline_unit,
                deadline_anchor=deadline_anchor,
                required_documents=required_documents,
                recipient_authority=recipient_authority,
                legal_effect=ket_qua_slot or legal_effect_abstract,
                exception_text=exception_text,
                output_status=output_status,
                chu_the=subject_type,
                vai_tro_chu_the=self._to_vai_tro_chu_the(subject_role),
                hanh_vi=action_predicate,
                doi_tuong_hanh_vi=doi_tuong,
                tinh_chat_phap_ly=self._to_tinh_chat_phap_ly(modality_out, frame_type_out),
                dieu_kien_ap_dung=condition_predicates,
                dieu_kien_dinh_luong=dieu_kien_dinh_luong,
                nguong_so_luong=nguong_so_luong,
                nguong_ty_le=nguong_ty_le,
                khoang_gia_tri=khoang_gia_tri,
                thanh_phan_ho_so=required_documents,
                co_quan_tiep_nhan=co_tiep,
                co_quan_xu_ly=co_xu_ly,
                ket_qua_thu_tuc=ket_qua_slot,
                thoi_han_so=deadline_value,
                don_vi_thoi_han=self._to_vi_deadline_unit(deadline_unit),
                moc_tinh_thoi_han=self._to_vi_deadline_anchor(deadline_anchor),
                ngoai_le=exception_text,
                van_ban_dan_chieu=van_ban_dan_chieu,
                ghi_chu_giai_thich=ghi_chu,
                muc_do_day_du=muc_do_day_du,
                can_tach_them=can_tach_them,
                ly_do_can_tach=ly_do_can_tach,
                notes=f"{ns.notes}; frame_type={frame_type_out}; {ghi_chu}",
            )
            out.append(main_frame)

            if (
                exception_text
                and len(exception_text) >= 14
                and ct != "ngoai_le"
                and frame_type_out != "khung_ngoai_le"
            ):
                ex_id = self._make_frame_id(
                    unit_ref_full=getattr(ns, "unit_ref_full", "") or "",
                    candidate_id=getattr(ns, "candidate_id", "") or ns.ns_id,
                    frame_type="khung_ngoai_le",
                    action_predicate="ngoai_le",
                    doc_code=getattr(ns, "doc_code", "") or "",
                    suffix="NGOAI_LE",
                )
                out.append(
                    LegalFrame(
                        frame_id=ex_id,
                        ns_id=ns.ns_id,
                        candidate_id=getattr(ns, "candidate_id", "") or ns.ns_id,
                        source_unit_id=ns.unit_id,
                        doc_id=ns.doc_id,
                        doc_code=getattr(ns, "doc_code", ""),
                        unit_ref_full=getattr(ns, "unit_ref_full", ""),
                        source_ref=ns.source_ref,
                        heading=heading,
                        parent_context=parent_context,
                        source_text=canonical_source,
                        frame_type="khung_ngoai_le",
                        subject_type=subject_type,
                        subject_role=subject_role,
                        trigger_event=None,
                        condition_predicates=None,
                        action_predicate="xác định phạm vi ngoại lệ",
                        modality="bat_buoc",
                        deadline_value=None,
                        deadline_unit=None,
                        deadline_anchor=None,
                        required_documents=None,
                        recipient_authority=recipient_authority,
                        legal_effect=None,
                        exception_text=exception_text,
                        output_status="seed_extracted_first_pass",
                        chu_the=subject_type,
                        vai_tro_chu_the=self._to_vai_tro_chu_the(subject_role),
                        hanh_vi="áp dụng quy định loại trừ",
                        doi_tuong_hanh_vi=None,
                        tinh_chat_phap_ly="bat_buoc",
                        dieu_kien_ap_dung=None,
                        dieu_kien_dinh_luong=None,
                        nguong_so_luong=None,
                        nguong_ty_le=None,
                        khoang_gia_tri=None,
                        thanh_phan_ho_so=None,
                        co_quan_tiep_nhan=co_tiep,
                        co_quan_xu_ly=co_xu_ly,
                        ket_qua_thu_tuc=None,
                        thoi_han_so=None,
                        don_vi_thoi_han=None,
                        moc_tinh_thoi_han=None,
                        ngoai_le=exception_text,
                        van_ban_dan_chieu=van_ban_dan_chieu,
                        ghi_chu_giai_thich="bo_sung_ngoai_le_tu_van_ban_goc;tach_frame_ngoai_le",
                        muc_do_day_du="kha_day_du",
                        can_tach_them="khong",
                        ly_do_can_tach=None,
                        notes=f"{ns.notes}; derived_ngoai_le; main_frame={frame_id}",
                    )
                )

        self._log.info("Extracted %d legal frames", len(out))
        return out

    def _normalize_frame_type_by_subject(self, frame_type: str, subject_type: str, sentence_text: str) -> str:
        if frame_type != "authority_action":
            return frame_type
        low_subject = (subject_type or "").strip().lower()
        is_authority_subject = any(
            k in low_subject for k in ("cơ quan", "ủy ban", "bộ", "sở", "phòng", "tòa án")
        )
        if is_authority_subject:
            return frame_type
        # Non-authority subject should not stay in authority_action.
        if re.search(r"\b(phải|có\s+trách\s+nhiệm|chịu\s+trách\s+nhiệm|thông\s+báo|đăng\s+ký|gửi)\b", sentence_text, flags=re.I | re.U):
            return "duty_rule"
        return "procedure_rule"

    def _map_candidate_rule_type_to_frame_type(self, candidate_rule_type: str, sentence_text: str) -> str:
        # Strong document-composition cues should always be `document_rule`.
        if any(trig.regex.search(sentence_text) for trig in DOSSIER_TRIGGERS):
            return "document_rule"

        if self._is_definition_like(sentence_text):
            return "drop"

        t_raw = (candidate_rule_type or "").strip().lower()
        # Review Excel uses Vietnamese `quy_pham_*` tokens; normalize to detector-internal types first.
        vi_to_internal: dict[str, str] = {
            "quy_pham_thu_tuc": "procedure_rule",
            "quy_pham_ho_so": "document_requirement",
            "quy_pham_nghia_vu": "duty",
            "quy_pham_cam": "prohibition",
            "quy_pham_quyen": "permission",
            "quy_pham_thoi_han": "deadline",
            "quy_pham_trang_thai": "status_rule",
            "quy_pham_dieu_kien": "condition",
            "hanh_dong_co_quan": "authority_action",
        }
        t = vi_to_internal.get(t_raw, t_raw)
        if t in {"duty", "registration_obligation"}:
            return "duty_rule"
        if t == "deadline":
            return "duty_rule"
        if t == "document_requirement":
            return "document_rule"
        if t == "authority_action":
            return "authority_action"
        if t in {"procedure_rule", "procedure"}:
            return "procedure_rule"
        if t == "condition":
            return "condition_rule"
        if t == "status_rule":
            return "status_rule"
        if t == "permission":
            # Keep procedure only for explicit actionable permission.
            if re.search(r"\b(có\s+quyền|có\s+thể|được\s+phép)\b", sentence_text, flags=re.I | re.U):
                return "procedure_rule"
            return "drop"
        if t == "notification":
            return "duty_rule"
        if t == "prohibition":
            return "duty_rule"

        # Fallback to cues.
        mod = classify_modality(sentence_text)
        if mod == "permission":
            if re.search(r"\b(có\s+quyền|có\s+thể|được\s+phép)\b", sentence_text, flags=re.I | re.U):
                return "procedure_rule"
            return "drop"
        if any(rx.search(sentence_text) for rx in self._authority_triggers):
            return "authority_action"
        if any(rx.search(sentence_text) for rx in self._dossier_triggers):
            return "document_rule"
        if mod in {"obligation", "prohibition"}:
            return "duty_rule"
        return "drop"

    def _infer_modality(self, frame_type: str, sentence_text: str) -> str:
        mod = classify_modality(sentence_text)
        if mod in {"obligation", "prohibition", "permission"}:
            return mod
        if frame_type == "status_rule":
            return "permission"
        return "obligation"

    def _extract_subject(self, ns: NormativeSentence, sentence_text: str, frame_type: str) -> tuple[str, str]:
        if ns.subject_span:
            from_span = self._find_first_by_patterns(ns.subject_span, _AUTHORITY_PATTERNS + _ENTERPRISE_PATTERNS)
            if from_span:
                if from_span == "người nộp":
                    return "người thành lập doanh nghiệp", "chủ thể nghĩa vụ"
                if from_span in {"cơ quan đăng ký kinh doanh", "cơ quan đăng ký kinh doanh cấp tỉnh", "cơ quan thuế"}:
                    return from_span, "cơ quan xử lý"
                return from_span, "chủ thể nghĩa vụ" if frame_type in {"duty_rule", "procedure_rule"} else "chủ thể thực hiện"

        if frame_type == "authority_action":
            auth = self._find_first_by_patterns(sentence_text, _AUTHORITY_PATTERNS)
            if auth:
                return auth, "cơ quan xử lý"
            return "cơ quan đăng ký kinh doanh", "cơ quan xử lý"

        ent = self._find_first_by_patterns(sentence_text, _ENTERPRISE_PATTERNS)
        if ent:
            if ent == "người nộp":
                return "người thành lập doanh nghiệp", "chủ thể nghĩa vụ"
            if ent == "người thành lập doanh nghiệp":
                return ent, "chủ thể nghĩa vụ"
            return ent, "chủ thể nghĩa vụ" if frame_type in {"duty_rule", "procedure_rule"} else "chủ thể thực hiện"

        if frame_type == "document_rule":
            return "doanh nghiệp", "chủ thể thực hiện"
        return "Unknown", "unknown"

    def _find_first_by_patterns(self, text: str, patterns: list[tuple[str, re.Pattern[str]]]) -> str | None:
        for label, rx in patterns:
            if rx.search(text):
                return label
        return None

    def _extract_trigger_event(self, ns: NormativeSentence, frame_type: str) -> str | None:
        text = ns.sentence_text
        event_map: list[tuple[str, str]] = [
            (r"\bđăng\s+ký\s+thay\s+đổi\b", "thay đổi nội dung đăng ký doanh nghiệp"),
            (r"\bthành\s+lập\s+chi\s+nhánh\b", "thành lập chi nhánh"),
            (r"\bthay\s+đổi\s+địa\s+chỉ\s+trụ\s+sở\b", "thay đổi địa chỉ trụ sở chính"),
            (r"\bchủ\s+sở\s+hưởng\s+lợi\b", "thay đổi thông tin chủ sở hữu hưởng lợi"),
            (r"\bđăng\s+ký\b", "đăng ký doanh nghiệp"),
            (r"\bthông\s+báo\b", "thông báo"),
            (r"\bgửi\s+hồ\s+sơ\b", "gửi hồ sơ"),
            (r"\bcấp\s+giấy\s+chứng\s+nhận\b", "cấp giấy chứng nhận"),
            (r"\bcập\s+nhật\b", "cập nhật thông tin"),
            (r"\bthu\s+hồi\b", "thu hồi"),
            (r"\bkhôi\s+phục\b", "khôi phục"),
        ]
        low = text.lower()
        for pat, label in event_map:
            if re.search(pat, low, flags=re.I | re.U):
                return label
        if frame_type == "document_rule":
            return "chuẩn bị hồ sơ đăng ký"
        if ns.action_span:
            return _clean_text(ns.action_span, max_chars=80)
        return None

    def _extract_action_predicate(self, ns: NormativeSentence, sentence_text: str, frame_type: str) -> str | None:
        if frame_type == "document_rule":
            if re.search(r"\bkèm\s+theo\s+hồ\s+sơ\b", sentence_text, flags=re.I | re.U):
                return "kèm theo hồ sơ"
            if re.search(r"\bhồ\s+sơ\s+bao\s+gồm\b", sentence_text, flags=re.I | re.U):
                return "hồ sơ bao gồm"
            return "thành phần hồ sơ"

        if frame_type == "status_rule":
            # Permission/status: extract near the permission marker, but re-anchor to central
            # verbs if the extracted span is polluted by lead-in explanations ("quy định tại ...").
            perm_match = _first_regex_match(sentence_text, [t.regex for t in PERMISSION_TRIGGERS])
            window = sentence_text[perm_match.end() :].strip() if perm_match else sentence_text

            # First attempt: simple truncation after permission.
            action1 = _truncate_at_first_stop(
                window,
                stop_patterns=self._action_stop_patterns + self._condition_triggers + self._deadline_triggers,
                fallback_max_chars=self._max_action_chars,
            )
            action1 = _strip_leading_non_action(action1)
            action1 = _clean_action_head(action1)
            if _action_is_plausible(action1):
                return _clean_text(action1, max_chars=self._max_action_chars)

            # Second attempt: find the earliest desired central action anchor inside the window.
            action2 = _extract_action_from_anchor(
                window,
                self._action_anchors_status,
                stop_patterns=self._action_stop_patterns,
                max_chars=self._max_action_chars,
            )
            action2 = _clean_action_head(action2)
            return _clean_text(action2, max_chars=self._max_action_chars) if action2 else None

        if frame_type == "authority_action":
            return self._extract_action_near_authority_triggers(sentence_text)

        if frame_type == "condition_rule":
            m_thi = re.search(r"\bthì\s+(.+)", sentence_text, flags=re.I | re.U)
            if m_thi:
                tail = m_thi.group(1).strip()
                action = _truncate_at_first_stop(
                    tail,
                    stop_patterns=self._action_stop_patterns + self._deadline_triggers + self._dossier_triggers,
                    fallback_max_chars=self._max_action_chars,
                )
                action = _strip_leading_non_action(action)
                action = _clean_action_head(action)
                if _action_is_plausible(action) and action and not _FORBIDDEN_ACTION_START_RE.search(action):
                    return _clean_text(action, max_chars=self._max_action_chars)
            if ns.action_span:
                cand = _clean_text(ns.action_span.strip(), max_chars=self._max_action_chars)
                if cand and _action_is_plausible(cand):
                    return cand
            return None

        # duty_rule / procedure_rule
        # Prefer ns.action_span when it's already anchored at a legal verb, but cut off
        # internal lead-in fragments ("quy định tại...") that create wrong_action.
        if ns.action_span:
            cand = ns.action_span.strip()
            cand = _strip_leading_non_action(cand)
            # Cut at internal "quy định..." lead-ins.
            q = _ACTION_INTERNAL_CUTOFF_RE.search(cand or "")
            if q:
                cand = cand[: q.start()].strip(" ,;:-")
            cand = _clean_action_head(cand)
            if _action_is_plausible(cand) and cand and not _FORBIDDEN_ACTION_START_RE.search(cand):
                return _clean_text(cand, max_chars=self._max_action_chars)

        # Fallback: extract after the first deontic marker.
        m = _first_regex_match(sentence_text, [t.regex for t in OBLIGATION_TRIGGERS + PROHIBITION_TRIGGERS + PERMISSION_TRIGGERS])
        if m:
            after = sentence_text[m.end() :].strip()
            action = _truncate_at_first_stop(
                after,
                stop_patterns=self._action_stop_patterns + self._condition_triggers + self._deadline_triggers + self._dossier_triggers + self._authority_triggers,
                fallback_max_chars=self._max_action_chars,
            )
            action = _strip_leading_non_action(action)
            action = _clean_action_head(action)
            if _action_is_plausible(action) and action and not _FORBIDDEN_ACTION_START_RE.search(action):
                return _clean_text(action, max_chars=self._max_action_chars)

            # If polluted, re-anchor by common legal action anchors.
            action2 = _extract_action_from_anchor(
                after,
                self._action_anchors_common,
                stop_patterns=self._action_stop_patterns,
                max_chars=self._max_action_chars,
            )
            action2 = _clean_action_head(action2)
            return _clean_text(action2, max_chars=self._max_action_chars) if action2 else None

        return None

    def _extract_action_near_authority_triggers(self, sentence_text: str) -> str | None:
        verb_patterns = [
            re.compile(r"\bxem\s*xét\b", re.I | re.U),
            re.compile(r"\bcấp\b", re.I | re.U),
            re.compile(r"\bthông\s*báo\b", re.I | re.U),
            re.compile(r"\btừ\s*chối\b", re.I | re.U),
            re.compile(r"\bcập\s*nhật\b", re.I | re.U),
        ]
        m = _first_regex_match(sentence_text, verb_patterns)
        if not m:
            return None

        after = sentence_text[m.start() :].strip()
        action = _truncate_at_first_stop(
            after,
            stop_patterns=self._action_stop_patterns + self._condition_triggers + self._deadline_triggers + self._dossier_triggers,
            fallback_max_chars=self._max_action_chars,
        )
        action = _strip_leading_non_action(action)
        action = _clean_action_head(action)
        if _action_is_plausible(action) and action and not _FORBIDDEN_ACTION_START_RE.search(action):
            return _clean_text(action, max_chars=self._max_action_chars)

        # Re-anchor to authority-preferred actions if first attempt is polluted.
        action2 = _extract_action_from_anchor(
            after,
            self._action_anchors_authority,
            stop_patterns=self._action_stop_patterns,
            max_chars=self._max_action_chars,
        )
        action2 = _clean_action_head(action2)
        return _clean_text(action2, max_chars=self._max_action_chars) if action2 else None

    def _extract_condition_predicates(self, ns: NormativeSentence, sentence_text: str) -> str | None:
        cond_row = getattr(ns, "condition_text", None)
        cond = ns.condition_span or (str(cond_row).strip() if cond_row is not None and str(cond_row).strip() else None)
        if not cond:
            alt = _cp._extract_condition_span(sentence_text)
            if alt:
                cond = alt
        if not cond:
            return None
        cond = cond.strip()

        # Sometimes detector extracts broader span; trim at first condition keyword.
        if not _COND_START_RE.search(cond):
            m = _first_regex_match(sentence_text, [t.regex for t in CONDITION_TRIGGERS])
            if m:
                cond = sentence_text[m.start() : m.start() + self._max_condition_chars].strip()

        if not _COND_START_RE.search(cond):
            return None

        cond = _truncate_at_first_stop(
            cond,
            stop_patterns=self._deadline_triggers + self._dossier_triggers + self._authority_triggers,
            fallback_max_chars=self._max_condition_chars,
        )
        cond = cond.strip(" ,;:-")
        if len(cond) < 10:
            return None
        # Normalize to compact condition phrase.
        cond = re.sub(r"\btheo\s+quy\s+định\s+[^,.;]{0,120}", "", cond, flags=re.I | re.U).strip(" ,;:-")
        return cond or None

    def _extract_deadline(self, sentence_text: str) -> tuple[str | None, str | None, str | None]:
        s_norm = re.sub(r"\s+", " ", sentence_text or "").strip()
        if not any(t.regex.search(s_norm) for t in DEADLINE_TRIGGERS):
            return None, None, None

        # Primary: "trong thời hạn X ngày/vòng ..." (optionally with làm việc)
        m = re.search(
            r"(trong\s+(thời\s+hạn|vòng)|chậm\s+nhất)\s*(\d{1,3})\s*(ngày|tháng|năm)(\s+làm\s+việc)?",
            s_norm,
            flags=re.I | re.U,
        )
        if m:
            anchor_word = m.group(1).strip()
            value = m.group(3)
            unit_base = m.group(4).lower()
            has_working = m.group(5) is not None
            unit = "working_day" if unit_base == "ngày" and has_working else (
                "month" if unit_base == "tháng" else ("year" if unit_base == "năm" else "day")
            )
            # Infer anchor type from nearby words after match end.
            after = s_norm[m.end() : m.end() + 140].lower()
            anchor = self._infer_anchor_from_context(after, anchor_word)
            return value, unit, anchor

        # Secondary: "... X ngày ... kể từ ngày ..."
        m2 = re.search(
            r"(\d{1,3})\s*(ngày|tháng|năm)(\s+làm\s+việc)?\s*kể\s+từ\s+ngày\s+([^.;]{0,90})",
            s_norm,
            flags=re.I | re.U,
        )
        if m2:
            value = m2.group(1)
            unit_base = m2.group(2).lower()
            has_working = m2.group(3) is not None
            unit = "working_day" if unit_base == "ngày" and has_working else (
                "month" if unit_base == "tháng" else ("year" if unit_base == "năm" else "day")
            )
            anchor_phrase = m2.group(4)
            anchor = self._infer_anchor_from_phrase(anchor_phrase)
            return value, unit, anchor

        # Fallback: bare number+unit
        m3 = re.search(r"\b(\d{1,3})\s*(ngày|tháng|năm)\b(\s+làm\s+việc)?", s_norm, flags=re.I | re.U)
        if m3:
            value = m3.group(1)
            unit_base = m3.group(2).lower()
            has_working = m3.group(3) is not None
            unit = "working_day" if unit_base == "ngày" and has_working else (
                "month" if unit_base == "tháng" else ("year" if unit_base == "năm" else "day")
            )
            return value, unit, None

        return None, None, None

    def _infer_anchor_from_context(self, after: str, anchor_word: str) -> str | None:
        if "nhận" in after and ("hồ sơ" in after or "ho so" in after):
            return "from_receipt_of_dossier"
        if "thay đổi" in after or "có thay đổi" in after:
            return "from_change_event"
        if "chính thức" in after or "lập" in after:
            return "from_establishment_date"
        if "kể từ ngày" in after:
            return "from_anchor"
        if "chậm" in anchor_word.lower():
            return "no_later_than"
        return None

    def _infer_anchor_from_phrase(self, phrase: str) -> str | None:
        p = (phrase or "").lower()
        if "nhận" in p and ("hồ sơ" in p or "ho so" in p):
            return "from_receipt_of_dossier"
        if "thay đổi" in p or "có thay đổi" in p:
            return "from_change_event"
        if "chính thức" in p or "lập" in p:
            return "from_establishment_date"
        return "from_anchor"

    def _extract_required_documents(self, ns: NormativeSentence, sentence_text: str, frame_type: str) -> str | None:
        if frame_type != "document_rule":
            return None

        doc_hint = getattr(ns, "document_text", None)
        dossier_text = ns.document_span or (
            str(doc_hint).strip() if doc_hint is not None and str(doc_hint).strip() else None
        ) or self._find_first_dossier_clause(sentence_text)
        if not dossier_text:
            return None

        cleaned = re.sub(
            r"^\s*(hồ\s+sơ\s+bao\s+gồm|kèm\s+theo\s*hồ\s+sơ|bao\s+gồm\s+các\s+giấy\s+tờ|bao\s+gồm\s+các\s+tài\s+liệu)\s*:?\s*",
            "",
            dossier_text,
            flags=re.I | re.U,
        ).strip(" :;-")

        item_re = re.compile(r"(?m)\b([a-zđ])\)\s+", re.I | re.U)
        if item_re.search(cleaned):
            starts = [m.start() for m in item_re.finditer(cleaned)]
            items: list[str] = []
            for i, st in enumerate(starts):
                end = starts[i + 1] if i + 1 < len(starts) else len(cleaned)
                part = cleaned[st:end].strip()
                part = re.sub(r"(?m)\b[a-zđ]\)\s+", "", part, flags=re.I | re.U).strip()
                if part:
                    items.append(part)
                if len("; ".join(items)) >= self._max_required_docs_chars:
                    break
            joined = "; ".join(items).strip()
            return joined[: self._max_required_docs_chars] or None

        cleaned = re.sub(r"\b(theo\s+quy\s+định\s+của\s+pháp\s+luật[^,.;]{0,120})\b", "", cleaned, flags=re.I | re.U).strip(" ,;:-")

        # Try to extract concrete document phrases.
        doc_item_rx = re.compile(
            r"\b("
            r"Giấy\s+đề\s+nghị[^.;]{0,120}"
            r"|Bản\s+sao(?:\s+hoặc\s+bản\s+chính)?[^.;]{0,140}"
            r"|Bản\s+chính[^.;]{0,120}"
            r"|Bản\s+sao\s+biên\s+bản\s+họp[^.;]{0,120}"
            r"|Bản\s+sao\s+quyết\s+định[^.;]{0,120}"
            r"|Danh\s+sách\s+chủ\s+sở\s+hữu\s+hưởng\s+lợi[^.;]{0,120}"
            r"|Thông\s+báo\s+thành\s+lập\s+chi\s+nhánh[^.;]{0,120}"
            r"|Thông\s+báo[^.;]{0,120}"
            r"|Giấy\s+tờ\s+pháp\s+lý[^.;]{0,120}"
            r")\b",
            flags=re.I | re.U,
        )
        items = [m.group(1).strip(" ,;:-") for m in doc_item_rx.finditer(cleaned)]
        if items:
            dedup: list[str] = []
            for it in items:
                if it not in dedup:
                    dedup.append(it)
            return _clean_text("; ".join(dedup), max_chars=self._max_required_docs_chars)

        # Fallback: keep first concrete noun phrase around dossier context.
        m_np = re.search(r"\b(giấy\s+đề\s+nghị[^.;]{0,120}|bản\s+sao[^.;]{0,120}|thông\s+báo[^.;]{0,120}|danh\s+sách[^.;]{0,120})\b", cleaned, flags=re.I | re.U)
        if m_np:
            return _clean_text(m_np.group(1), max_chars=self._max_required_docs_chars)
        # Last fallback for generic labels.
        low = cleaned.lower()
        sent_low = sentence_text.lower()
        if "đăng ký doanh nghiệp" in low:
            if "ủy quyền" in sent_low:
                return "Văn bản ủy quyền; Giấy đề nghị đăng ký doanh nghiệp"
            if "thay đổi nội dung" in sent_low:
                return "Giấy đề nghị đăng ký thay đổi nội dung đăng ký doanh nghiệp"
            if "chi nhánh" in sent_low or "văn phòng đại diện" in sent_low:
                return "Thông báo thành lập chi nhánh, văn phòng đại diện"
            return "Giấy đề nghị đăng ký doanh nghiệp"
        if "đăng ký hộ kinh doanh" in low:
            if "ủy quyền" in sent_low:
                return "Văn bản ủy quyền; Giấy đề nghị đăng ký hộ kinh doanh"
            return "Giấy đề nghị đăng ký hộ kinh doanh"
        return _clean_text(cleaned, max_chars=self._max_required_docs_chars)

    def _find_first_dossier_clause(self, sentence_text: str) -> str | None:
        for trig in DOSSIER_TRIGGERS:
            m = trig.regex.search(sentence_text)
            if not m:
                continue
            start = m.start()
            return sentence_text[start : start + 280].strip()
        return None

    def _extract_recipient_authority(self, ns: NormativeSentence, sentence_text: str, frame_type: str) -> str | None:
        # Only fill recipient_authority when the sentence contains an authority-handling cue.
        # Avoid guessing from "hồ sơ"/"trong thời hạn"/"nếu".
        has_authority_handling_cue = any(rx.regex.search(sentence_text) for rx in AUTHORITY_TRIGGERS) or bool(ns.authority_span)
        if not has_authority_handling_cue:
            return None

        # If explicit "Cơ quan đăng ký kinh doanh ..." appears, keep it.
        for label, rx in _AUTHORITY_PATTERNS:
            if rx.search(sentence_text):
                return label

        # Conservative fallback only when authority span explicitly exists.
        if ns.authority_span and re.search(r"\bcấp\s+tỉnh\b", ns.authority_span, flags=re.I | re.U):
            return "cơ quan đăng ký kinh doanh cấp tỉnh"
        if ns.authority_span:
            return "cơ quan đăng ký kinh doanh"
        return None

    def _extract_exception(self, text: str) -> str | None:
        if not text:
            return None
        m = re.search(
            r"((?:trừ\s+trường\s+hợp|ngoại\s+trừ|trừ\s+khi|nếu\s+không|"
            r"không\s+áp\s+dụng\s+đối\s+với)[^.;]{0,280})",
            text,
            flags=re.I | re.U,
        )
        return m.group(1).strip() if m else None

    def _infer_legal_effect(self, frame_type: str, modality: str) -> str:
        if modality == "prohibition":
            return "không được thực hiện"
        if modality == "permission":
            return "được phép thực hiện"
        if frame_type == "status_rule":
            return "trạng thái có thể thay đổi"
        return "phải thực hiện"

    def _to_vi_frame_type(self, frame_type: str) -> str:
        mapping = {
            "duty_rule": "khung_nghia_vu",
            "document_rule": "khung_ho_so",
            "authority_action": "khung_hanh_dong_co_quan",
            "procedure_rule": "khung_thu_tuc",
            "condition_rule": "khung_dieu_kien",
            "status_rule": "khung_quyen",
        }
        return mapping.get(frame_type, frame_type)

    def _to_vi_modality(self, modality: str) -> str:
        mapping = {
            "obligation": "bat_buoc",
            "permission": "duoc_phep",
            "prohibition": "bi_cam",
        }
        return mapping.get(modality, modality)

    def _make_frame_id(
        self,
        *,
        unit_ref_full: str,
        candidate_id: str,
        frame_type: str,
        action_predicate: str | None,
        doc_code: str,
        suffix: str = "",
    ) -> str:
        doc_token = "LUATDN" if "67/" in doc_code else "ND168" if "168/" in doc_code else "DOC"
        m_d = re.search(r"Điều\s+(\d+[a-z]?)", unit_ref_full, flags=re.I | re.U)
        m_k = re.search(r"khoản\s+(\d+)", unit_ref_full, flags=re.I | re.U)
        m_p = re.search(r"điểm\s+([a-zđ])", unit_ref_full, flags=re.I | re.U)
        parts = [f"FRAME_{doc_token}"]
        if m_d:
            parts.append(f"D{m_d.group(1)}")
        if m_k:
            parts.append(f"K{m_k.group(1)}")
        if m_p:
            parts.append(m_p.group(1).upper())
        key = "QUY_TAC"
        if action_predicate:
            key = re.sub(r"[^0-9A-Za-z]+", "_", action_predicate).strip("_").upper()[:36]
        elif frame_type:
            key = re.sub(r"[^0-9A-Za-z]+", "_", frame_type).strip("_").upper()[:36]
        parts.append(key or stable_hash(candidate_id, n=8))
        base = "_".join(parts)
        if suffix:
            return f"{base}_{suffix}"
        return base

    def _to_vai_tro_chu_the(self, subject_role: str) -> str:
        low = (subject_role or "").lower()
        if "cơ quan" in low:
            return "co_quan"
        if "nghĩa vụ" in low:
            return "chu_the_bi_dieu_chinh"
        if "thực hiện" in low:
            return "chu_the_thuc_hien"
        return "chu_the_thuc_hien"

    def _to_tinh_chat_phap_ly(self, modality: str, frame_type: str) -> str:
        m = (modality or "").lower()
        ft = (frame_type or "").lower()
        if "khung_cam_doan" in ft:
            return "bi_cam"
        if "bi_cam" in m:
            return "bi_cam"
        if "duoc_phep" in m:
            return "duoc_phep"
        if "hanh_dong_co_quan" in ft:
            return "co_trach_nhiem"
        if "khung_quyen" in ft:
            return "duoc_phep"
        if "khung_ket_qua" in ft:
            return "co_the"
        return "bat_buoc"

    def _extract_quantitative_slots(self, text: str) -> tuple[str | None, str | None, str | None, str | None]:
        t = re.sub(r"\s+", " ", text or "").strip()
        nguong_sl = None
        nguong_tl = None
        khoang = None
        dkdl = None
        m_khoang = re.search(r"\btừ\s+(\d+[^ ]*)\s+đến\s+(\d+[^,.; ]*)", t, flags=re.I | re.U)
        if m_khoang:
            khoang = m_khoang.group(0)
            dkdl = m_khoang.group(0)
        m_tl = re.search(r"\b\d+(\,\d+)?\s*%|\btỷ\s+lệ\s+[^,.;]{0,80}", t, flags=re.I | re.U)
        if m_tl:
            nguong_tl = m_tl.group(0)
            dkdl = dkdl or m_tl.group(0)
        m_sl = re.search(r"\b(không\s+quá|ít\s+nhất|trở\s+lên|từ)\s+\d+[^,.;]{0,60}", t, flags=re.I | re.U)
        if m_sl:
            nguong_sl = m_sl.group(0)
            dkdl = dkdl or m_sl.group(0)
        return nguong_sl, nguong_tl, khoang, dkdl

    def _extract_van_ban_dan_chieu(self, text: str) -> str | None:
        m = re.search(r"\b(Điều|Khoản|Điểm)\s+\d+[a-z]?(?:\s+của\s+Luật\s+này)?", text or "", flags=re.I | re.U)
        return m.group(0) if m else None

    def _split_flags(
        self,
        text: str,
        action_predicate: str | None,
        required_documents: str | None,
        deadline_value: str | None,
        exception_text: str | None,
    ) -> tuple[str, str | None]:
        reasons: list[str] = []
        t = text or ""
        if t.count(";") >= 1:
            reasons.append("nhieu_hanh_vi")
        if re.search(r"\b(doanh nghiệp|công ty)\b.*\b(cơ quan)\b", t, flags=re.I | re.U):
            reasons.append("nhieu_chu_the")
        if required_documents and deadline_value:
            reasons.append("vua_ho_so_vua_thoi_han")
        if exception_text:
            reasons.append("co_ngoai_le_rieng")
        if re.search(r"\b(cấp|thông báo|từ chối)\b.*\b(và|;)\b.*\b(cấp|thông báo|từ chối)\b", t, flags=re.I | re.U):
            reasons.append("co_nhieu_ket_qua")
        if not reasons:
            return "khong", None
        return "co", ";".join(dict.fromkeys(reasons))

    def _muc_do_day_du(
        self,
        *,
        chu_the: str | None,
        hanh_vi: str | None,
        dieu_kien_ap_dung: str | None,
        thanh_phan_ho_so: str | None,
        thoi_han_so: str | None,
        co_quan: str | None,
    ) -> str:
        c = 0
        for v in [chu_the, hanh_vi, dieu_kien_ap_dung, thanh_phan_ho_so, thoi_han_so, co_quan]:
            if v and str(v).strip():
                c += 1
        if c >= 5:
            return "day_du"
        if c >= 4:
            return "kha_day_du"
        if c >= 2:
            return "thieu_vai_slot"
        return "thieu_nhieu_slot"

    def _muc_do_day_du_rich(
        self,
        *,
        chu_the: str | None,
        hanh_vi: str | None,
        doi_tuong: str | None,
        tinh_chat: str | None,
        dieu_kien_ap_dung: str | None,
        thanh_phan_ho_so: str | None,
        thoi_han_so: str | None,
        co_quan: str | None,
        ngoai_le: str | None,
        ket_qua: str | None,
    ) -> str:
        core = 0
        for v in [chu_the, hanh_vi, doi_tuong, tinh_chat]:
            if v and str(v).strip() and str(v).strip().lower() != "unknown":
                core += 1
        bonus = 0
        for v in [dieu_kien_ap_dung, thanh_phan_ho_so, co_quan, thoi_han_so, ngoai_le, ket_qua]:
            if v and str(v).strip():
                bonus += 1
        if core >= 4 and bonus >= 3:
            return "rat_day_du"
        if core >= 4 and bonus >= 1:
            return "day_du"
        if core >= 3 and bonus >= 1:
            return "kha_day_du"
        if core >= 2:
            return "thieu_vai_slot"
        return "thieu_nhieu_slot"

    def _extract_object_from_text(self, text: str) -> str | None:
        for pat in [
            r"\bGiấy\s+chứng\s+nhận\s+đăng\s+ký\s+doanh\s+nghiệp\b",
            r"\bnội\s+dung\s+đăng\s+ký\s+doanh\s+nghiệp\b",
            r"\bhồ\s+sơ\s+đăng\s+ký\s+doanh\s+nghiệp\b",
            r"\bDanh\s+sách\s+chủ\s+sở\s+hữu\s+hưởng\s+lợi\b",
        ]:
            m = re.search(pat, text or "", flags=re.I | re.U)
            if m:
                return m.group(0)
        return None

    def _to_vi_deadline_unit(self, unit: str | None) -> str | None:
        if not unit:
            return None
        m = {"day": "ngay", "working_day": "ngay_lam_viec", "month": "thang", "year": "nam"}
        return m.get(unit, unit)

    def _to_vi_deadline_anchor(self, anchor: str | None) -> str | None:
        if not anchor:
            return None
        m = {
            "from_receipt_of_dossier": "ke_tu_ngay_nhan_ho_so",
            "from_change_event": "ke_tu_ngay_co_thay_doi",
            "from_establishment_date": "ke_tu_ngay_thanh_lap",
            "from_anchor": "ke_tu_moc_tham_chieu",
            "no_later_than": "cham_nhat",
        }
        return m.get(anchor, anchor)

    def _is_definition_like(self, text: str) -> bool:
        return bool(
            re.search(
                r"\b(được\s+hiểu\s+là|là\s+đơn\s+vị\s+phụ\s+thuộc|là\s+dãy\s+số|là\s+tập\s+hợp\s+dữ\s+liệu|là\s+văn\s+bản|giải\s+thích\s+từ\s+ngữ)\b",
                text,
                flags=re.I | re.U,
            )
        )

    def _assess_frame_quality(
        self,
        *,
        ns: NormativeSentence,
        frame_type: str,
        subject_type: str,
        action_predicate: str | None,
        deadline_value: str | None,
        sentence_text: str,
        required_documents: str | None = None,
        exception_text: str | None = None,
        condition_predicates: str | None = None,
        candidate_type: str = "",
        ket_qua_grounded: str | None = None,
        nguong_ok: bool = False,
    ) -> tuple[str, str]:
        ct = (candidate_type or "").strip().lower()
        if self._is_definition_like(sentence_text):
            return "dropped", "definition_like_rejected"

        specialized_ok = False
        if ct == "thoi_han" and deadline_value:
            specialized_ok = True
        elif ct == "thanh_phan_ho_so" and required_documents:
            specialized_ok = True
        elif ct == "ngoai_le" and exception_text:
            specialized_ok = True
        elif ct == "nguong_so_luong" and nguong_ok:
            specialized_ok = True
        elif ct == "ket_qua_phap_ly" and ket_qua_grounded:
            specialized_ok = True
        elif ct == "dieu_kien_ap_dung" and condition_predicates:
            specialized_ok = True
        elif frame_type == "condition_rule" and condition_predicates:
            specialized_ok = True

        if not action_predicate and not specialized_ok:
            return "dropped", "weak_action_dropped"
        if frame_type == "procedure_rule" and not specialized_ok:
            if subject_type == "Unknown":
                return "dropped", "weak_procedure_rule"
            if action_predicate and re.search(
                r"\b(có\s+thể|được|bao\s+gồm|thực\s+hiện)\b", action_predicate, flags=re.I | re.U
            ):
                return "dropped", "weak_procedure_rule"
            if action_predicate and re.search(
                r"\b(khai\s+thác|tra\s+cứu|cung\s+cấp)\b", action_predicate, flags=re.I | re.U
            ):
                return "dropped", "weak_procedure_rule"
        if subject_type == "Unknown" and frame_type not in {"document_rule"} and not specialized_ok:
            return "low_confidence", "low_confidence_subject"
        if (
            deadline_value
            and frame_type not in {"duty_rule", "authority_action", "procedure_rule", "condition_rule"}
            and ct != "thoi_han"
        ):
            return "low_confidence", "deadline_mismatch"
        note = "quality_ok"
        if specialized_ok and not action_predicate:
            note = "specialized_frame_slot_ok"
        return "seed_extracted_first_pass", note


__all__ = ["LegalFrameExtractor"]

