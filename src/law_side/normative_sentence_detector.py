"""Rule-based normative sentence detection (Stage 2).

Extract *useful* normative candidates for rule-base construction using only
regex + heuristics (no LLM, no OCR).

Precision-first for paper research:
- split list-like structures (e.g., multiple `a)`, `b)`)
- prefer trigger-driven windows around normative cues
- filter definition/header-like spans
- keep spans short/readable for human review and downstream extraction
"""

from __future__ import annotations

import re
from typing import Any, Iterable

from law_side.law_rulebase_models import LegalUnit, NormativeSentence
from law_side.rule_patterns import (
    AUTHORITY_TRIGGERS,
    DEADLINE_TRIGGERS,
    DOSSIER_TRIGGERS,
    OBLIGATION_TRIGGERS,
    PERMISSION_TRIGGERS,
    PROHIBITION_TRIGGERS,
    CONDITION_TRIGGERS,
    detect_candidate_categories,
    classify_modality,
)
from utils.ids import stable_hash
from utils.logger import get_logger


_POINT_ITEM_RE = re.compile(r"(?m)^\s*([a-zđ])\)\s+")
_DEFINITION_HEAD_RE = re.compile(r"^\s*([A-ZÀ-ỸĐ][^.;]{0,120})\s+là\s+", re.I | re.U)

# Captures a stop boundary for spans.
_PUNCT_STOP_RE = re.compile(r"[.;]\s+|\n{2,}", re.U)


def _norm(s: str | None) -> str:
    return (s or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def _norm_space(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = s.replace("\n", " ")
    return re.sub(r"\s+", " ", s).strip()


class NormativeSentenceDetector:
    """Stage-2 detector: legal unit -> normative candidate segments."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or {}
        self._log = get_logger(self.__class__.__name__)

        self._min_sentence_chars = int(self._config.get("min_sentence_chars", 40))
        self._max_candidate_chars = int(self._config.get("max_candidate_chars", 260))
        # Broadened defaults for recall; still overridable via YAML.
        self._max_candidates_per_unit = int(self._config.get("max_candidates_per_unit", 16))
        self._pre_trigger_chars = int(self._config.get("pre_trigger_chars", 120))
        self._max_trigger_matches = int(self._config.get("max_trigger_matches", 60))

        # "Legal action center" verbs (heuristic; used only for candidate filtering).
        self._action_verbs: list[re.Pattern[str]] = [
            re.compile(r"\bđăng\s*ký\b", re.I | re.U),
            re.compile(r"\bthông\s*báo\b", re.I | re.U),
            re.compile(r"\bgửi\b", re.I | re.U),
            re.compile(r"\bnộp\b", re.I | re.U),
            re.compile(r"\b cấp \b", re.I | re.U),
            re.compile(r"\bcấp\b", re.I | re.U),
            re.compile(r"\bxem\s*xét\b", re.I | re.U),
            re.compile(r"\btừ\s*chối\b", re.I | re.U),
            re.compile(r"\bcập\s*nhật\b", re.I | re.U),
            re.compile(r"\bthực\s*hiện\b", re.I | re.U),
            re.compile(r"\btiếp\s*nhận\b", re.I | re.U),
            re.compile(r"\bchịu\s*trách\s*nhiệm\b", re.I | re.U),
            re.compile(r"\bphải\b", re.I | re.U),
            re.compile(r"\bkhông\s*được\b", re.I | re.U),
        ]

        self._subject_keywords: list[re.Pattern[str]] = [
            re.compile(r"\bdoanh\s*nghiệp\b", re.I | re.U),
            re.compile(r"\bcông\s*ty\s*cổ\s*phần\b", re.I | re.U),
            re.compile(r"\bcông\s*ty\s*trách\s*nhiệm\s*hữu\s*hạn\b", re.I | re.U),
            re.compile(r"\bcông\s*ty\b", re.I | re.U),
            re.compile(r"\bngười\s*thành\s*lập\s*doanh\s*nghiệp\b", re.I | re.U),
            re.compile(r"\bngười\s*nộp\b", re.I | re.U),
            re.compile(r"\bcơ\s*quan\s*đăng\s*ký\s*kinh\s*doanh\b", re.I | re.U),
            re.compile(r"\bcơ\s*quan\s*đăng\s*ký\s*kinh\s*doanh\s*cấp\s*tỉnh\b", re.I | re.U),
        ]
        self._subject_priority_patterns: list[re.Pattern[str]] = [
            re.compile(r"^\s*(Cơ quan đăng ký kinh doanh cấp tỉnh)\b", re.I | re.U),
            re.compile(r"^\s*(Cơ quan đăng ký kinh doanh)\b", re.I | re.U),
            re.compile(r"^\s*(Người thành lập doanh nghiệp)\b", re.I | re.U),
            re.compile(r"^\s*(Doanh nghiệp xã hội)\b", re.I | re.U),
            re.compile(r"^\s*(Doanh nghiệp)\b", re.I | re.U),
            re.compile(r"^\s*(Công ty cổ phần)\b", re.I | re.U),
            re.compile(r"^\s*(Chủ sở hữu[^,.;]{0,80})\b", re.I | re.U),
            re.compile(r"^\s*(Người đại diện theo pháp luật[^,.;]{0,80})\b", re.I | re.U),
        ]
        self._authority_subject_re = re.compile(
            r"\b(cơ\s+quan\s+đăng\s+ký\s+kinh\s+doanh|phòng\s+đăng\s+ký\s+kinh\s+doanh|cơ\s+quan\s+nhà\s+nước\s+có\s+thẩm\s+quyền|BHXH|bảo\s+hiểm\s+xã\s+hội|cơ\s+quan\s+bảo\s+hiểm\s+xã\s+hội|sở\s+lao\s+động\s+thương\s+binh\s+và\s+xã\s+hội|chủ\s+tịch\s+ubnd\s+cấp\s+tỉnh|ngân\s+hàng\s+nhận\s+ký\s+quỹ)\b",
            re.I | re.U,
        )
        self._authority_subject_head_re = re.compile(
            r"^\s*(cơ\s+quan\s+đăng\s+ký\s+kinh\s+doanh(?:\s+cấp\s+tỉnh)?|phòng\s+đăng\s+ký\s+kinh\s+doanh|cơ\s+quan\s+nhà\s+nước\s+có\s+thẩm\s+quyền|BHXH|bảo\s+hiểm\s+xã\s+hội|cơ\s+quan\s+bảo\s+hiểm\s+xã\s+hội|sở\s+lao\s+động\s+thương\s+binh\s+và\s+xã\s+hội|chủ\s+tịch\s+ubnd\s+cấp\s+tỉnh|ngân\s+hàng\s+nhận\s+ký\s+quỹ)\b",
            re.I | re.U,
        )
        self._authority_action_re = re.compile(
            r"\b(xem\s+xét|thông\s+báo|cập\s+nhật|từ\s+chối|tiếp\s+nhận|ra\s+thông\s+báo|công\s+bố|cấp\s+(giấy|đăng\s*ký|lại|đổi|sổ\s+BHXH)|trả\s+BHXH|giải\s+quyết\s+chế\s+độ|chuyển\s+BHXH|thu\s+BHXH|hướng\s+dẫn\s+BHXH|cấp|gia\s+hạn|thu\s+hồi|xác\s+nhận|trình|kiểm\s+tra|chi\s+trả|trích)\b",
            re.I | re.U,
        )
        self._lead_in_only_re = re.compile(
            r"^\s*(trường\s+hợp|đối\s+với|sau\s+khi|trước\s+khi|kèm\s+theo)\b",
            re.I | re.U,
        )
        self._definition_like_re = re.compile(
            r"\b(được\s+hiểu\s+là|là\s+dãy\s+số|là\s+đơn\s+vị\s+phụ\s+thuộc|là\s+tình\s+trạng\s+pháp\s+lý|là\s+việc|là\s+tổ\s+chức|là\s+cá\s+nhân|là\s+người)\b",
            re.I | re.U,
        )
        self._status_description_re = re.compile(
            r"\b(hệ\s+thống\s+.*\s+bao\s+gồm|giấy\s+chứng\s+nhận\s+.*\s+ghi|nội\s+dung\s+.*\s+ghi|thông\s+tin\s+.*\s+được\s+|ghi\s+lại\s+những\s+thông\s+tin\s+về)\b",
            re.I | re.U,
        )
        self._concept_description_re = re.compile(
            r"\b(giải\s+thích\s+từ\s+ngữ|đáp\s+ứng\s+các\s+tiêu\s+chí\s+sau\s+đây|phải\s+có\s+ít\s+nhất|là\s+chào\s+bán|tiêu\s+chí\s+sau\s+đây)\b",
            re.I | re.U,
        )
        self._definition_strong_re = re.compile(
            r"\b(là\s+văn\s+bản|là\s+tập\s+hợp\s+dữ\s+liệu|là\s+doanh\s+nghiệp|là\s+đơn\s+vị\s+phụ\s+thuộc|là\s+dãy\s+số)\b",
            re.I | re.U,
        )

        # Semantic stage-2 extras: broaden recall for missing types.
        # BROADENED for labor: add labor-specific exception patterns
        self._exception_re = re.compile(r"\b(trừ\s+trường\s+hợp|ngoại\s+trừ|trừ\s+khi|nếu\s+không|trừ\b|không\s+áp\s+dụng\s+cho|ngoại\s+lệ)\b", re.I | re.U)
        self._threshold_re = re.compile(
            r"\b(không\s+quá|ít\s+nhất|trở\s+lên|từ\s+\d{1,4}|\d{1,3}\s*%|tỷ\s+lệ|phần\s+trăm|từ\s+[^.;]{0,10}\s+đến\s+[^.;]{0,10})\b",
            re.I | re.U,
        )
        self._procedure_re = re.compile(
            r"\b(đăng\s*ký|thông\s*báo|gửi\s+đến|gửi\b|nộp\b|công\s*bố|lưu\s+giữ|trình\s+tự|thủ\s+tục)\b",
            re.I | re.U,
        )
        self._legal_effect_re = re.compile(
            r"\b(được\s+cấp|bị\s+thu\s+hồi|thu\s+hồi\s+Giấy|được\s+công\s+bố|có\s+hiệu\s+lực|hết\s+hiệu\s+lực|"
            r"bị\s+tạm\s+ng(?:ừ|ư)ng|khôi\s+phục|chấp\s+thuận|bị\s+giải\s+thể)\b",
            re.I | re.U,
        )

    def detect(self, units: list[LegalUnit]) -> list[NormativeSentence]:
        """Run normative sentence detection over segmented `LegalUnit`s."""
        out: list[NormativeSentence] = []

        for unit in units:
            raw_candidates = self._generate_candidates(unit.text)
            per_unit_candidates: list[dict[str, Any]] = []
            for idx, (cand_text, debug) in enumerate(raw_candidates[: self._max_candidates_per_unit]):
                cand_text = _norm_space(cand_text)
                if len(cand_text) < self._min_sentence_chars:
                    continue
                if len(cand_text) > self._max_candidate_chars:
                    continue
                if not self._is_candidate_good(cand_text, source_ref=unit.source_ref, heading=unit.heading):
                    continue

                modality = classify_modality(cand_text)
                cats = detect_candidate_categories(cand_text)
                normative_pattern = self._infer_sentence_type(cand_text, cats, modality)

                candidate_rule_type = self._infer_candidate_rule_type(cand_text)
                if candidate_rule_type == "other":
                    continue

                subject_span, action_span, modality_span = self._extract_subject_action_modality(cand_text)
                subject_span = self._recover_subject_span(cand_text, subject_span, candidate_rule_type)
                condition_span = self._extract_condition_span(cand_text)
                time_span = self._extract_deadline_span(cand_text)
                document_span = self._extract_dossier_span(cand_text)
                authority_span = self._extract_authority_span(cand_text)
                if not self._passes_minimal_semantic_gate(
                    cand_text=cand_text,
                    candidate_rule_type=candidate_rule_type,
                    subject_span=subject_span,
                    action_span=action_span,
                ):
                    continue

                conf = self._estimate_confidence(modality=modality, candidate_rule_type=candidate_rule_type, cand_text=cand_text)
                notes = f"{debug}; cue={self._cue_summary(cand_text)}"
                if conf == "high":
                    notes += "; high_confidence_kept"
                per_unit_candidates.append(
                    {
                        "cand_text": cand_text,
                        "candidate_rule_type": candidate_rule_type,
                        "normative_pattern": normative_pattern,
                        "subject_span": subject_span,
                        "action_span": action_span,
                        "modality_span": modality_span,
                        "condition_span": condition_span,
                        "time_span": time_span,
                        "document_span": document_span,
                        "authority_span": authority_span,
                        "confidence_manual": conf,
                        "notes": notes,
                        "quality_score": self._score_candidate_quality(cand_text, candidate_rule_type, subject_span, action_span),
                        "idx": idx,
                    }
                )

            emitted_keys: set[str] = set()
            for kept in self._deduplicate_overlapping_candidates(per_unit_candidates):
                expanded = [kept] + self._expand_semantic_subcandidates(kept)
                for sub_idx, item in enumerate(expanded):
                    emit_key = stable_hash(
                        f"{unit.unit_id}|{item['candidate_rule_type']}|{item['cand_text'][:120]}",
                        n=14,
                    )
                    if emit_key in emitted_keys:
                        continue
                    emitted_keys.add(emit_key)
                    ns_id = stable_hash(
                        f"{unit.unit_id}|{item['candidate_rule_type']}|{kept['idx']}|{sub_idx}|{item['cand_text'][:60]}",
                        n=16,
                    )
                    out.append(
                        NormativeSentence(
                        ns_id=ns_id,
                        unit_id=unit.unit_id,
                        doc_id=unit.doc_id,
                        doc_code=getattr(unit, "doc_code", "") or "",
                        unit_ref_full=getattr(unit, "unit_ref_full", "") or "",
                        source_ref=unit.source_ref,
                        source_text=unit.text,
                        sentence_text=item["cand_text"],
                        sentence_type=unit.unit_type,
                        normative_pattern=kept["normative_pattern"],
                        subject_span=item["subject_span"],
                        action_span=item["action_span"],
                        modality_span=kept["modality_span"],
                        condition_span=item["condition_span"],
                        time_span=item["time_span"],
                        document_span=item["document_span"],
                        authority_span=item["authority_span"],
                        candidate_rule_type=item["candidate_rule_type"],
                        confidence_manual=kept["confidence_manual"],
                        candidate_id=self._make_candidate_id(
                            unit_id=unit.unit_id,
                            unit_ref_full=getattr(unit, "unit_ref_full", "") or "",
                            cand_text=item["cand_text"],
                            candidate_rule_type=item["candidate_rule_type"],
                            normative_pattern=kept["normative_pattern"],
                        ),
                        candidate_type=self._candidate_type(
                            candidate_rule_type=item["candidate_rule_type"],
                            cand_text=item["cand_text"],
                        ),
                        candidate_subtype=self._candidate_subtype(item["cand_text"]),
                        candidate_score=self._candidate_score(
                            confidence_manual=kept["confidence_manual"],
                            cand_text=item["cand_text"],
                        ),
                        trigger_patterns=";".join(self._trigger_patterns(item["cand_text"])),
                        actor_text=self._best_actor_text(
                            cand_text=item["cand_text"],
                            subject_span=item["subject_span"],
                            unit_actor_hint=getattr(unit, "actor_hint", None),
                        ),
                        action_text=self._best_action_text(
                            cand_text=item["cand_text"],
                            action_span=item["action_span"],
                            unit_action_hint=getattr(unit, "action_hint", None),
                        ),
                        object_text=self._best_object_text(
                            cand_text=item["cand_text"],
                            unit_object_hint=getattr(unit, "object_hint", None),
                        ),
                        condition_text=item["condition_span"],
                        deadline_text=item["time_span"],
                        authority_text=item["authority_span"],
                        document_text=item["document_span"],
                        exception_text=self._extract_exception_text(item["cand_text"]),
                        threshold_text=self._extract_threshold_text(item["cand_text"]),
                        legal_effect_text=self._extract_legal_effect_text(item["cand_text"]),
                        should_extract_rule=self._should_extract_rule(
                            cand_text=item["cand_text"],
                            candidate_rule_type=item["candidate_rule_type"],
                            confidence_manual=kept["confidence_manual"],
                        ),
                        extraction_priority=self._extraction_priority(item["cand_text"]),
                        notes=f"{kept['notes']}; {item.get('extra_note','')}; q={kept['quality_score']}",
                        heading=getattr(unit, "heading", "") or "",
                        parent_context=getattr(unit, "parent_context", "") or "",
                    )
                )

        self._log.info("Detected %d normative candidates", len(out))
        return out

    def _expand_semantic_subcandidates(self, kept: dict[str, Any]) -> list[dict[str, Any]]:
        """Derive extra focused candidates for missing semantic layers in same unit."""
        t = kept["cand_text"]
        outs: list[dict[str, Any]] = []
        base = {
            "subject_span": kept.get("subject_span"),
            "action_span": kept.get("action_span"),
            "condition_span": kept.get("condition_span"),
            "time_span": kept.get("time_span"),
            "document_span": kept.get("document_span"),
            "authority_span": kept.get("authority_span"),
        }
        if self._extract_exception_text(t):
            span = self._extract_exception_text(t)
            if span and len(span) >= 14:
                outs.append({**base, "cand_text": span, "candidate_rule_type": "condition", "extra_note": "derived_ngoai_le"})
        if self._extract_threshold_text(t):
            span = self._extract_threshold_text(t)
            if span and len(span) >= 10:
                outs.append({**base, "cand_text": span, "candidate_rule_type": "threshold", "extra_note": "derived_nguong"})
        if self._extract_legal_effect_text(t):
            span = self._extract_legal_effect_text(t)
            if span and len(span) >= 12:
                outs.append({**base, "cand_text": span, "candidate_rule_type": "legal_effect", "extra_note": "derived_ket_qua"})
        if kept.get("document_span"):
            d = _norm_space(kept["document_span"])
            if len(d) >= 14:
                outs.append({**base, "cand_text": d, "candidate_rule_type": "document_requirement", "extra_note": "derived_ho_so"})
        if kept.get("time_span"):
            d = _norm_space(kept["time_span"])
            if len(d) >= 12:
                outs.append({**base, "cand_text": d, "candidate_rule_type": "deadline", "extra_note": "derived_thoi_han"})
        if kept.get("condition_span"):
            d = _norm_space(kept["condition_span"])
            if len(d) >= 10:
                outs.append({**base, "cand_text": d, "candidate_rule_type": "condition", "extra_note": "derived_dieu_kien"})
        return outs[:6]

    # -------------------------------
    # Focused candidate slices (recall boosters)
    # -------------------------------
    def _slice_from_match(self, text: str, m_start: int, *, max_chars: int) -> str:
        """Take a bounded slice starting from match position, stopping at punctuation if possible."""
        t = _norm_space(text)
        start = max(0, min(len(t), m_start))
        chunk = t[start : start + max_chars]
        stop = re.search(r"[.;]\s+|\n{2,}", chunk, flags=re.U)
        if stop:
            chunk = chunk[: stop.start()]
        # Prefer trimming at comma when chunk is long.
        if "," in chunk and len(chunk) > 180:
            chunk = chunk.split(",", 1)[0]
        return _norm_space(chunk)

    def _focused_exception_candidates(self, unit_text: str) -> list[tuple[str, str]]:
        t = unit_text or ""
        out: list[tuple[str, str]] = []
        for m in self._exception_re.finditer(t):
            cand = self._slice_from_match(t, m.start(), max_chars=min(self._max_candidate_chars, 240))
            if cand:
                out.append((cand, "split=focused_exception"))
            if len(out) >= 4:
                break
        return out

    def _focused_legal_effect_candidates(self, unit_text: str) -> list[tuple[str, str]]:
        t = unit_text or ""
        out: list[tuple[str, str]] = []
        for m in self._legal_effect_re.finditer(t):
            cand = self._slice_from_match(t, m.start(), max_chars=min(self._max_candidate_chars, 240))
            if cand:
                out.append((cand, "split=focused_legal_effect"))
            if len(out) >= 4:
                break
        return out

    def _make_candidate_id(
        self,
        *,
        unit_id: str,
        unit_ref_full: str,
        cand_text: str,
        candidate_rule_type: str,
        normative_pattern: str,
    ) -> str:
        doc_token = "LUATDN" if "UNIT_LUATDN" in (unit_id or "") else "ND168" if "UNIT_ND168" in (unit_id or "") else "DOC"
        ref = unit_ref_full or ""
        # Try to parse Điều/Khoản/Điểm from ref to keep readable IDs.
        m_d = re.search(r"Điều\s+(\d+[a-z]?)", ref, flags=re.I | re.U)
        m_k = re.search(r"khoản\s+(\d+)", ref, flags=re.I | re.U)
        m_p = re.search(r"điểm\s+([a-zđ])", ref, flags=re.I | re.U)
        parts = [f"CAND_{doc_token}"]
        if m_d:
            parts.append(f"D{m_d.group(1)}")
        if m_k:
            parts.append(f"K{m_k.group(1)}")
        if m_p:
            parts.append(m_p.group(1).upper())
        key = self._candidate_key_phrase(cand_text, candidate_rule_type, normative_pattern)
        parts.append(key)
        return "_".join(parts)

    def _candidate_key_phrase(self, cand_text: str, candidate_rule_type: str, normative_pattern: str) -> str:
        t = _norm_space(cand_text).lower()
        if re.search(r"\bhồ\s+sơ\s+bao\s+gồm\b", t, flags=re.I | re.U):
            return "HO_SO_BAO_GOM"
        if re.search(r"\btrong\s+thời\s+hạn\b|\bchậm\s+nhất\b|\bkể\s+từ\s+ngày\b", t, flags=re.I | re.U):
            return "THOI_HAN"
        if re.search(r"\btrừ\s+trường\s+hợp\b|\bngoại\s+trừ\b|\bnếu\s+không\b", t, flags=re.I | re.U):
            return "NGOAI_LE"
        if re.search(r"\b(không\s+quá|ít\s+nhất|trở\s+lên|từ\s+\d+)\b", t, flags=re.I | re.U):
            return "NGUONG"
        if "authority_action" in (candidate_rule_type or ""):
            return "HANH_DONG_CO_QUAN"
        if "document" in (candidate_rule_type or ""):
            return "HO_SO"
        if "deadline" in (candidate_rule_type or ""):
            return "THOI_HAN"
        if "permission" in (candidate_rule_type or "") or "permission" in (normative_pattern or ""):
            return "QUYEN"
        if "prohibition" in (candidate_rule_type or "") or "prohibition" in (normative_pattern or ""):
            return "CAM"
        if re.search(r"\bđăng\s*ký\b", t, flags=re.I | re.U):
            return "DANG_KY"
        if re.search(r"\bthông\s+báo\b", t, flags=re.I | re.U):
            return "THONG_BAO"
        return "QUY_TAC"

    def _candidate_type(self, *, candidate_rule_type: str, cand_text: str) -> str:
        t = _norm_space(cand_text)
        crt = (candidate_rule_type or "").strip().lower()
        if re.search(r"\btrừ\s+trường\s+hợp\b|\bngoại\s+trừ\b|\btrừ\s+khi\b|\bnếu\s+không\b", t, flags=re.I | re.U):
            return "ngoai_le"
        if crt in {"threshold"} or re.search(
            r"\b(không\s+quá|ít\s+nhất|trở\s+lên|từ\s+\d+|tỷ\s+lệ|phần\s+trăm|từ\s+[^.;]{0,10}\s+đến\s+[^.;]{0,10})\b",
            t,
            flags=re.I | re.U,
        ):
            return "nguong_so_luong"
        if crt in {"condition"} and re.search(r"\b(nếu|khi|trường\s+hợp|đối\s+với)\b", t, flags=re.I | re.U):
            return "dieu_kien_ap_dung"
        if crt in {"procedure", "procedure_rule"} or re.search(
            r"\b(trình\s+tự|thủ\s+tục)\b", t, flags=re.I | re.U
        ):
            return "thu_tuc"
        if crt in {"legal_effect"}:
            return "ket_qua_phap_ly"
        if self._extract_legal_effect_text(t):
            # If the sentence focuses on result/effect, keep as separate type.
            if not re.search(r"\b(phải|có\s+nghĩa\s+vụ|không\s+được|nghiêm\s+cấm|có\s+quyền|được\s+phép)\b", t, flags=re.I | re.U):
                return "ket_qua_phap_ly"
        if re.search(r"\b(không\s+quá|ít\s+nhất|trở\s+lên|từ\s+\d+|tỷ\s+lệ|phần\s+trăm)\b", t, flags=re.I | re.U):
            return "nguong_so_luong"
        if crt in {"document_requirement"}:
            return "thanh_phan_ho_so"
        if crt in {"deadline"}:
            return "thoi_han"
        if crt in {"authority_action"}:
            return "hanh_dong_co_quan"
        if crt in {"prohibition"}:
            return "cam_doan"
        if crt in {"permission"}:
            return "quyen"
        if crt in {"registration_obligation", "duty", "notification"}:
            return "nghia_vu"
        if re.search(r"\b(hồ\s+sơ|kèm\s+theo)\b", t, flags=re.I | re.U):
            return "thanh_phan_ho_so"
        if re.search(r"\b(trong\s+thời\s+hạn|chậm\s+nhất|kể\s+từ\s+ngày)\b", t, flags=re.I | re.U):
            return "thoi_han"
        if re.search(r"\b(khi|nếu|trường\s+hợp)\b", t, flags=re.I | re.U):
            return "dieu_kien_ap_dung"
        return "nghia_vu"

    def _candidate_subtype(self, cand_text: str) -> str:
        t = _norm_space(cand_text).lower()
        if "đăng ký" in t and "thay đổi" in t:
            return "dang_ky_thay_doi"
        if "xem xét" in t and "hợp lệ" in t:
            return "xem_xet_ho_so"
        if "cấp giấy chứng nhận" in t:
            return "cap_giay_chung_nhan"
        if "thông báo" in t:
            return "thong_bao"
        if "hồ sơ" in t:
            return "ho_so"
        return ""

    def _candidate_score(self, *, confidence_manual: str, cand_text: str) -> str:
        t = _norm_space(cand_text)
        conf = (confidence_manual or "").strip().lower()
        bonus = 0
        if re.search(r"\b(hồ\s+sơ|trong\s+thời\s+hạn|chậm\s+nhất|kể\s+từ\s+ngày|trừ\s+trường\s+hợp|ngoại\s+trừ|không\s+quá|ít\s+nhất|trở\s+lên)\b", t, flags=re.I | re.U):
            bonus += 1
        if conf == "high":
            return "rat_cao" if bonus else "cao"
        if conf == "medium":
            return "cao" if bonus else "trung_binh"
        return "trung_binh" if bonus else "thap"

    def _trigger_patterns(self, cand_text: str) -> list[str]:
        t = _norm_space(cand_text).lower()
        pats: list[str] = []
        if re.search(r"\btrong\s+thời\s+hạn\b|\bchậm\s+nhất\b|\bkể\s+từ\s+ngày\b", t, flags=re.I | re.U):
            pats.append("trong_thoi_han")
        if re.search(r"\bhồ\s+sơ\s+bao\s+gồm\b", t, flags=re.I | re.U):
            pats.append("ho_so_bao_gom")
        if re.search(r"\bkèm\s+theo\b", t, flags=re.I | re.U):
            pats.append("kem_theo")
        if re.search(r"\bcơ\s+quan\b", t, flags=re.I | re.U):
            pats.append("co_quan")
        if re.search(r"\btrừ\s+trường\s+hợp\b|\bngoại\s+trừ\b|\bnếu\s+không\b", t, flags=re.I | re.U):
            pats.append("tru_truong_hop")
        if re.search(r"\b(từ\s+\d+|không\s+quá|ít\s+nhất|trở\s+lên|tỷ\s+lệ|phần\s+trăm)\b", t, flags=re.I | re.U):
            pats.append("nguong_so_luong")
        if re.search(r"\b(nếu|khi|trường\s+hợp|đối\s+với)\b", t, flags=re.I | re.U):
            pats.append("dieu_kien")
        if re.search(r"\bđăng\s*ký\b", t, flags=re.I | re.U):
            pats.append("dang_ky")
        if re.search(r"\bthông\s+báo\b", t, flags=re.I | re.U):
            pats.append("thong_bao")
        if re.search(r"\b(gửi\s+đến|nộp|công\s+bố|lưu\s+giữ|thủ\s+tục|trình\s+tự)\b", t, flags=re.I | re.U):
            pats.append("thu_tuc")
        if re.search(r"\b(được\s+cấp|bị\s+thu\s+hồi|có\s+hiệu\s+lực|hết\s+hiệu\s+lực)\b", t, flags=re.I | re.U):
            pats.append("ket_qua_phap_ly")
        if re.search(r"\bkhông\s+được\b|\bnghiêm\s+cấm\b", t, flags=re.I | re.U):
            pats.append("khong_duoc")
        if re.search(r"\bcó\s+quyền\b|\bđược\s+phép\b", t, flags=re.I | re.U):
            pats.append("co_quyen")
        return pats

    def _extract_exception_text(self, cand_text: str) -> str | None:
        t = _norm_space(cand_text)
        # IMPROVED: Better labor exception patterns, avoid deadline/threshold confusion
        m = re.search(r"(trừ\s+trường\s+hợp[^.;]{0,200}|trừ\s+khi[^.;]{0,200}|không\s+thuộc\s+trường\s+hợp[^.;]{0,200}|ngoại\s+trừ[^.;]{0,200}|nếu\s+không[^.;]{0,200})", t, flags=re.I | re.U)
        return m.group(1).strip() if m else None

    def _extract_threshold_text(self, cand_text: str) -> str | None:
        t = _norm_space(cand_text)
        m = re.search(r"((không\s+quá|ít\s+nhất|trở\s+lên|từ)\s+[^.;]{0,120})", t, flags=re.I | re.U)
        return m.group(1).strip() if m else None

    def _extract_legal_effect_text(self, cand_text: str) -> str | None:
        t = _norm_space(cand_text)
        # Simple grounded effects: cấp/thu hồi/khôi phục/chấp thuận/bị ... (kept short).
        m = re.search(
            r"\b(được\s+cấp[^.;]{0,120}|bị\s+thu\s+hồi[^.;]{0,120}|thu\s+hồi\s+Giấy[^.;]{0,120}|"
            r"được\s+công\s+bố[^.;]{0,120}|bị\s+tạm\s+ng(?:ừ|ư)ng[^.;]{0,120}|"
            r"khôi\s+phục[^.;]{0,120}|chấp\s+thuận[^.;]{0,120})",
            t,
            flags=re.I | re.U,
        )
        return m.group(1).strip()[:160] if m else None

    def _best_actor_text(self, *, cand_text: str, subject_span: str | None, unit_actor_hint: str | None) -> str | None:
        s = _norm_space(subject_span) if subject_span else ""
        if len(s) >= 4:
            return s
        if unit_actor_hint is not None:
            h = _norm_space(str(unit_actor_hint))
            if h and re.search(re.escape(h), cand_text, flags=re.I | re.U):
                return h
        return subject_span

    def _best_action_text(self, *, cand_text: str, action_span: str | None, unit_action_hint: str | None) -> str | None:
        s = _norm_space(action_span) if action_span else ""
        if len(s) >= 10:
            return s
        if unit_action_hint is not None:
            h = _norm_space(str(unit_action_hint))
            if h and re.search(re.escape(h), cand_text, flags=re.I | re.U):
                return h
        return action_span

    def _best_object_text(self, *, cand_text: str, unit_object_hint: str | None) -> str | None:
        obj = self._extract_object_text(cand_text)
        if obj:
            return obj
        if unit_object_hint is not None:
            h = _norm_space(str(unit_object_hint))
            if len(h) >= 5 and re.search(re.escape(h), cand_text, flags=re.I | re.U):
                return h
        return None

    def _extract_object_text(self, cand_text: str) -> str | None:
        t = _norm_space(cand_text)
        for pat in [
            r"\bGiấy\s+chứng\s+nhận\s+đăng\s+ký\s+doanh\s+nghiệp\b",
            r"\bnội\s+dung\s+đăng\s+ký\s+doanh\s+nghiệp\b",
            r"\bhồ\s+sơ\s+đăng\s+ký\s+doanh\s+nghiệp\b",
            r"\bDanh\s+sách\s+chủ\s+sở\s+hữu\s+hưởng\s+lợi\b",
        ]:
            m = re.search(pat, t, flags=re.I | re.U)
            if m:
                return m.group(0)
        return None

    def _should_extract_rule(self, *, cand_text: str, candidate_rule_type: str, confidence_manual: str) -> str:
        score = self._candidate_score(confidence_manual=confidence_manual, cand_text=cand_text)
        triggers = self._trigger_patterns(cand_text)
        if any(k in triggers for k in ["trong_thoi_han", "ho_so_bao_gom", "tru_truong_hop", "nguong_so_luong", "co_quan"]):
            return "co"
        if score in {"rat_cao", "cao"}:
            return "co"
        if score == "trung_binh":
            return "can_nhac"
        return "khong"

    def _extraction_priority(self, cand_text: str) -> str:
        triggers = self._trigger_patterns(cand_text)
        if any(k in triggers for k in ["ho_so_bao_gom", "trong_thoi_han", "tru_truong_hop", "nguong_so_luong"]):
            return "rat_cao"
        if "co_quan" in triggers:
            return "cao"
        if "dang_ky" in triggers or "thong_bao" in triggers:
            return "trung_binh"
        return "thap"

    # -------------------------------
    # Candidate generation/splitting
    # -------------------------------
    def _generate_candidates(self, unit_text: str) -> list[tuple[str, str]]:
        text = unit_text or ""
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 1) If the unit already contains multiple `a)`, `b)` items, split first.
        point_matches = list(_POINT_ITEM_RE.finditer(text))
        if len(point_matches) >= 2:
            segs: list[tuple[str, str]] = []
            for i, m in enumerate(point_matches):
                start = m.start()
                end = point_matches[i + 1].start() if i + 1 < len(point_matches) else len(text)
                cand = text[start:end].strip()
                if cand:
                    segs.append((cand, "split=points"))
            return segs[: self._max_candidates_per_unit]

        # 1b) PRIORITY: If unit has strong exception/procedure cues, emit those FIRST before obligation-heavy candidates.
        # This recovers missing semantic families that get buried in deontic-heavy windows.
        focused_exc = self._focused_exception_candidates(text)
        if focused_exc and len(focused_exc) >= 2:
            # Unit has multiple exception phrases → this is likely exception-focused, return them prioritized.
            return focused_exc[: self._max_candidates_per_unit]

        # 2) Otherwise: trigger-driven windows (broadened for recall).
        triggers = (
            OBLIGATION_TRIGGERS
            + PROHIBITION_TRIGGERS
            + PERMISSION_TRIGGERS
            + DEADLINE_TRIGGERS
            + DOSSIER_TRIGGERS
            + AUTHORITY_TRIGGERS
            + CONDITION_TRIGGERS
        )
        matches: list[tuple[int, int, str]] = []
        for trig in triggers:
            for m in trig.regex.finditer(text):
                matches.append((m.start(), m.end(), trig.name))
                # Don't early-break; we will cap after sorting to preserve coverage.

        # Also window around exception/threshold/effect/procedure cues even if no shared triggers fired.
        for name, rx in [
            ("exception", self._exception_re),
            ("threshold", self._threshold_re),
            ("legal_effect", self._legal_effect_re),
            ("procedure", self._procedure_re),
        ]:
            for m in rx.finditer(text):
                matches.append((m.start(), m.end(), name))
                # Cap after sorting.

        matches = sorted(matches, key=lambda x: x[0])
        if len(matches) > self._max_trigger_matches:
            matches = matches[: self._max_trigger_matches]
        if not matches:
            # Still allow focused exception/effect slices.
            focused = self._focused_exception_candidates(text) + self._focused_legal_effect_candidates(text)
            return focused[: self._max_candidates_per_unit]

        candidates: list[tuple[str, str]] = []
        seen: set[str] = set()
        for i, (s, e, trig_name) in enumerate(matches):
            start = max(0, s - self._pre_trigger_chars)
            start = self._align_window_start(text, start)
            end = matches[i + 1][0] if i + 1 < len(matches) else len(text)
            end = min(end, start + self._max_candidate_chars)
            chunk = text[start:end].strip()
            chunk = _trim_by_sentence_boundary(chunk, max_chars=self._max_candidate_chars)
            chunk = _norm_space(chunk)
            if not chunk:
                continue
            key = stable_hash(chunk[:140], n=10)
            if key in seen:
                continue
            seen.add(key)
            candidates.append((chunk, f"split=trigger_window; matched={trig_name}"))
            if len(candidates) >= self._max_candidates_per_unit:
                break
        # Add focused slices (non-overlapping, high-signal for missing types).
        for cand, why in self._focused_exception_candidates(text) + self._focused_legal_effect_candidates(text):
            key = stable_hash(cand[:140], n=10)
            if key in seen:
                continue
            seen.add(key)
            candidates.append((cand, why))
            if len(candidates) >= self._max_candidates_per_unit:
                break
        return self._drop_overlapping_fragments(candidates)

    # -------------------------------
    # Candidate filtering
    # -------------------------------
    def _is_candidate_good(self, text: str, *, source_ref: str = "", heading: str = "") -> bool:
        has_obligation = self._has_any_trigger(text, OBLIGATION_TRIGGERS)
        has_prohibition = self._has_any_trigger(text, PROHIBITION_TRIGGERS)
        has_deontic = self._has_any_trigger(text, OBLIGATION_TRIGGERS + PROHIBITION_TRIGGERS + PERMISSION_TRIGGERS)
        has_deadline = self._has_any_trigger(text, DEADLINE_TRIGGERS)
        has_document = self._has_any_trigger(text, DOSSIER_TRIGGERS)
        has_authority = self._has_any_trigger(text, AUTHORITY_TRIGGERS)
        has_condition = self._has_any_trigger(text, CONDITION_TRIGGERS) or bool(self._exception_re.search(text))
        has_threshold = bool(self._threshold_re.search(text))
        has_effect = bool(self._legal_effect_re.search(text))
        has_procedure = bool(self._procedure_re.search(text))

        # Must be normative cue-driven.
        if not (has_deontic or has_deadline or has_document or has_authority or has_condition or has_threshold or has_effect or has_procedure):
            return False

        # Definition/header-like filter: drop "X là Y" / "được hiểu là ..." unless it contains an
        # explicit obligation/prohibition marker (precision-first to avoid definition noise).
        has_strong_norm = self._has_strong_normative_cue(text)
        if (self._looks_definition_like(text) or self._is_status_description(text) or self._is_concept_description(text)) and not has_strong_norm:
            return False
        if self._is_from_glossary_section(source_ref=source_ref, heading=heading):
            if (self._looks_definition_like(text) or self._definition_strong_re.search(text)) and not has_strong_norm:
                return False

        # "được" alone is highly ambiguous in legal Vietnamese descriptions.
        has_permission = self._has_any_trigger(text, PERMISSION_TRIGGERS)
        if has_permission and not (has_obligation or has_prohibition or has_deadline or has_document) and not has_effect:
            if self._is_weak_permission_description(text):
                return False

        # Reduce multi-rule swallowing: many modality markers within one candidate.
        modal_count = self._count_modal_markers(text)
        if modal_count >= 2 and not (has_condition or has_threshold or has_effect):
            return False

        # If contains multiple points, it's risky (should have been split earlier).
        if len(re.findall(r"(?i)\b[a-zđ]\)", text, flags=re.U)) >= 2 and not has_document:
            return False

        # Lead-in fragments without main clause are noisy.
        if self._lead_in_only_re.search(text) and not (has_obligation or has_prohibition or has_document or has_deadline):
            return False

        # Subject-ish signal: for precision, require subject for deontic/authority candidates.
        has_subject = self._has_subject(text)
        has_action = self._has_action(text)

        # Exception: allow exception-only candidates even without full subject/action structure.
        # Exception phrases like "trừ trường hợp ..." are valid rules even if they lack subject/action detail.
        has_clear_exception = bool(self._exception_re.search(text)) and len(_norm_space(text)) >= 40
        
        if (has_deontic or has_authority) and not has_subject and not has_clear_exception:
            return False
        if has_deontic and not has_action and not has_clear_exception:
            return False
        # Document requirement sentences can be action-poor; allow if document cue exists.
        if not (has_document or has_authority or has_deontic or has_condition or has_threshold or has_effect or has_procedure) and not has_action:
            return False

        # For condition/threshold/effect-only candidates, avoid very short fragments.
        if (has_condition or has_threshold or has_effect) and len(_norm_space(text)) < max(self._min_sentence_chars, 55):
            return False

        # Candidate too short still can be useful; allow.
        return True

    def _looks_definition_like(self, text: str) -> bool:
        if self._definition_like_re.search(text):
            return True
        if re.search(r"\bđược\s+hiểu\s+là\b", text, flags=re.I | re.U):
            return True
        if re.search(r"\b(là\s+tình\s+trạng|là\s+việc|là\s+quyền|là\s+doanh\s+nghiệp)\b", text, flags=re.I | re.U):
            return True
        if _DEFINITION_HEAD_RE.search(text):
            return True
        return False

    def _is_status_description(self, text: str) -> bool:
        return bool(self._status_description_re.search(text))

    def _is_concept_description(self, text: str) -> bool:
        t = _norm_space(text)
        # Keep dossier patterns (e.g., "hồ sơ bao gồm ...") despite "bao gồm".
        if re.search(r"\bhồ\s+sơ\s+bao\s+gồm\b", t, flags=re.I | re.U):
            return False
        if re.search(r"\bbao\s+gồm\s+các\s+giấy\s+tờ\b", t, flags=re.I | re.U):
            return False
        return bool(self._concept_description_re.search(t))

    def _is_from_glossary_section(self, *, source_ref: str, heading: str) -> bool:
        h = (heading or "").lower()
        if "giải thích từ ngữ" in h:
            return True
        s = (source_ref or "").lower()
        if "doc_id=doc_01" in s and "article=4" in s:
            return True
        if "doc_id=doc_02" in s and "article=3" in s:
            return True
        return False

    def _has_strong_normative_cue(self, text: str) -> bool:
        has_deontic_strong = self._has_any_trigger(text, OBLIGATION_TRIGGERS + PROHIBITION_TRIGGERS)
        has_proc = self._has_any_trigger(text, DEADLINE_TRIGGERS + DOSSIER_TRIGGERS)
        return has_deontic_strong or has_proc

    def _is_weak_permission_description(self, text: str) -> bool:
        t = _norm_space(text)
        if re.search(r"\bđược\s+(hiểu\s+là|tạo\s+bởi|ghi\s+trên|lưu\s+giữ|xác\s+định)\b", t, flags=re.I | re.U):
            return True
        if re.search(r"\bđược\s+tổ\s+chức\b", t, flags=re.I | re.U):
            return True
        if re.search(r"\bđược\s+cấp\b", t, flags=re.I | re.U) and not re.search(r"\b(có\s+quyền|có\s+thể|phải|trách\s+nhiệm)\b", t, flags=re.I | re.U):
            return True
        return False

    def _count_modal_markers(self, text: str) -> int:
        return sum(len(t.regex.findall(text)) for t in (OBLIGATION_TRIGGERS + PROHIBITION_TRIGGERS + PERMISSION_TRIGGERS))

    def _has_subject(self, text: str) -> bool:
        return any(rx.search(text) for rx in self._subject_keywords)

    def _has_action(self, text: str) -> bool:
        return any(rx.search(text) for rx in self._action_verbs)

    def _has_any_trigger(self, text: str, triggers: list[Any]) -> bool:
        return any(t.regex.search(text) for t in triggers)

    # -------------------------------
    # Type inference
    # -------------------------------
    def _infer_sentence_type(self, text: str, cats: set[str], modality: str | None) -> str:
        if modality == "prohibition":
            return "prohibition"
        if modality == "obligation":
            return "obligation"
        if modality == "permission":
            return "permission"
        if "document" in cats:
            return "dossier"
        if "authority" in cats:
            return "procedure"
        if "deadline" in cats:
            return "deadline"
        if "condition" in cats:
            return "condition"
        if "status" in cats:
            return "status"
        return "duty"

    def _infer_candidate_rule_type(self, text: str) -> str:
        has_obligation = self._has_any_trigger(text, OBLIGATION_TRIGGERS)
        has_prohibition = self._has_any_trigger(text, PROHIBITION_TRIGGERS)
        has_permission = self._has_any_trigger(text, PERMISSION_TRIGGERS)
        has_deadline = self._has_any_trigger(text, DEADLINE_TRIGGERS)
        has_document = self._has_any_trigger(text, DOSSIER_TRIGGERS)
        has_authority = self._has_any_trigger(text, AUTHORITY_TRIGGERS)
        has_condition = self._has_any_trigger(text, CONDITION_TRIGGERS) or bool(self._exception_re.search(text))
        has_threshold = bool(self._threshold_re.search(text))
        has_effect = bool(self._legal_effect_re.search(text))
        has_procedure = bool(self._procedure_re.search(text))

        has_deontic = has_obligation or has_prohibition or has_permission

        if has_document and not has_authority and not has_deadline:
            return "document_requirement"
        if has_authority and self._has_authority_as_subject(text):
            return "authority_action"
        if has_authority and not (has_obligation or has_prohibition or has_document or has_deadline):
            return "other"
        if has_deadline:
            return "deadline"
        # Prioritize deontic over effects
        if has_obligation:
            if re.search(r"\bđăng\s*ký\b", text, re.I | re.U):
                return "registration_obligation"
            if re.search(r"\bthông\s*báo\b", text, re.I | re.U):
                return "notification"
            return "duty"
        if has_prohibition:
            return "prohibition"
        if has_permission and not (has_obligation or has_prohibition):
            if not self._is_permission_normative(text):
                return "other"
            return "permission"
        if has_effect:
            return "legal_effect"
        if has_threshold:
            return "threshold"
        if has_condition:
            return "condition"
        if has_procedure and not has_deontic:
            return "procedure"

    def _is_permission_normative(self, text: str) -> bool:
        if self._looks_definition_like(text) or self._is_status_description(text):
            return False
        if self._is_weak_permission_description(text):
            return False
        t = _norm_space(text)
        if re.search(r"\bđược\s+(quy\s+định|dùng|đọc|ghi|lưu\s+giữ|tạo)\b", t, flags=re.I | re.U):
            return False

        explicit_permission = bool(re.search(r"\b(có\s+quyền|có\s+thể|được\s+phép|được\s+quyền)\b", t, flags=re.I | re.U))
        duoc_action = bool(re.search(r"\bđược\s+(ký|yêu\s+cầu|đề\s+nghị|lựa\s+chọn|chuyển\s+nhượng|thành\s+lập)\b", t, flags=re.I | re.U))

        has_subject = self._has_subject(text)
        has_action = self._has_action(text)
        if not (explicit_permission or duoc_action):
            return False
        return has_subject and has_action

    def _cue_summary(self, text: str) -> str:
        parts: list[str] = []
        for group_name, triggers in [
            ("obligation", OBLIGATION_TRIGGERS),
            ("prohibition", PROHIBITION_TRIGGERS),
            ("permission", PERMISSION_TRIGGERS),
            ("deadline", DEADLINE_TRIGGERS),
            ("document", DOSSIER_TRIGGERS),
            ("authority", AUTHORITY_TRIGGERS),
        ]:
            if self._has_any_trigger(text, triggers):
                parts.append(group_name)
        return ",".join(parts) if parts else "none"

    # -------------------------------
    # Span extraction (Stage 2 -> Stage 3)
    # -------------------------------
    def _earliest_deontic_or_cue(self, text: str) -> tuple[int, int, str] | None:
        # Deontic first; then dossier; then authority.
        deontic_trigs = OBLIGATION_TRIGGERS + PROHIBITION_TRIGGERS + PERMISSION_TRIGGERS
        best: tuple[int, int, str] | None = None
        for trig in deontic_trigs:
            m = trig.regex.search(text)
            if not m:
                continue
            cand = (m.start(), m.end(), trig.name)
            if best is None or cand[0] < best[0]:
                best = cand
        if best is not None:
            return best

        for trig in DOSSIER_TRIGGERS + AUTHORITY_TRIGGERS:
            m = trig.regex.search(text)
            if not m:
                continue
            cand = (m.start(), m.end(), trig.name)
            if best is None or cand[0] < best[0]:
                best = cand
        return best

    def _extract_subject_action_modality(
        self, text: str
    ) -> tuple[str | None, str | None, str | None]:
        best = self._earliest_deontic_or_cue(text)
        if best is None:
            return None, None, None

        s, e, trig_name = best
        subject_prefix = text[:s].strip(" ,;:-")
        subject = self._trim_subject(subject_prefix)

        modality_span = text[s:e].strip()
        after = text[e:].strip()

        # Stop cues for action span extraction.
        # For deontic cut, keep authority verbs inside the action phrase.
        stop_triggers = []
        # Condition/Deadline are always stop cues.
        stop_triggers.extend(t.regex for t in CONDITION_TRIGGERS)
        stop_triggers.extend(t.regex for t in DEADLINE_TRIGGERS)
        stop_triggers.extend(t.regex for t in DOSSIER_TRIGGERS)
        if "dossier" not in trig_name.lower():
            # If cut is authority/dossier, also stop at authority cues to avoid mixing.
            stop_triggers.extend(t.regex for t in AUTHORITY_TRIGGERS)

        stop_pos = first_regex_pos(after, stop_triggers)
        action = after if stop_pos is None else after[:stop_pos]
        action = action.strip(" ,;:-")
        if not action:
            action = None
        return subject, action, modality_span

    def _recover_subject_span(self, text: str, subject: str | None, candidate_rule_type: str) -> str | None:
        if subject:
            return subject
        t = _norm_space(text)
        for rx in self._subject_priority_patterns:
            m = rx.search(t)
            if m:
                return m.group(1).strip()
        if candidate_rule_type == "authority_action":
            m_auth = self._authority_subject_re.search(t)
            if m_auth:
                return m_auth.group(0).strip()
        if candidate_rule_type in {"duty", "registration_obligation", "prohibition"}:
            m_ent = re.search(r"\b(Doanh nghiệp|Người thành lập doanh nghiệp|Công ty cổ phần)\b", t, flags=re.I | re.U)
            if m_ent:
                return m_ent.group(1).strip()
        return None

    def _trim_subject(self, subject_prefix: str) -> str | None:
        if not subject_prefix:
            return None
        # Avoid taking pure condition/time phrases as subject.
        if re.search(r"\b(trong\s+thời\s+hạn|kể\s+từ\s+ngày|chậm\s+nhất|khi|nếu|trường\s+hợp)\b", subject_prefix, flags=re.I | re.U):
            return None
        subject_prefix = subject_prefix.strip()
        if len(subject_prefix) > 120:
            subject_prefix = subject_prefix[-120:]
        return subject_prefix.strip() or None

    def _extract_condition_span(self, text: str) -> str | None:
        for trig in CONDITION_TRIGGERS:
            m = trig.regex.search(text)
            if not m:
                continue
            start = m.start()
            chunk = text[start : start + 220]
            stop_pos = first_regex_pos(
                chunk,
                stop_triggers=self._deadline_and_doc_and_auth_and_modals(),
                skip_prefix=True,
            )
            if stop_pos is not None:
                chunk = chunk[:stop_pos]
            chunk = chunk.strip(" ,;:-")
            if chunk and len(chunk) >= 8:
                return chunk
        return None

    def _deadline_and_doc_and_auth_and_modals(self) -> list[re.Pattern[str]]:
        return [t.regex for t in DEADLINE_TRIGGERS] + [t.regex for t in DOSSIER_TRIGGERS] + [t.regex for t in AUTHORITY_TRIGGERS] + [
            t.regex for t in (OBLIGATION_TRIGGERS + PROHIBITION_TRIGGERS + PERMISSION_TRIGGERS)
        ]

    def _extract_deadline_span(self, text: str) -> str | None:
        patterns: list[re.Pattern[str]] = [
            re.compile(r"(trong\s+(thời\s+hạn|vòng)|chậm\s+nhất)\s*(\d{1,3})\s*(ngày|tháng|năm)(\s+làm\s+việc)?[^.;\n]{0,90}", re.I | re.U),
            re.compile(r"(\d{1,3})\s*(ngày|tháng|năm)(\s+làm\s+việc)?\s*kể\s+từ\s+ngày[^.;\n]{0,90}", re.I | re.U),
            re.compile(r"(trong\s+(thời\s+hạn|vòng)[^.;\n]{0,80}?\bkể\s+từ\s+ngày[^.;\n]{0,90})", re.I | re.U),
            re.compile(r"(kể\s+từ\s+ngày[^.;\n]{0,120})", re.I | re.U),
            re.compile(r"(chậm\s+nhất[^.;\n]{0,120})", re.I | re.U),
        ]
        for p in patterns:
            m = p.search(text)
            if m:
                return m.group(0).strip()
        # Fallback.
        for trig in DEADLINE_TRIGGERS:
            m = trig.regex.search(text)
            if m:
                return text[m.start() : m.start() + 180].strip()
        return None

    def _extract_dossier_span(self, text: str) -> str | None:
        for trig in DOSSIER_TRIGGERS:
            m = trig.regex.search(text)
            if not m:
                continue
            start = m.start()
            chunk = text[start : start + 280]
            stop_pos = first_regex_pos(chunk, stop_triggers=[t.regex for t in AUTHORITY_TRIGGERS] + [t.regex for t in DEADLINE_TRIGGERS])
            if stop_pos is not None:
                chunk = chunk[:stop_pos]
            chunk = chunk.strip(" ,;:-")
            return chunk or None
        return None

    def _extract_authority_span(self, text: str) -> str | None:
        # Prefer explicit authority subject phrases (frame-ready).
        m_subj = self._authority_subject_re.search(text)
        if m_subj:
            return m_subj.group(0).strip()
        for trig in AUTHORITY_TRIGGERS:
            m = trig.regex.search(text)
            if not m:
                continue
            start = m.start()
            chunk = text[start : start + 240]
            stop_pos = first_regex_pos(chunk, stop_triggers=[t.regex for t in CONDITION_TRIGGERS] + [t.regex for t in DEADLINE_TRIGGERS])
            if stop_pos is not None:
                chunk = chunk[:stop_pos]
            chunk = chunk.strip(" ,;:-")
            return chunk or None
        return None

    def _estimate_confidence(self, modality: str | None, candidate_rule_type: str, cand_text: str) -> str:
        score = 0
        if modality in {"obligation", "prohibition"}:
            score += 2
        if candidate_rule_type in {"deadline", "document_requirement", "authority_action"}:
            score += 1
        if len(cand_text) <= 170:
            score += 1
        if self._looks_definition_like(cand_text):
            score -= 2
        if self._is_status_description(cand_text):
            score -= 1
        if self._lead_in_only_re.search(cand_text):
            score -= 1
        if score >= 3:
            return "high"
        if score >= 1:
            return "medium"
        return "low"

    def _align_window_start(self, text: str, start: int) -> int:
        if start <= 0:
            return 0
        i = start
        while i < len(text) and i > 0 and text[i - 1].isalnum():
            i += 1
            if i >= len(text):
                return start
        while i < len(text) and text[i] in " \t":
            i += 1
        return min(i, len(text))

    def _drop_overlapping_fragments(self, candidates: list[tuple[str, str]]) -> list[tuple[str, str]]:
        kept: list[tuple[str, str]] = []
        for text, note in candidates:
            t_norm = _norm_space(text).lower()
            drop = False
            for kt, _ in kept:
                k_norm = _norm_space(kt).lower()
                if t_norm in k_norm and len(t_norm) + 20 < len(k_norm):
                    drop = True
                    break
                if k_norm in t_norm and len(k_norm) + 20 < len(t_norm):
                    # Prefer richer candidate; replace older shorter one.
                    kept = [(x, n) for (x, n) in kept if _norm_space(x).lower() != k_norm]
            if drop:
                continue
            kept.append((text, note))
        return kept[: self._max_candidates_per_unit]

    def _passes_minimal_semantic_gate(
        self,
        *,
        cand_text: str,
        candidate_rule_type: str,
        subject_span: str | None,
        action_span: str | None,
    ) -> bool:
        if len(cand_text) < max(self._min_sentence_chars, 45):
            return False
        if re.match(r"^[a-zà-ỹđ]", cand_text):
            if not re.match(
                r"^(trường\s+hợp|đối\s+với|cơ\s+quan|doanh\s+nghiệp|người|tổ\s+chức|hồ\s+sơ|thông\s+báo|kèm\s+theo)",
                cand_text,
                flags=re.I | re.U,
            ):
                return False
        if self._lead_in_only_re.search(cand_text) and candidate_rule_type in {"other", "permission"}:
            return False
        if self._is_concept_description(cand_text) and candidate_rule_type in {"duty", "registration_obligation", "permission"}:
            return False
        if candidate_rule_type == "authority_action":
            if not self._has_authority_as_subject(cand_text):
                return False
            if not self._is_authority_subject_span(subject_span):
                return False
            if not self._authority_action_re.search(cand_text):
                return False
            # Authority actions should be explicit and not too short.
            if not action_span or len(_norm_space(action_span)) < 18:
                return False
        if not subject_span and not action_span:
            return False
        if not subject_span and candidate_rule_type not in {
            "document_requirement",
            "condition",
            "procedure",
            "legal_effect",
            "threshold",
            "deadline",
        }:
            return False
        if action_span and len(_norm_space(action_span)) < 10 and candidate_rule_type in {"permission", "authority_action", "duty", "registration_obligation"}:
            return False
        _weak_action_ok_types = {
            "condition",
            "procedure",
            "legal_effect",
            "threshold",
            "deadline",
            "document_requirement",
        }
        if self._is_weak_action_span(action_span) and candidate_rule_type not in _weak_action_ok_types:
            return False
        if (
            self._is_weak_subject(subject_span)
            and self._is_weak_action_span(action_span)
            and candidate_rule_type not in _weak_action_ok_types
        ):
            return False
        return True

    def _has_authority_as_subject(self, text: str) -> bool:
        t = _norm_space(text)
        # Relaxed check: if authority subject appears in text AND authority action verb appears anywhere,
        # count as authority_action (don't require strict 70-char co-location).
        has_authority_subject = bool(self._authority_subject_re.search(t)) or bool(self._authority_subject_head_re.search(t))
        has_authority_action = bool(self._authority_action_re.search(t))
        if has_authority_subject and has_authority_action:
            return True
        # Fallback to original strict pattern (head + action close together).
        if self._authority_subject_head_re.search(t):
            return True
        return bool(
            re.search(
                r"\b(cơ\s+quan\s+đăng\s+ký\s+kinh\s+doanh(?:\s+cấp\s+tỉnh)?|phòng\s+đăng\s+ký\s+kinh\s+doanh)\b[^.;]{0,70}\b(có\s+trách\s+nhiệm|tiếp\s+nhận|xem\s+xét|cấp|cập\s+nhật|từ\s+chối|ra\s+thông\s+báo)\b",
                t,
                flags=re.I | re.U,
            )
        )

    def _is_authority_subject_span(self, subject_span: str | None) -> bool:
        if not subject_span:
            return False
        return bool(self._authority_subject_re.search(_norm_space(subject_span)))

    def _is_weak_action_span(self, action_span: str | None) -> bool:
        if not action_span:
            return True
        a = _norm_space(action_span)
        if len(a) < 12:
            return True
        if re.fullmatch(r"(là|có|được|phải|không\s+được)", a, flags=re.I | re.U):
            return True
        if re.search(r"\b(đáp\s+ứng\s+các\s+tiêu\s+chí\s+sau\s+đây|phải\s+có\s+ít\s+nhất)\b", a, flags=re.I | re.U):
            return True
        if not self._has_action(a):
            return True
        return False

    def _is_weak_subject(self, subject_span: str | None) -> bool:
        if not subject_span:
            return True
        s = _norm_space(subject_span)
        if len(s) < 4:
            return True
        if re.fullmatch(r"(trường\s+hợp|đối\s+với|sau\s+khi|trước\s+khi)", s, flags=re.I | re.U):
            return True
        return False

    def _score_candidate_quality(
        self,
        cand_text: str,
        candidate_rule_type: str,
        subject_span: str | None,
        action_span: str | None,
    ) -> float:
        score = 0.0
        if self._has_strong_normative_cue(cand_text):
            score += 2.0
        if candidate_rule_type in {
            "deadline",
            "document_requirement",
            "authority_action",
            "duty",
            "prohibition",
            "condition",
            "procedure",
        }:
            score += 1.2
        if candidate_rule_type == "permission":
            score += 0.6
        if subject_span:
            score += 0.6
        if action_span and len(_norm_space(action_span)) >= 12:
            score += 0.8
        if self._looks_definition_like(cand_text):
            score -= 2.0
        if self._is_status_description(cand_text):
            score -= 1.2
        if self._lead_in_only_re.search(cand_text):
            score -= 0.8
        if len(cand_text) > 220:
            score -= 0.6
        return score

    def _deduplicate_overlapping_candidates(self, cands: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not cands:
            return []
        ranked = sorted(cands, key=lambda c: c["quality_score"], reverse=True)
        kept: list[dict[str, Any]] = []
        for cand in ranked:
            t_norm = _norm_space(cand["cand_text"]).lower()
            overlapped = False
            for k in kept:
                k_norm = _norm_space(k["cand_text"]).lower()
                if t_norm in k_norm or k_norm in t_norm:
                    overlapped = True
                    break
            if overlapped:
                continue
            kept.append(cand)
        kept = sorted(kept, key=lambda c: c["idx"])
        return kept[: self._max_candidates_per_unit]


def _trim_by_sentence_boundary(chunk: str, *, max_chars: int) -> str:
    chunk = chunk.strip()
    if not chunk:
        return chunk
    if len(chunk) > max_chars:
        chunk = chunk[:max_chars].rsplit(" ", 1)[0].strip()
    m = _PUNCT_STOP_RE.search(chunk)
    if m:
        chunk = chunk[: m.start()].strip()
    return chunk


def first_regex_pos(text: str, stop_triggers: list[re.Pattern[str]], *, skip_prefix: bool = False) -> int | None:
    best: int | None = None
    for rx in stop_triggers:
        m = rx.search(text)
        if not m:
            continue
        if skip_prefix and m.start() == 0:
            continue
        pos = m.start()
        if best is None or pos < best:
            best = pos
    return best

