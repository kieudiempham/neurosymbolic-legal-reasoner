"""Vietnamese legal structural segmentation (Chương/Mục/Điều/Khoản/Điểm).

Goal: produce *human review friendly* legal units with a traceable `source_ref`.

Heuristic scope:
- Recognize headings by regex at line starts.
- Build units at the lowest available level: point -> clause -> article preamble.
"""

from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any

from law_side.law_rulebase_models import LegalDocument, LegalUnit
from utils.ids import stable_hash
from utils.logger import get_logger


class LegalSegmenter:
    """Segment legal text into hierarchical `LegalUnit` records."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or {}
        self._log = get_logger(self.__class__.__name__)

        # Headings (case-insensitive, unicode).
        self._chapter_re = re.compile(
            r"^\s*(Chương|CHƯƠNG)\s+([0-9IVXLCDM]+)\s*(?:[.: -]\s*)?(.*)$",
            flags=re.IGNORECASE | re.UNICODE,
        )
        self._section_re = re.compile(
            r"^\s*(Mục|MỤC)\s+([0-9]+)\s*(?:[.: -]\s*)?(.*)$",
            flags=re.IGNORECASE | re.UNICODE,
        )
        self._article_re = re.compile(
            r"^\s*(Điều|ĐIỀU)\s+(\d+[a-z]?)\s*\.?\s*(.*)$",
            flags=re.IGNORECASE | re.UNICODE,
        )

        # Clause / point inside an article.
        self._clause_re = re.compile(r"^\s*(\d+)\.\s+(.*)$", flags=re.UNICODE)
        self._point_re = re.compile(r"^\s*([a-zđ])\)\s+(.*)$", flags=re.IGNORECASE | re.UNICODE)

        # Precision-first pre-filter markers at legal-unit layer.
        self._strong_markers: list[tuple[str, re.Pattern[str]]] = [
            ("phai", re.compile(r"\bphải\b", re.I | re.U)),
            ("chiu_trach_nhiem", re.compile(r"\bchịu\s+trách\s+nhiệm\b", re.I | re.U)),
            ("co_trach_nhiem", re.compile(r"\bcó\s+trách\s+nhiệm\b", re.I | re.U)),
            ("co_nghia_vu", re.compile(r"\bcó\s+nghĩa\s+vụ\b", re.I | re.U)),
            ("khong_duoc", re.compile(r"\bkhông\s+được\b", re.I | re.U)),
            ("nghiem_cam", re.compile(r"\bnghiêm\s+cấm\b", re.I | re.U)),
            ("trong_thoi_han", re.compile(r"\btrong\s+thời\s+hạn\b", re.I | re.U)),
            ("trong_vong", re.compile(r"\btrong\s+vòng\b", re.I | re.U)),
            ("ke_tu_ngay", re.compile(r"\bkể\s+từ\s+ngày\b", re.I | re.U)),
            ("ho_so_bao_gom", re.compile(r"\bhồ\s+sơ\s+bao\s+gồm\b", re.I | re.U)),
            ("kem_theo_ho_so", re.compile(r"\bkèm\s+theo\s+hồ\s+sơ\b", re.I | re.U)),
            ("bao_gom_giay_to", re.compile(r"\bbao\s+gồm\s+các\s+giấy\s+tờ\b", re.I | re.U)),
            ("thong_bao", re.compile(r"\bthông\s+báo\b", re.I | re.U)),
            ("dang_ky", re.compile(r"\bđăng\s+ký\b", re.I | re.U)),
            ("cap", re.compile(r"\bcấp\b", re.I | re.U)),
            ("cap_nhat", re.compile(r"\bcập\s+nhật\b", re.I | re.U)),
            ("luu_giu", re.compile(r"\blưu\s+giữ\b", re.I | re.U)),
            ("thu_hoi", re.compile(r"\bthu\s+hồi\b", re.I | re.U)),
            ("khoi_phuc", re.compile(r"\bkhôi\s+phục\b", re.I | re.U)),
            ("dieu_kien", re.compile(r"\b(khi|nếu|trường\s+hợp)\b", re.I | re.U)),
            ("ngoai_le", re.compile(r"\b(trừ\s+trường\s+hợp|ngoại\s+trừ|nếu\s+không)\b", re.I | re.U)),
            ("nguong_so_luong", re.compile(r"\b(từ\s+\d+|không\s+quá|ít\s+nhất|từ\s+.+\s+đến\s+.+|trở\s+lên)\b", re.I | re.U)),
        ]
        self._definition_like_res: list[re.Pattern[str]] = [
            re.compile(r"^\s*[^.;:\n]{1,120}\s+là\s+", re.I | re.U),
            re.compile(r"\bđược\s+hiểu\s+là\b", re.I | re.U),
            re.compile(r"\bgiải\s+thích\s+từ\s+ngữ\b", re.I | re.U),
            re.compile(r"\b(?:bao\s+gồm|gồm\s+các)\s+", re.I | re.U),
            re.compile(r"\blà\s+(?:một\s+)?(?:tổ\s+chức|doanh\s+nghiệp|việc)\b", re.I | re.U),
        ]

        self._min_unit_chars = int(self._config.get("min_unit_chars", 20))

    def segment(self, doc: LegalDocument) -> list[LegalUnit]:
        """Segment a document into units."""
        lines = doc.cleaned_text.split("\n")

        chapter: str | None = None
        section: str | None = None
        article: str | None = None
        article_heading: str = ""

        current_clause: str | None = None
        current_point: str | None = None

        article_lines: list[str] = []
        clause_lines: list[str] = []
        point_lines: list[str] = []

        preamble_emitted_for_article = False
        has_subunits_in_article = False

        unit_buffer_start_line = 0

        units: list[LegalUnit] = []

        def flush_point(end_line: int) -> None:
            nonlocal current_point, point_lines
            if current_point is None:
                return
            text = "\n".join(point_lines).strip()
            if len(text) >= self._min_unit_chars:
                unit_id = self._make_unit_id(
                    doc_code=doc.doc_code,
                    article=article,
                    clause=current_clause,
                    point=current_point,
                    sentence_index=1,
                    subsentence_index=1,
                )
                heading = self._format_heading(article, article_heading)
                parent_context = self._parent_context(chapter, section, article)
                text = self._strip_heading_from_text(text, heading)
                is_candidate, normative_signal, note = self._estimate_candidate_rule_signal(text, heading)
                source_ref = self._source_ref(unit_id, doc.doc_id, chapter, section, article, current_clause, current_point, unit_buffer_start_line, end_line)
                meta = self._build_unit_meta(
                    text=text,
                    heading=heading,
                    parent_context=parent_context,
                    doc_code=doc.doc_code,
                    article=article,
                    clause=current_clause,
                    point=current_point,
                    unit_type="diem",
                    normative_signal=normative_signal,
                    is_candidate=is_candidate,
                    source_ref=source_ref,
                    note=note,
                )
                units.append(
                    LegalUnit(
                        unit_id=unit_id,
                        doc_id=doc.doc_id,
                        doc_code=doc.doc_code,
                        chapter=chapter,
                        section=section,
                        article=article,
                        clause=current_clause,
                        point=current_point,
                        unit_type="diem",
                        heading=heading,
                        text=text,
                        parent_context=parent_context,
                        topic_tag=meta["topic_tag"],
                        normative_signal=meta["normative_signal"],
                        is_candidate_rule_sentence=is_candidate,
                        source_ref=source_ref,
                        unit_ref_full=meta["unit_ref_full"],
                        sentence_index=meta["sentence_index"],
                        subsentence_index=meta["subsentence_index"],
                        list_item_marker=meta["list_item_marker"],
                        deontic_signal=meta["deontic_signal"],
                        has_condition_marker=meta["has_condition_marker"],
                        has_deadline_marker=meta["has_deadline_marker"],
                        has_document_marker=meta["has_document_marker"],
                        has_authority_marker=meta["has_authority_marker"],
                        has_exception_marker=meta["has_exception_marker"],
                        has_threshold_marker=meta["has_threshold_marker"],
                        has_cross_reference=meta["has_cross_reference"],
                        cross_reference_text=meta["cross_reference_text"],
                        actor_hint=meta["actor_hint"],
                        action_hint=meta["action_hint"],
                        object_hint=meta["object_hint"],
                        rule_density_estimate=meta["rule_density_estimate"],
                        needs_split=meta["needs_split"],
                        split_reason=meta["split_reason"],
                        notes=meta["notes"],
                    )
                )
            current_point = None
            point_lines = []

        def flush_clause(end_line: int) -> None:
            nonlocal current_clause, clause_lines, preamble_emitted_for_article
            if current_clause is None:
                return
            text = "\n".join(clause_lines).strip()
            if len(text) >= self._min_unit_chars:
                unit_id = self._make_unit_id(
                    doc_code=doc.doc_code,
                    article=article,
                    clause=current_clause,
                    point=None,
                    sentence_index=1,
                    subsentence_index=1,
                )
                heading = self._format_heading(article, article_heading)
                parent_context = self._parent_context(chapter, section, article)
                text = self._strip_heading_from_text(text, heading)
                is_candidate, normative_signal, note = self._estimate_candidate_rule_signal(text, heading)
                source_ref = self._source_ref(unit_id, doc.doc_id, chapter, section, article, current_clause, None, unit_buffer_start_line, end_line)
                meta = self._build_unit_meta(
                    text=text,
                    heading=heading,
                    parent_context=parent_context,
                    doc_code=doc.doc_code,
                    article=article,
                    clause=current_clause,
                    point=None,
                    unit_type="khoan",
                    normative_signal=normative_signal,
                    is_candidate=is_candidate,
                    source_ref=source_ref,
                    note=note,
                )
                units.append(
                    LegalUnit(
                        unit_id=unit_id,
                        doc_id=doc.doc_id,
                        doc_code=doc.doc_code,
                        chapter=chapter,
                        section=section,
                        article=article,
                        clause=current_clause,
                        point=None,
                        unit_type="khoan",
                        heading=heading,
                        text=text,
                        parent_context=parent_context,
                        topic_tag=meta["topic_tag"],
                        normative_signal=meta["normative_signal"],
                        is_candidate_rule_sentence=is_candidate,
                        source_ref=source_ref,
                        unit_ref_full=meta["unit_ref_full"],
                        sentence_index=meta["sentence_index"],
                        subsentence_index=meta["subsentence_index"],
                        list_item_marker=meta["list_item_marker"],
                        deontic_signal=meta["deontic_signal"],
                        has_condition_marker=meta["has_condition_marker"],
                        has_deadline_marker=meta["has_deadline_marker"],
                        has_document_marker=meta["has_document_marker"],
                        has_authority_marker=meta["has_authority_marker"],
                        has_exception_marker=meta["has_exception_marker"],
                        has_threshold_marker=meta["has_threshold_marker"],
                        has_cross_reference=meta["has_cross_reference"],
                        cross_reference_text=meta["cross_reference_text"],
                        actor_hint=meta["actor_hint"],
                        action_hint=meta["action_hint"],
                        object_hint=meta["object_hint"],
                        rule_density_estimate=meta["rule_density_estimate"],
                        needs_split=meta["needs_split"],
                        split_reason=meta["split_reason"],
                        notes=meta["notes"],
                    )
                )
            current_clause = None
            clause_lines = []

        def flush_article_preamble(end_line: int) -> None:
            nonlocal article_lines, preamble_emitted_for_article, has_subunits_in_article
            if article is None:
                # Ignore any content before the first detected article.
                article_lines = []
                return
            if not article_lines:
                return
            text = "\n".join(article_lines).strip()
            if len(text) < self._min_unit_chars:
                article_lines = []
                return
            if has_subunits_in_article and preamble_emitted_for_article:
                # Already emitted once.
                article_lines = []
                return
            # Emit only when:
            # - no subunits exist in this article, OR
            # - we haven't emitted yet and we're flushing preamble.
            if (not has_subunits_in_article) or (has_subunits_in_article and not preamble_emitted_for_article):
                unit_id = self._make_unit_id(
                    doc_code=doc.doc_code,
                    article=article,
                    clause=None,
                    point=None,
                    sentence_index=1,
                    subsentence_index=1,
                )
                heading = self._format_heading(article, article_heading)
                parent_context = self._parent_context(chapter, section, article)
                text = self._strip_heading_from_text(text, heading)
                is_candidate, normative_signal, note = self._estimate_candidate_rule_signal(text, heading)
                source_ref = self._source_ref(unit_id, doc.doc_id, chapter, section, article, None, None, unit_buffer_start_line, end_line)
                meta = self._build_unit_meta(
                    text=text,
                    heading=heading,
                    parent_context=parent_context,
                    doc_code=doc.doc_code,
                    article=article,
                    clause=None,
                    point=None,
                    unit_type="dieu",
                    normative_signal=normative_signal,
                    is_candidate=is_candidate,
                    source_ref=source_ref,
                    note=note,
                )
                units.append(
                    LegalUnit(
                        unit_id=unit_id,
                        doc_id=doc.doc_id,
                        doc_code=doc.doc_code,
                        chapter=chapter,
                        section=section,
                        article=article,
                        clause=None,
                        point=None,
                        unit_type="dieu",
                        heading=heading,
                        text=text,
                        parent_context=parent_context,
                        topic_tag=meta["topic_tag"],
                        normative_signal=meta["normative_signal"],
                        is_candidate_rule_sentence=is_candidate,
                        source_ref=source_ref,
                        unit_ref_full=meta["unit_ref_full"],
                        sentence_index=meta["sentence_index"],
                        subsentence_index=meta["subsentence_index"],
                        list_item_marker=meta["list_item_marker"],
                        deontic_signal=meta["deontic_signal"],
                        has_condition_marker=meta["has_condition_marker"],
                        has_deadline_marker=meta["has_deadline_marker"],
                        has_document_marker=meta["has_document_marker"],
                        has_authority_marker=meta["has_authority_marker"],
                        has_exception_marker=meta["has_exception_marker"],
                        has_threshold_marker=meta["has_threshold_marker"],
                        has_cross_reference=meta["has_cross_reference"],
                        cross_reference_text=meta["cross_reference_text"],
                        actor_hint=meta["actor_hint"],
                        action_hint=meta["action_hint"],
                        object_hint=meta["object_hint"],
                        rule_density_estimate=meta["rule_density_estimate"],
                        needs_split=meta["needs_split"],
                        split_reason=meta["split_reason"],
                        notes=meta["notes"],
                    )
                )
                preamble_emitted_for_article = True
            article_lines = []

        for idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line:
                continue

            m_ch = self._chapter_re.match(line)
            if m_ch:
                # Flush any open structures at article level.
                flush_point(idx - 1)
                flush_clause(idx - 1)
                flush_article_preamble(idx - 1)

                chapter = f"{m_ch.group(2)}"
                section = None
                article = None
                article_heading = ""
                current_clause = None
                current_point = None
                preamble_emitted_for_article = False
                has_subunits_in_article = False
                unit_buffer_start_line = idx
                continue

            m_sec = self._section_re.match(line)
            if m_sec:
                flush_point(idx - 1)
                flush_clause(idx - 1)
                flush_article_preamble(idx - 1)

                section = f"{m_sec.group(2)}"
                article = None
                article_heading = ""
                current_clause = None
                current_point = None
                preamble_emitted_for_article = False
                has_subunits_in_article = False
                unit_buffer_start_line = idx
                continue

            m_art = self._article_re.match(line)
            if m_art:
                # New article boundary flush.
                flush_point(idx - 1)
                flush_clause(idx - 1)
                flush_article_preamble(idx - 1)

                article = m_art.group(2)
                article_heading = (m_art.group(3) or "").strip()
                current_clause = None
                current_point = None
                preamble_emitted_for_article = False
                has_subunits_in_article = False
                unit_buffer_start_line = idx
                continue

            m_clause = self._clause_re.match(line)
            if m_clause and article is not None:
                # New clause: flush point then clause.
                has_subunits_in_article = True
                flush_point(idx - 1)
                flush_clause(idx - 1)

                current_clause = m_clause.group(1)
                clause_lines = []
                current_point = None
                unit_buffer_start_line = idx
                remainder = m_clause.group(2).strip()
                if remainder:
                    clause_lines.append(remainder)
                continue

            m_point = self._point_re.match(line)
            if m_point and current_clause is not None:
                has_subunits_in_article = True
                flush_point(idx - 1)

                current_point = m_point.group(1).lower()
                point_lines = []
                unit_buffer_start_line = idx
                remainder = m_point.group(2).strip()
                if remainder:
                    point_lines.append(remainder)
                continue

            # Content line: append to the innermost buffer.
            if current_point is not None:
                point_lines.append(line)
            elif current_clause is not None:
                clause_lines.append(line)
            else:
                if article is not None:
                    article_lines.append(line)

        # Final flush.
        flush_point(len(lines))
        flush_clause(len(lines))
        flush_article_preamble(len(lines))

        self._log.info("Segmented doc_id=%s into %d units", doc.doc_id, len(units))
        return units

    def _format_heading(self, article: str | None, article_heading: str) -> str:
        if article is None:
            return (article_heading or "").strip()
        base = f"Điều {article}"
        if article_heading:
            return f"{base}. {article_heading}".strip()
        return base

    def _parent_context(self, chapter: str | None, section: str | None, article: str | None) -> str:
        parts = []
        if chapter:
            parts.append(f"Chương {chapter}")
        if section:
            parts.append(f"Mục {section}")
        if article:
            parts.append(f"Điều {article}")
        return " | ".join(parts)

    def _source_ref(
        self,
        unit_id: str,
        doc_id: str,
        chapter: str | None,
        section: str | None,
        article: str | None,
        clause: str | None,
        point: str | None,
        start_line: int,
        end_line: int,
    ) -> str:
        return (
            f"unit={unit_id}|doc_id={doc_id}|chapter={chapter or ''}|section={section or ''}|"
            f"article={article or ''}|clause={clause or ''}|point={point or ''}|lines={start_line}-{end_line}"
        )

    def _make_unit_id(
        self,
        *,
        doc_code: str,
        article: str | None,
        clause: str | None,
        point: str | None,
        sentence_index: int,
        subsentence_index: int,
    ) -> str:
        code = re.sub(r"[^0-9a-z]+", "_", (doc_code or "").lower()).strip("_")
        if "67_vbhn_vpqh" in code:
            doc_token = "LUATDN"
        elif "168_2025_nd_cp" in code:
            doc_token = "ND168"
        else:
            doc_token = code.upper()[:20] if code else "DOC"
        parts = [f"UNIT_{doc_token}"]
        if article:
            parts.append(f"D{article}")
        if clause:
            parts.append(f"K{clause}")
        if point:
            parts.append(str(point).upper())
        parts.append(f"S{sentence_index}")
        parts.append(f"SS{subsentence_index}")
        return "_".join(parts)

    def _structural_soft_context(self, heading: str, parent_context: str) -> dict[str, bool]:
        blob = f"{heading} {parent_context}".lower()
        return {
            "glossary": any(k in blob for k in ("giải thích từ ngữ", "chú giải từ ngữ")),
            "scope": "phạm vi điều chỉnh" in blob
            or ("phạm vi" in blob and "điều chỉnh" in blob),
            "applicability": "đối tượng áp dụng" in blob
            or ("đối tượng" in blob and "áp dụng" in blob),
            "concept_heading": any(
                k in blob
                for k in (
                    "khái niệm",
                    "nguyên tắc",
                    "chế độ",
                    "hình thức",
                    "đặc điểm",
                    "quyền tồn tại",
                    "tư cách pháp lý",
                    "cơ cấu tổ chức",
                )
            ),
        }

    def _pure_descriptive_opening(self, compact: str) -> bool:
        return bool(
            re.search(
                r"(?:^|\n)\s*[^.;]{0,200}\s+(?:là|là\s+một\s+|bao\s+gồm|gồm\s+các|được\s+hiểu\s+là)\b",
                compact,
                re.I | re.U,
            )
        )

    def _has_strong_normative_surface(self, compact: str) -> bool:
        return bool(
            re.search(
                r"\b(phải\s+|không\s+được|nghiêm\s+cấm|có\s+nghĩa\s+vụ|"
                r"tiếp\s+nhận\s+hồ\s+sơ|nộp\s+hồ\s+sơ|từ\s+chối\s+(?:cấp|đăng\s+ký|tiếp)|"
                r"cấp\s+(?:lại\s+)?Giấy\s+chứng\s+nhận|thu\s+hồi\s+Giấy|"
                r"yêu\s+cầu\s+(?:bổ\s+sung|sửa\s+đổi))\b",
                compact,
                re.I | re.U,
            )
        )

    def _semicolon_independent_clauses(self, compact: str) -> bool:
        if compact.count(";") < 1:
            return False
        parts = [p.strip() for p in compact.split(";") if p.strip()]
        if len(parts) < 2:
            return False

        def vein(s: str) -> bool:
            return bool(
                re.search(
                    r"\b(phải|không\s+được|có\s+nghĩa\s+vụ|có\s+trách\s+nhiệm|"
                    r"cấp(?!\s+(?:phó|bậc|trên|dưới))\s+|thu\s+hồi|từ\s+chối|được\s+phép|có\s+quyền)\b",
                    s,
                    re.I | re.U,
                )
            )

        return sum(1 for p in parts if vein(p)) >= 2

    def _co_quan_yeu_cau_weak(self, compact: str) -> bool:
        return bool(
            re.search(
                r"\b(?:"
                r"yêu\s+cầu\s+của\s+cơ\s+quan(?:\s+có\s+thẩm\s+quyền|\s+đại\s+diện\s+chủ\s+sở\s+hữu)?|"
                r"(?:theo|khi|nếu|trường\s+hợp)\s+(?:có\s+)?yêu\s+cầu\s+của\s+cơ\s+quan|"
                r"theo\s+yêu\s+cầu\s+(?:bằng\s+văn\s+bản\s+)?của\s+cơ\s+quan"
                r")\b",
                compact,
                flags=re.I | re.U,
            )
        )

    def _co_quan_strong_subject_act(self, compact: str) -> bool:
        return bool(
            re.search(
                r"\b(?:cơ\s+quan(?:\s+đăng\s+ký\s+kinh\s+doanh)?|phòng\s+đăng\s+ký(?:\s+kinh\s+doanh)?|"
                r"ủy\s+ban\s+nhân\s+dân)\s+"
                r"(?:cấp(?:\s+lại)?(?!\s+(?:phó|bậc|trên|dưới|tỉnh|huyện|xã|quận|phường|thành\s+phố))|thu\s+hồi|cập\s+nhật|thông\s+báo|"
                r"yêu\s+cầu\s+(?:sửa\s+đổi|bổ\s+sung)|xem\s+xét|giải\s+quyết|tiếp\s+nhận|từ\s+chối)\b",
                compact,
                flags=re.I | re.U,
            )
        )

    def _compress_action_hint_tail(self, phrase: str | None) -> str:
        """Drop long trailing 'theo yêu cầu của cơ quan…' tails; keep core legal act phrase."""
        if not phrase:
            return ""
        t = re.sub(r"\s+", " ", phrase).strip()
        m = re.search(
            r"\s+(?:theo|khi|nếu|trường\s+hợp)\s+(?:có\s+)?yêu\s+cầu\s+(?:bằng\s+văn\s+bản\s+)?của\s+cơ\s+quan",
            t,
            flags=re.I | re.U,
        )
        if m:
            t = t[: m.start()].strip().rstrip(",").rstrip(";")
        m2 = re.search(
            r"(?:[,;]\s*|\s+)yêu\s+cầu\s+của\s+cơ\s+quan(?:\s+có\s+thẩm\s+quyền|\s+đại\s+diện\s+chủ\s+sở\s+hữu)?(?:\s*,|\s*;|\s*$)",
            t,
            flags=re.I | re.U,
        )
        if m2:
            t = t[: m2.start()].strip().rstrip(",").rstrip(";")
        return t

    def _fallback_deontic_after_weak_co_quan(
        self, compact: str, *, has_obligation: bool, has_condition: bool
    ) -> str | None:
        if re.search(r"\b(không\s+được|nghiêm\s+cấm)\b", compact, flags=re.I | re.U):
            return "cam_doan"
        if re.search(
            r"\b(có\s+quyền|được\s+phép|được\s+quyền)\b", compact, flags=re.I | re.U
        ):
            return "quyen"
        if re.search(
            r"\b(có\s+trách\s+nhiệm|chịu\s+trách\s+nhiệm)\b",
            compact,
            flags=re.I | re.U,
        ):
            return "co_trach_nhiem"
        if has_obligation:
            return "nghia_vu"
        if has_condition:
            return "dieu_kien"
        if re.search(r"\b(có\s+thể)\b", compact, flags=re.I | re.U):
            return "co_the"
        return "mo_ta_pham_vi"

    def _fill_deontic_if_empty(
        self,
        compact: str,
        *,
        has_obligation: bool,
        has_condition: bool,
        descriptive_shell: bool,
        ctx: dict[str, bool],
    ) -> str | None:
        # High-precision cues: apply even inside descriptive shell when surface is clear.
        if re.search(r"\btừ\s+chối\b", compact, flags=re.I | re.U):
            return "quyen"
        if re.search(r"\b(không\s+được|nghiêm\s+cấm)\b", compact, flags=re.I | re.U):
            return "cam_doan"
        if re.search(
            r"\b(có\s+quyền|được\s+phép|được\s+quyền)\b", compact, flags=re.I | re.U
        ):
            return "quyen"
        if re.search(r"\bgiám\s+sát\b", compact, flags=re.I | re.U) and not re.search(
            r"^\s*[^.;]{0,80}\b(?:là|được\s+hiểu\s+là|bao\s+gồm)\b",
            compact,
            flags=re.I | re.U,
        ):
            return "co_trach_nhiem"
        if re.search(r"\btạm\s+ng(?:ừ|ư)ng\b", compact, flags=re.I | re.U) and re.search(
            r"\bkinh\s+doanh\b", compact, flags=re.I | re.U
        ):
            if has_obligation:
                return "nghia_vu"
            if has_condition or self._co_quan_yeu_cau_weak(compact):
                return "dieu_kien"
            if re.search(
                r"\b(có\s+thể|được\s+phép|được\s+quyền)\b", compact, flags=re.I | re.U
            ):
                return "co_the"
            return "co_the"
        if descriptive_shell and not has_obligation:
            if ctx.get("glossary"):
                return "dinh_nghia_ho_tro"
            if ctx.get("scope") or ctx.get("applicability"):
                return "mo_ta_pham_vi"
            return None
        if re.search(
            r"\b(có\s+trách\s+nhiệm|chịu\s+trách\s+nhiệm)\b",
            compact,
            flags=re.I | re.U,
        ):
            return "co_trach_nhiem"
        if has_obligation:
            return "nghia_vu"
        if has_condition:
            return "dieu_kien"
        if re.search(r"\b(có\s+thể)\b", compact, flags=re.I | re.U):
            return "co_the"
        return None

    def _clean_legacy_pipeline_note(self, note: str) -> str:
        """Strip obsolete matched=… / authority false-positive tags from upstream notes."""
        if not note or not note.strip():
            return ""
        parts = [p.strip() for p in re.split(r"[;|,]+", note) if p.strip()]
        out: list[str] = []
        for p in parts:
            if re.match(r"^matched\s*=", p, flags=re.I):
                continue
            if re.search(r"co_hanh_dong_cap", p, flags=re.I):
                continue
            out.append(p)
        return "; ".join(out)

    def _authority_act_strict(self, compact: str) -> tuple[bool, str | None]:
        if self._co_quan_yeu_cau_weak(compact) and not self._co_quan_strong_subject_act(
            compact
        ):
            return False, None
        if re.search(
            r"\b(nhà\s+nước|chính\s+phủ)\b",
            compact,
            re.I | re.U,
        ) and not re.search(
            r"\b(cơ\s+quan(?:\s+đăng\s+ký\s+kinh\s+doanh)?|phòng\s+đăng\s+ký|ủy\s+ban\s+nhân\s+dân)\b",
            compact,
            re.I | re.U,
        ):
            return False, None
        if re.search(
            r"\b(cơ\s+sở\s+dữ\s+liệu|hệ\s+thống\s+thông\s+tin)\b",
            compact,
            re.I | re.U,
        ) and not re.search(
            r"\b(cấp(?!\s+(?:phó|bậc|trên|dưới))|thu\s+hồi|tiếp\s+nhận|từ\s+chối|cập\s+nhật|thông\s+báo|"
            r"xử\s+lý|xem\s+xét|giải\s+quyết)\b",
            compact,
            re.I | re.U,
        ):
            return False, None
        body = (
            r"(?:cơ\s+quan(?:\s+đăng\s+ký\s+kinh\s+doanh)?|phòng\s+đăng\s+ký(?:\s+kinh\s+doanh)?|"
            r"ủy\s+ban\s+nhân\s+dân)"
        )
        cap_bad = r"(?:phó|bậc|trên|dưới|tỉnh|huyện|xã|quận|phường|thành\s+phố)"
        act = (
            rf"(?:cấp\s+lại|cấp(?!\s+{cap_bad})(?:\s+(?:Giấy|giấy|chứng\s+nhận))?|thu\s+hồi|cập\s+nhật|"
            r"thông\s+báo|tiếp\s+nhận|xử\s+lý|từ\s+chối|khôi\s+phục|xem\s+xét|giải\s+quyết|"
            r"yêu\s+cầu(?:\s+(?:sửa\s+đổi|bổ\s+sung))?)"
        )
        p1 = re.compile(rf"\b{body}[^.;]{{0,120}}?\b{act}", re.I | re.U)
        p2 = re.compile(rf"\b{act}[^.;]{{0,80}}?\b{body}", re.I | re.U)
        m = p1.search(compact) or p2.search(compact)
        if not m:
            return False, None
        span_l = m.group(0).lower()
        if re.search(rf"\bcấp\s+{cap_bad}\b", span_l, flags=re.I | re.U):
            return False, None
        return True, m.group(0).strip()[:100]

    def _document_obligation_surface(self, compact: str) -> tuple[bool, str | None]:
        rx = re.compile(
            r"\b(hồ\s+sơ(?:\s+đăng\s+ký|\s+đề\s+nghị|\s+bao\s+gồm)?|"
            r"kèm\s+theo\s+(?:hồ\s+sơ|bản)|nộp\s+hồ\s+sơ|nộp\s+(?:bản\s+)?(?:sao|chụp)|"
            r"giấy\s+đề\s+nghị|bản\s+sao(?:\s+công\s+chứng)?)\b",
            re.I | re.U,
        )
        m = rx.search(compact)
        if not m:
            return False, None
        return True, m.group(0).strip()[:90]

    def _threshold_rule_core(self, compact: str, descriptive_shell: bool) -> tuple[bool, str | None]:
        rx = re.compile(
            r"\b(?:từ\s+\d{1,3}(?:\s*,\s*\d{1,3})?\s*(?:đến|tới|-)\s*\d{1,3}(?:\s+(?:thành\s+viên|cổ\s+đông))?|"
            r"(?:ít\s+nhất|không\s+quá)\s+\d{1,4}(?:\s+(?:năm|ngày|tháng|cổ\s+đông|thành\s+viên))?|"
            r"\d{1,3}\s*%(?:\s+vốn)?|trên\s+\d{1,3}\s*%(?:\s+vốn)?|"
            r"tỷ\s+lệ[^.;]{0,40}?\d{1,3}\s*%)\b",
            re.I | re.U,
        )
        m = rx.search(compact)
        if not m:
            return False, None
        snippet = m.group(0).strip()
        if descriptive_shell and not self._has_strong_normative_surface(compact):
            return False, None
        return True, snippet[:120]

    def _build_unit_meta(
        self,
        *,
        text: str,
        heading: str,
        parent_context: str,
        doc_code: str,
        article: str | None,
        clause: str | None,
        point: str | None,
        unit_type: str,
        normative_signal: str | None,
        is_candidate: bool,
        source_ref: str,
        note: str,
    ) -> dict[str, Any]:
        compact = re.sub(r"\s+", " ", text).strip()
        markers = [name for name, rx in self._strong_markers if rx.search(compact)]

        ctx = self._structural_soft_context(heading, parent_context)
        definition_like = self._is_definition_like_unit(compact)
        descriptive_shell = self._pure_descriptive_opening(compact) or definition_like
        strong_surface = self._has_strong_normative_surface(compact)
        soft_meta_block = (
            ctx["glossary"] or ctx["scope"] or ctx["applicability"] or ctx["concept_heading"]
        )

        cond_rx = re.compile(r"\b(khi|nếu|trường\s+hợp|điều\s+kiện)\b", re.I | re.U)
        dl_rx = re.compile(
            r"\b(trong\s+thời\s+hạn|chậm\s+nhất|kể\s+từ\s+ngày|trong\s+vòng)\b", re.I | re.U
        )
        exc_rx = re.compile(r"\b(trừ\s+trường\s+hợp|ngoại\s+trừ|trừ\s+khi|nếu\s+không)\b", re.I | re.U)

        has_condition = bool(cond_rx.search(compact))
        dl_m = dl_rx.search(compact)
        has_deadline = bool(dl_m)
        has_authority, auth_evidence = self._authority_act_strict(compact)
        doc_ob, doc_evidence = self._document_obligation_surface(compact)
        has_document = doc_ob
        has_threshold, threshold_snippet = self._threshold_rule_core(compact, descriptive_shell)
        has_exception = bool(exc_rx.search(compact))

        has_cross_ref = bool(re.search(r"\b(điều|khoản|điểm)\s+\d+[a-z]?\b", compact, flags=re.I | re.U))
        cross_ref_match = re.search(r"((điều|khoản|điểm)\s+[^.;\n]{0,120})", compact, flags=re.I | re.U)
        cross_ref_text = cross_ref_match.group(1).strip() if cross_ref_match else None

        has_obligation = bool(
            re.search(
                r"\b(phải|có\s+nghĩa\s+vụ|chịu\s+trách\s+nhiệm|có\s+trách\s+nhiệm|thực\s+hiện\s+nghĩa\s+vụ)\b",
                compact,
                flags=re.I | re.U,
            )
        )
        has_thu_tuc = bool(re.search(r"\b(trình\s+tự|thủ\s+tục)\b", compact, flags=re.I | re.U))

        conservative = soft_meta_block and not strong_surface
        if conservative:
            has_authority = False
            has_document = False
            has_deadline = False
            has_threshold = False
            has_exception = False
            has_thu_tuc = False
            has_condition = False
            auth_evidence = None
            doc_evidence = None
            threshold_snippet = None

        soft_marker_notes: list[str] = []
        procedural_anchor = has_obligation or strong_surface or has_authority
        if descriptive_shell and not procedural_anchor:
            if has_document:
                soft_marker_notes.append("bo_false_positive_ho_so_dinh_nghia")
                has_document = False
                doc_evidence = None
            if has_deadline:
                soft_marker_notes.append("bo_false_positive_thoi_han_mo_ta")
                has_deadline = False
                dl_m = None
            if has_exception:
                soft_marker_notes.append("bo_false_positive_ngoai_le_mo_ta")
                has_exception = False
            if has_condition:
                soft_marker_notes.append("bo_false_positive_dieu_kien_mo_ta")
                has_condition = False
            if has_threshold:
                soft_marker_notes.append("bo_false_positive_nguong_mo_ta")
                has_threshold = False
                threshold_snippet = None
            if has_thu_tuc:
                soft_marker_notes.append("bo_thu_tuc_mo_ta_khong_neo_nghia_vu")
                has_thu_tuc = False

        allow_hints = (
            has_obligation
            or strong_surface
            or ((not descriptive_shell) and not conservative)
            or bool(has_authority and auth_evidence)
        )
        if not allow_hints:
            allow_hints = bool(self._extract_action_hint_strict(compact))

        extra_meta_notes: list[str] = []
        actor_hint = self._extract_actor_hint(compact) if allow_hints else None
        if actor_hint and re.search(r"cơ\s+quan", actor_hint, flags=re.I | re.U) and not has_authority:
            actor_hint = None
            extra_meta_notes.append("bo_false_positive_authority")
        action_raw = self._extract_action_hint_strict(compact) if allow_hints else None
        action_hint = self._sanitize_action_hint(action_raw)
        action_hint, did_expand = self._expand_thin_action_hint(compact, action_hint)
        if did_expand:
            extra_meta_notes.append("mo_rong_action_hint")
        if action_raw and not action_hint:
            extra_meta_notes.append("sua_action_hint_bi_cat_manh")
        elif action_raw and action_hint and "mo_rong_action_hint" not in extra_meta_notes:
            raw_norm = re.sub(r"\s+", " ", action_raw).strip()
            if len(raw_norm) - len(action_hint) >= 12:
                extra_meta_notes.append("rut_gon_action_hint")
        object_raw = (
            self._extract_object_hint_rich(compact, action_hint, actor_hint) if allow_hints else None
        )
        object_mid, obj_upgrade_note = self._upgrade_object_hint_noun_phrase(compact, object_raw)
        object_hint = self._sanitize_object_hint(object_mid)
        if object_raw and not object_hint:
            extra_meta_notes.append("bo_object_hint_fragment")
        if obj_upgrade_note:
            extra_meta_notes.append(obj_upgrade_note)
        if (
            allow_hints
            and not object_hint
            and action_hint
            and actor_hint
            and has_threshold
            and threshold_snippet
        ):
            object_hint = f"ngưỡng ({threshold_snippet})"
            object_hint = self._sanitize_object_hint(object_hint)

        marker_evidences: list[str] = []
        note_reasons: list[str] = list(extra_meta_notes) + soft_marker_notes
        if conservative:
            note_reasons.append("dinh_nghia_khai_niem_khong_sinh_rule_manh")
        if has_condition and (m := cond_rx.search(compact)):
            marker_evidences.append(f"dau_hieu_dk={m.group(0).strip()[:80]}")
        if has_deadline and dl_m:
            marker_evidences.append(f"co_thoi_han_ro_rang_trong_cau={dl_m.group(0).strip()[:80]}")
        if has_document and doc_evidence:
            marker_evidences.append(f"co_liet_ke_thanh_phan_ho_so={doc_evidence}")
        if has_authority and auth_evidence:
            marker_evidences.append(f"dau_hieu_hanh_vi_co_quan={auth_evidence}")
        if has_exception and (m := exc_rx.search(compact)):
            marker_evidences.append(f"co_ngoai_le_rieng_can_tach={m.group(0).strip()[:80]}")
        if has_threshold and threshold_snippet:
            marker_evidences.append(f"co_nguong_so_luong_co_y_nghia_ap_dung={threshold_snippet[:120]}")

        split_reason_parts = (
            []
            if conservative
            else self._split_reasons_for_unit(
                compact=compact,
                has_obligation=has_obligation,
                has_deadline=has_deadline,
                has_thu_tuc=has_thu_tuc,
                has_document=has_document,
                has_exception=has_exception,
                has_threshold=has_threshold,
                has_authority=has_authority,
                strong_surface=strong_surface,
                descriptive_shell=descriptive_shell,
            )
        )

        marker_score = len(set(markers))
        if has_condition:
            marker_score += 1
        if has_deadline:
            marker_score += 1
        if has_document:
            marker_score += 1
        if has_authority:
            marker_score += 1
        if has_exception:
            marker_score += 1
        if has_threshold:
            marker_score += 1
        if marker_score >= 5:
            density = "rat_cao"
        elif marker_score >= 3:
            density = "cao"
        elif marker_score >= 2:
            density = "trung_binh"
        else:
            density = "thap"

        unit_ref_parts = []
        if article:
            unit_ref_parts.append(f"Điều {article}")
        if clause:
            unit_ref_parts.append(f"khoản {clause}")
        if point:
            unit_ref_parts.append(f"điểm {point}")
        unit_ref_full = " ".join(unit_ref_parts).strip()

        if conservative:
            if ctx["glossary"]:
                deontic: str | None = "dinh_nghia_ho_tro"
            elif ctx["scope"] or ctx["applicability"]:
                deontic = "mo_ta_pham_vi"
            elif definition_like or descriptive_shell:
                deontic = "dinh_nghia_ho_tro"
            else:
                deontic = "mo_ta_pham_vi"
            deontic_secondary: list[str] = []
        else:
            deontic, deontic_secondary = self._primary_and_secondary_deontic(
                compact,
                has_condition=has_condition,
                has_deadline=has_deadline,
                has_document=has_document,
                has_authority=has_authority,
                has_exception=has_exception,
                has_threshold=has_threshold,
                has_thu_tuc=has_thu_tuc,
                has_obligation=has_obligation,
                descriptive_shell=descriptive_shell,
                strong_surface=strong_surface,
            )
        post_deontic_notes: list[str] = []
        if not conservative:
            if (
                self._co_quan_yeu_cau_weak(compact)
                and not self._co_quan_strong_subject_act(compact)
                and deontic == "hanh_dong_co_quan"
            ):
                deontic = self._fallback_deontic_after_weak_co_quan(
                    compact, has_obligation=has_obligation, has_condition=has_condition
                )
                deontic_secondary = []
                post_deontic_notes.append("bo_false_positive_authority_yeu_cau_cua_co_quan")
            if deontic is None:
                filled = self._fill_deontic_if_empty(
                    compact,
                    has_obligation=has_obligation,
                    has_condition=has_condition,
                    descriptive_shell=descriptive_shell,
                    ctx=ctx,
                )
                if filled:
                    deontic = filled
                    post_deontic_notes.append("sua_deontic_signal_bo_sung")

        topic = self._infer_topic_tag_rich(compact, heading, parent_context, conservative, ctx)
        sentence_index = 1
        subsentence_index = 1
        list_item_marker = point if point else (clause if clause else None)
        split_reason = ";".join(dict.fromkeys(split_reason_parts)) if split_reason_parts else None
        needs_split = "co" if (split_reason and not conservative) else "khong"
        if needs_split == "khong":
            split_reason = None

        notes_parts: list[str] = []
        if note:
            cleaned = self._clean_legacy_pipeline_note(note)
            if cleaned.strip() != note.strip():
                note_reasons.append("don_notes_cu")
            if cleaned:
                notes_parts.append(cleaned)
        if post_deontic_notes:
            note_reasons.extend(post_deontic_notes)
        if note_reasons:
            notes_parts.extend(note_reasons)
        if deontic_secondary:
            notes_parts.append(f"deontic_phu={','.join(deontic_secondary)}")
        if marker_evidences:
            notes_parts.append(";".join(marker_evidences))
        if split_reason:
            notes_parts.append(f"needs_split={split_reason}")
        notes = "; ".join(notes_parts) if notes_parts else ""

        return {
            "unit_ref_full": unit_ref_full,
            "sentence_index": sentence_index,
            "subsentence_index": subsentence_index,
            "list_item_marker": list_item_marker,
            "normative_signal": normative_signal,
            "deontic_signal": deontic,
            "topic_tag": topic,
            "has_condition_marker": has_condition,
            "has_deadline_marker": has_deadline,
            "has_document_marker": has_document,
            "has_authority_marker": has_authority,
            "has_exception_marker": has_exception,
            "has_threshold_marker": has_threshold,
            "has_cross_reference": has_cross_ref,
            "cross_reference_text": cross_ref_text,
            "actor_hint": actor_hint,
            "action_hint": action_hint,
            "object_hint": object_hint,
            "rule_density_estimate": density,
            "needs_split": needs_split,
            "split_reason": split_reason,
            "notes": notes,
        }

    def _split_reasons_for_unit(
        self,
        *,
        compact: str,
        has_obligation: bool,
        has_deadline: bool,
        has_thu_tuc: bool,
        has_document: bool,
        has_exception: bool,
        has_threshold: bool,
        has_authority: bool,
        strong_surface: bool,
        descriptive_shell: bool,
    ) -> list[str]:
        parts: list[str] = []
        norm_anchor = has_obligation or strong_surface
        if descriptive_shell and not (norm_anchor or has_authority or has_exception or has_threshold):
            return []
        list_hits = len(re.findall(r"\b[a-zđ]\)", compact, flags=re.I | re.U))
        if list_hits >= 2 and norm_anchor:
            parts.append("co_liet_ke_thanh_phan")
        if self._semicolon_independent_clauses(compact) and norm_anchor:
            parts.append("nhieu_ve_nghia_vu")
        if has_obligation and has_deadline and norm_anchor:
            parts.append("vua_thoi_han_vua_nghia_vu")
        if has_thu_tuc and has_document and norm_anchor:
            parts.append("vua_thu_tuc_vua_ho_so")
        priv = bool(
            re.search(
                r"\b(doanh\s+nghiệp|công\s+ty|người\s+thành\s+lập|chủ\s+sở\s+hữu)\b",
                compact,
                flags=re.I | re.U,
            )
        )
        pub = bool(
            re.search(
                r"\b(cơ\s+quan(?:\s+đăng\s+ký\s+kinh\s+doanh)?|phòng\s+đăng\s+ký|ủy\s+ban\s+nhân\s+dân)\b",
                compact,
                flags=re.I | re.U,
            )
        )
        if priv and pub and has_authority and norm_anchor:
            parts.append("vua_chu_the_tu_nhan_vua_co_quan")
        actor_hits = re.findall(
            r"\b(doanh\s+nghiệp|công\s+ty|cơ\s+quan|người\s+thành\s+lập|chủ\s+sở\s+hữu|thành\s+viên\s+hợp\s+danh|thành\s+viên\s+công\s+ty)\b",
            compact,
            flags=re.I | re.U,
        )
        multi_phai = len(re.findall(r"\bphải\b", compact, flags=re.I | re.U)) >= 2
        if (
            len({h.lower().replace(" ", "") for h in actor_hits}) >= 2
            and norm_anchor
            and not descriptive_shell
            and (
                multi_phai
                or self._semicolon_independent_clauses(compact)
                or (priv and pub and has_authority)
            )
        ):
            parts.append("nhieu_chu_the")
        if has_exception and norm_anchor:
            parts.append("co_ngoai_le_rieng")
        if has_threshold and norm_anchor:
            parts.append("co_nguong_dinh_luong")
        outcomes = re.findall(
            r"\b(cấp(?!\s+(?:phó|bậc|trên|dưới))|từ\s+chối|thu\s+hồi|khôi\s+phục|chấp\s+thuận)\b",
            compact,
            flags=re.I | re.U,
        )
        if len(outcomes) >= 2 and re.search(r"\b(và|hoặc|;)\b", compact, flags=re.I | re.U):
            parts.append("co_nhieu_ket_qua_phap_ly")
        return parts

    def _primary_and_secondary_deontic(
        self,
        compact: str,
        *,
        has_condition: bool,
        has_deadline: bool,
        has_document: bool,
        has_authority: bool,
        has_exception: bool,
        has_threshold: bool,
        has_thu_tuc: bool,
        has_obligation: bool,
        descriptive_shell: bool,
        strong_surface: bool,
    ) -> tuple[str | None, list[str]]:
        if descriptive_shell and not strong_surface and not has_obligation:
            return "dinh_nghia_ho_tro", []

        signals: list[tuple[int, str]] = []
        prio = {
            "cam_doan": 0,
            "quyen": 1,
            "co_trach_nhiem": 2,
            "nghia_vu": 3,
            "thoi_han": 4,
            "thu_tuc": 5,
            "ho_so": 6,
            "hanh_dong_co_quan": 7,
            "ngoai_le": 8,
            "dieu_kien": 9,
            "nguong_so_luong": 10,
            "co_the": 11,
        }

        def add(p: int, label: str) -> None:
            signals.append((p, label))

        if re.search(r"\b(không\s+được|nghiêm\s+cấm)\b", compact, flags=re.I | re.U):
            add(prio["cam_doan"], "cam_doan")
        allow_quyen = not (descriptive_shell and not strong_surface)
        if allow_quyen and re.search(
            r"\b(có\s+quyền|được\s+phép|được\s+quyền)\b", compact, flags=re.I | re.U
        ):
            add(prio["quyen"], "quyen")
        if re.search(r"\b(có\s+trách\s+nhiệm|chịu\s+trách\s+nhiệm)\b", compact, flags=re.I | re.U):
            add(prio["co_trach_nhiem"], "co_trach_nhiem")
        if has_obligation and not any(s[1] == "co_trach_nhiem" for s in signals):
            add(prio["nghia_vu"], "nghia_vu")
        if has_deadline and (strong_surface or has_obligation or has_authority):
            add(prio["thoi_han"], "thoi_han")
        if has_thu_tuc and (strong_surface or has_obligation):
            add(prio["thu_tuc"], "thu_tuc")
        if has_document and (strong_surface or has_obligation or has_authority):
            add(prio["ho_so"], "ho_so")
        if has_authority:
            add(prio["hanh_dong_co_quan"], "hanh_dong_co_quan")
        if has_exception and (strong_surface or has_obligation):
            add(prio["ngoai_le"], "ngoai_le")
        if has_condition and (strong_surface or has_obligation or has_exception):
            add(prio["dieu_kien"], "dieu_kien")
        if has_threshold and (strong_surface or has_obligation or has_authority):
            add(prio["nguong_so_luong"], "nguong_so_luong")
        if re.search(r"\b(có\s+thể)\b", compact, flags=re.I | re.U) and (
            strong_surface or has_obligation
        ):
            add(prio["co_the"], "co_the")

        if not signals:
            if re.search(r"\bđối\s+tượng\s+áp\s+dụng\b", compact, flags=re.I | re.U):
                return "mo_ta_pham_vi", []
            if descriptive_shell:
                return "dinh_nghia_ho_tro", []
            return None, []

        signals.sort(key=lambda x: x[0])
        primary = signals[0][1]
        if primary == "hanh_dong_co_quan" and not has_authority:
            signals = [x for x in signals if x[1] != "hanh_dong_co_quan"]
            if not signals:
                if has_obligation:
                    return "nghia_vu", []
                if has_condition:
                    return "dieu_kien", []
                if descriptive_shell:
                    return "dinh_nghia_ho_tro", []
                return None, []
            signals.sort(key=lambda x: x[0])
            primary = signals[0][1]
        secondary = list(dict.fromkeys([label for _, label in signals[1:] if label != primary]))
        return primary, secondary

    def _infer_topic_tag_rich(
        self,
        text: str,
        heading: str,
        parent_context: str,
        conservative: bool,
        ctx: dict[str, bool],
    ) -> str | None:
        low = text.lower()
        blob = f"{heading} {parent_context}".lower()
        hlow = heading.lower()
        lead = low[:220]

        if ctx.get("glossary") or "giải thích từ ngữ" in hlow:
            return "dinh_nghia_phap_ly"
        if ctx.get("scope") or "phạm vi điều chỉnh" in blob:
            return "pham_vi_ap_dung"
        if ctx.get("applicability") or "đối tượng áp dụng" in blob:
            return "pham_vi_ap_dung"
        if conservative:
            return "dinh_nghia_phap_ly"

        if "thu hồi" in low and ("giấy chứng nhận" in low or "giấy phép" in low):
            return "thu_hoi_giay_chung_nhan"
        if "tạm ngừng" in low or "tạm ngưng" in low:
            return "tam_ngung"
        if (
            "hội đồng quản trị" in low
            or "ban kiểm soát" in low
            or "hội đồng thành viên" in low
            or "tổ chức quản lý" in low
            or "người quản lý" in low
            or "quản trị công ty" in low
        ):
            return "to_chuc_quan_ly"
        if (
            "công bố thông tin" in low
            or "niêm yết" in low
            or "thông tin trên cổng thông tin" in low
            or ("công khai" in low and "thông tin" in low)
        ):
            return "cong_bo_thong_tin"
        if "cung cấp thông tin" in low or (
            "cung cấp" in low and "thông tin" in low and "báo cáo" not in lead[:80]
        ):
            return "cung_cap_thong_tin"
        if (
            "hợp đồng" in low
            or "giao dịch" in low
            or "người có liên quan" in low
            or ("giao dịch" in low and "liên quan" in low)
            or ("chuyển nhượng" in low and "phần vốn" in low)
        ):
            return "hop_dong_giao_dich_lien_quan"
        if "góp vốn" in low and ("thực hiện" in low or "đủ" in low or "vốn" in low):
            return "gop_von"
        if "đăng ký thay đổi" in low or ("thay đổi" in low and "đăng ký" in low):
            return "dang_ky_thay_doi"
        if "chi nhánh" in low or "văn phòng đại diện" in low or "địa điểm kinh doanh" in low:
            return "chi_nhanh_van_phong_dai_dien"
        if "giải thể" in low:
            return "giai_the"
        _idx_vdl = low.find("vốn điều lệ")
        centrality_von = (
            "vốn điều lệ" in blob
            or "điều lệ" in hlow
            or "vốn điều lệ" in lead
            or (_idx_vdl >= 0 and _idx_vdl < 180)
        )
        if ("vốn điều lệ" in low or ("điều lệ" in low and "vốn" in low)) and centrality_von:
            return "von_dieu_le"
        ubo_central = (
            "chủ sở hữu hưởng lợi" in blob
            or "chủ sở hữu hưởng lợi" in hlow
            or "chủ sở hữu hưởng lợi" in lead
        )
        if ("chủ sở hữu hưởng lợi" in low or "ubo" in low) and ubo_central:
            return "chu_so_huu_huong_loi"
        co_dong_central = (
            "cổ đông" in blob
            or "thành viên công ty" in blob
            or "cổ đông" in hlow
            or any(
                x in low
                for x in (
                    "đại hội đồng cổ đông",
                    "biểu quyết",
                    "danh sách cổ đông",
                    "quyền cổ đông",
                )
            )
        )
        if (
            "cổ đông" in low
            or ("thành viên" in low and ("công ty" in low or "hợp danh" in low))
        ) and co_dong_central:
            return "co_dong_thanh_vien"
        if "đăng ký doanh nghiệp" in low or "đăng ký thành lập" in low:
            return "dang_ky_doanh_nghiep"
        if "đăng ký" in low and re.search(
            r"\b(phải|nộp|thông\s+báo|cơ\s+quan|hồ\s+sơ)\b", low, flags=re.I
        ):
            return "dang_ky_doanh_nghiep"
        if "tên doanh nghiệp" in low:
            return "ten_doanh_nghiep"
        return None

    def _clip_hint_short(self, text: str, max_chars: int) -> str:
        t = re.sub(r"\s+", " ", text).strip()
        if len(t) <= max_chars:
            return t
        return t[:max_chars].rsplit(" ", 1)[0]

    def _light_clean_action_hint(self, phrase: str | None) -> str | None:
        """Post-process expanded action_hint: clip + valid chunk only, less strict than full sanitize."""
        if not phrase:
            return None
        t = re.sub(r"\s+", " ", phrase).strip()
        t = self._compress_action_hint_tail(t)
        t = self._clip_hint_short(t, 72)
        if len(t) < 3:
            return None
        low = t.lower()
        if re.search(r"\bcấp\s+(?:phó|bậc|trên|dưới|tỉnh|huyện|xã)\b", low):
            return None
        return t

    def _expand_thin_action_hint(self, compact: str, hint: str | None) -> tuple[str | None, bool]:
        """Turn single-word / very short hints into verb+object chunks from the same sentence."""
        if not hint:
            return None, False
        t = re.sub(r"\s+", " ", hint).strip()
        if len(t) >= 22 and len(t.split()) >= 3:
            return t, False
        if len(t) > 18 and len(t.split()) >= 3:
            return t, False
        thin = (len(t.split()) <= 2 and len(t) <= 18) or (
            len(t.split()) == 1 and len(t) <= 12
        )
        if not thin:
            return t, False
        m = re.search(re.escape(t), compact, flags=re.I | re.U)
        if not m:
            return t, False
        segment = compact[m.start() :]
        segment = re.split(r"[.;]", segment, maxsplit=1)[0].strip()
        cpos = segment.find(",")
        if cpos > len(t) + 6:
            segment = segment[:cpos].strip()
        expanded = self._light_clean_action_hint(segment)
        if not expanded or len(expanded) <= len(t) + 3:
            return t, False
        return expanded, True

    def _upgrade_object_hint_noun_phrase(
        self, compact: str, hint: str | None
    ) -> tuple[str | None, str | None]:
        if not hint:
            return None, None
        low = re.sub(r"\s+", " ", hint).strip().lower()
        if low == "điều lệ" and re.search(
            r"\bđiều\s+lệ\s+công\s+ty\b", compact, flags=re.I | re.U
        ):
            m = re.search(r"\b(điều\s+lệ\s+công\s+ty)\b", compact, flags=re.I | re.U)
            if m:
                return m.group(1).strip(), "sua_object_hint_thanh_noun_phrase"
        if low in {"yêu cầu", "yêu cầu."} and re.search(
            r"\byêu\s+cầu\s+cung\s+cấp[^.;]{0,40}", compact, flags=re.I | re.U
        ):
            m = re.search(
                r"\b(yêu\s+cầu\s+cung\s+cấp\s+nguồn\s+lực)\b",
                compact,
                flags=re.I | re.U,
            )
            if m:
                return m.group(1).strip(), "sua_object_hint_thanh_noun_phrase"
        return hint, None

    def _sanitize_action_hint(self, phrase: str | None) -> str | None:
        if not phrase:
            return None
        t = re.sub(r"\s+", " ", phrase).strip()
        t = self._compress_action_hint_tail(t)
        t = self._clip_hint_short(t, 72)
        if len(t) < 2:
            return None
        low = t.lower()
        if re.search(r"\bcấp\s+(?:phó|bậc|trên|dưới)\b", low):
            return None
        bad_open = ("phó của", "với cơ", "bằng văn", "của người", "đối với")
        head = low[:40]
        if any(b in head for b in bad_open):
            return None
        garbage_starts = (
            "bao gồm",
            "bảo đảm",
            "có nghĩa là",
            "đồng nghĩa",
            "nghĩa là",
        )
        if any(low.startswith(g) for g in garbage_starts):
            return None
        bad_atoms = {
            "đăng ký",
            "nghĩa",
            "bao gồm",
            "bảo đảm",
            "công ty",
            "thông báo",
            "cấp",
            "nộp",
        }
        if low in bad_atoms:
            return None
        thin_starts = ("cấp", "thông báo", "đăng ký", "gửi", "nộp")
        toks = low.split()
        first = toks[0] if toks else ""
        if len(toks) == 1 and first in thin_starts:
            return None
        if first in thin_starts and len(t) < 20:
            return None
        return t

    def _sanitize_object_hint(self, phrase: str | None) -> str | None:
        if not phrase:
            return None
        t = re.sub(r"\s+", " ", phrase).strip()
        t = self._clip_hint_short(t, 90)
        low = t.lower().rstrip(".")
        allow_short_legal = low in {"hồ sơ", "vốn điều lệ"}
        if len(t) < 5 and not allow_short_legal:
            return None
        fragment_atoms = {
            "yêu cầu",
            "áp dụng",
            "đáp ứng",
            "là cá",
            "loại đã",
            "có ít",
            "là công",
        }
        if low in fragment_atoms:
            return None
        bad = (
            "phó của",
            "với cơ",
            "bằng văn",
            "của người",
            "đối với",
            "theo yêu cầu của",
            "là người",
            "nghĩa",
            "đăng ký",
            "bao gồm",
            "bảo đảm",
        )
        if low in bad or low in {"công ty", "doanh nghiệp", "là người"}:
            return None
        if low == "điều lệ":
            return None
        for b in bad:
            if low.startswith(b) or low == b or f" {b}" in low:
                return None
        if low.split()[0] in {"nghĩa", "đăng", "bao", "bảo", "công"} and len(t) < 14:
            return None
        if len(t.split()) < 2 and len(t) < 12 and not allow_short_legal:
            return None
        if re.match(r"^là\s+người\b", low):
            return None
        if re.match(r"^là\s+c[aá]\b", low) and len(low) < 10:
            return None
        return t

    def _extract_actor_hint(self, text: str) -> str | None:
        m = re.search(r"\b(doanh nghiệp|công ty|người thành lập doanh nghiệp|cơ quan đăng ký kinh doanh|cơ quan thuế|tổ chức, cá nhân)\b", text, flags=re.I | re.U)
        return m.group(1) if m else None

    def _extract_action_hint(self, text: str) -> str | None:
        m = re.search(
            r"\b(đăng\s+ký|thông\s+báo|cấp|cấp\s+lại|cập\s+nhật|xem\s+xét|tiếp\s+nhận|từ\s+chối|thu\s+hồi|"
            r"khôi\s+phục|lưu\s+giữ|gửi|niêm\s+yết|công\s+bố|ban\s+hành|thực\s+hiện|bổ\s+sung|sửa\s+đổi|"
            r"chấm\s+dứt|chấp\s+thuận|phê\s+duyệt|đình\s+chỉ|giải\s+thể|đăng\s+tải)\b",
            text,
            flags=re.I | re.U,
        )
        return m.group(1) if m else None

    def _extract_action_hint_strict(self, compact: str) -> str | None:
        m = re.search(
            r"\b(đăng\s+ký(?:\s+thay\s+đổi)?|thông\s+báo|"
            r"cấp\s+lại|cấp(?!\s+(?:phó|bậc|trên|dưới))(?:\s+(?:Giấy|giấy|chứng\s+nhận))?|"
            r"cập\s+nhật|xem\s+xét|tiếp\s+nhận|từ\s+chối|thu\s+hồi|"
            r"khôi\s+phục|lưu\s+giữ|gửi|niêm\s+yết|công\s+bố|ban\s+hành|thực\s+hiện|bổ\s+sung|sửa\s+đổi|"
            r"chấm\s+dứt|chấp\s+thuận|phê\s+duyệt|đình\s+chỉ|giải\s+thể|đăng\s+tải|góp\s+vốn)\b",
            compact,
            flags=re.I | re.U,
        )
        if not m:
            return None
        start = m.start()
        chunk = compact[start:]
        chunk = re.split(r"[.;]", chunk, maxsplit=1)[0].strip()
        cl = chunk.lower()
        if re.search(r"\bcấp\s+(?:phó|bậc|trên|dưới)\b", cl):
            return None
        if "," in chunk and len(chunk) > 52:
            chunk = chunk.split(",", 1)[0].strip()
        if len(chunk) > 72:
            chunk = chunk[:72].rsplit(" ", 1)[0]
        if self._pure_descriptive_opening(compact) and not self._has_strong_normative_surface(compact):
            win = compact[max(0, start - 90) : min(len(compact), start + 90)]
            if not re.search(
                r"\b(phải|không\s+được|nộp|cơ\s+quan|tiếp\s+nhận|trong\s+thời\s+hạn|kể\s+từ)\b",
                win,
                flags=re.I | re.U,
            ):
                return None
        verb = m.group(1).strip()
        out = chunk if len(chunk) >= len(verb) + 3 else verb
        out = self._compress_action_hint_tail(out)
        return self._clip_hint_short(out, 72)

    def _extract_object_hint(self, text: str) -> str | None:
        for pat in [
            r"\b(Giấy chứng nhận đăng ký doanh nghiệp)\b",
            r"\b(hồ sơ đăng ký doanh nghiệp)\b",
            r"\b(nội dung đăng ký doanh nghiệp)\b",
            r"\b(Danh sách chủ sở hữu hưởng lợi)\b",
        ]:
            m = re.search(pat, text, flags=re.I | re.U)
            if m:
                return m.group(1)
        return None

    def _extract_object_hint_rich(
        self, text: str, action_hint: str | None, actor_hint: str | None
    ) -> str | None:
        base = self._extract_object_hint(text)
        if base:
            return base
        for pat in [
            r"\b(hồ\s+sơ\s+đăng\s+ký\s+hoạt\s+động\s+chi\s+nhánh)\b",
            r"\b(nội\s+dung\s+đăng\s+ký[^.;]{0,40}?)\b",
            r"\b(sổ\s+sách\s+kế\s+toán)\b",
            r"\b(cổ\s+đông\s+sáng\s+lập)\b",
            r"\b(thông\s+tin\s+về\s+chủ\s+sở\s+hữu\s+hưởng\s+lợi)\b",
            r"\b(thông\s+tin[^.;]{5,60}?chủ\s+sở\s+hữu\s+hưởng\s+lợi)\b",
            r"\b(vốn\s+điều\s+lệ)\b",
            r"\b(phần\s+vốn\s+góp)\b",
            r"\b(biên\s+bản\s+họp)\b",
            r"\b(quyết\s+định[^.;]{0,40}?)\b",
            r"\b(nghị\s+quyết[^.;]{0,40}?)\b",
            r"\b(danh\s+sách\s+cổ\s+đông|danh\s+sách\s+thành\s+viên)\b",
            r"\b(tài\s+liệu\s+[^.;]{5,80}?)\b",
            r"\b(bản\s+sao[^.;]{5,60}?)\b",
            r"\b(giấy\s+đề\s+nghị[^.;]{0,50}?)\b",
            r"\b(giấy\s+tờ[^.;]{5,70}?)\b",
        ]:
            m = re.search(pat, text, flags=re.I | re.U)
            if m:
                s = re.sub(r"\s+", " ", m.group(1 if m.lastindex else 0).strip())
                if 4 <= len(s) <= 120:
                    return s[:120]
        if action_hint:
            esc = re.escape(action_hint.strip())
            m = re.search(esc + r"\s+([^.;]{5,100}?)(?=\s|;|\.|,|$)", text, flags=re.I | re.U)
            if m:
                chunk = re.sub(r"\s+", " ", m.group(1).strip())
                for noise in ("theo", "trong", "khi", "nếu", "đối với"):
                    if chunk.lower().startswith(noise + " "):
                        chunk = chunk[len(noise) + 1 :].strip()
                if 5 <= len(chunk) <= 100 and not re.match(r"^(là|và|hoặc)\b", chunk, flags=re.I):
                    return chunk[:100]
        if actor_hint and re.search(r"\bphải\b", text, flags=re.I | re.U):
            m = re.search(r"\bphải\s+([^.;]{5,100}?)(?=\s|;|\.|,|trong\s+thời|$)", text, flags=re.I | re.U)
            if m:
                chunk = re.sub(r"\s+", " ", m.group(1).strip())
                if 5 <= len(chunk) <= 100:
                    return chunk[:100]
        return None

    def _strip_heading_from_text(self, text: str, heading: str) -> str:
        t = text.strip()
        h = heading.strip()
        if not t or not h:
            return t
        t_norm = re.sub(r"\s+", " ", t).strip().lower()
        h_norm = re.sub(r"\s+", " ", h).strip().lower()
        if t_norm.startswith(h_norm):
            stripped = t[len(heading) :].lstrip(" .:-\n\t")
            return stripped or t
        return t

    def _is_definition_like_unit(self, text: str) -> bool:
        compact = re.sub(r"\s+", " ", text).strip()
        if not compact:
            return False
        return any(rx.search(compact) for rx in self._definition_like_res)

    def _estimate_candidate_rule_signal(self, text: str, heading: str = "") -> tuple[bool, str | None, str]:
        compact = re.sub(r"\s+", " ", text).strip()
        if not compact:
            return False, None, ""

        matched = [name for name, rx in self._strong_markers if rx.search(compact)]
        if not matched:
            return False, None, ""

        strong_deontic = {"phai", "co_nghia_vu", "co_trach_nhiem", "chiu_trach_nhiem", "khong_duoc", "nghiem_cam"}
        # Weak lexical cues at legal-unit layer (often appear in definitions/descriptions).
        weak_lexical = {"dang_ky", "thong_bao", "cap", "cap_nhat", "luu_giu"}

        heading_lower = heading.lower()
        has_deontic = any(m in strong_deontic for m in matched)
        has_non_weak = any(m not in weak_lexical for m in matched)

        # Precision-first for glossary sections.
        if "giải thích từ ngữ" in heading_lower and not has_deontic:
            return False, None, "definition_like"

        # Precision-first: downgrade definition-like lines unless obligation/prohibition is explicit.
        if self._is_definition_like_unit(compact):
            if not has_deontic:
                return False, None, "definition_like"

        # Special-case: if a unit only contains {dang_ky, cap, thong_bao}, require procedural context.
        only_three = set(matched).issubset({"dang_ky", "cap", "thong_bao"})
        if only_three and (not has_deontic):
            has_procedural_context = bool(
                re.search(
                    r"\b(hồ\s+sơ|trình\s+tự|thủ\s+tục|thời\s+hạn|kể\s+từ\s+ngày|trong\s+vòng|trong\s+thời\s+hạn|cơ\s+quan|tiếp\s+nhận|từ\s+chối)\b",
                    compact,
                    flags=re.IGNORECASE | re.UNICODE,
                )
            )
            if not has_procedural_context:
                return False, None, "weak_signal_only"

        # If only weak lexical cues are present (broader set), keep conservative at legal-unit layer.
        if (not has_deontic) and (not has_non_weak):
            has_procedural_context = bool(
                re.search(
                    r"\b(hồ\s+sơ|trình\s+tự|thủ\s+tục|thời\s+hạn|kể\s+từ\s+ngày|trong\s+vòng|trong\s+thời\s+hạn|cơ\s+quan|tiếp\s+nhận|từ\s+chối)\b",
                    compact,
                    flags=re.IGNORECASE | re.UNICODE,
                )
            )
            if not has_procedural_context:
                return False, None, "weak_signal_only"

        # Broaden candidate coverage for deadline/document/authority/exception/threshold cues.
        broaden_cues = bool(
            re.search(
                r"\b(trong\s+thời\s+hạn|chậm\s+nhất|kể\s+từ\s+ngày|hồ\s+sơ\s+bao\s+gồm|kèm\s+theo|cơ\s+quan|trừ\s+trường\s+hợp|ngoại\s+trừ|nếu\s+không|không\s+quá|ít\s+nhất|trở\s+lên|từ\s+\d+)\b",
                compact,
                flags=re.I | re.U,
            )
        )
        signal = ";".join(matched[:3]) if matched else None
        if not matched and broaden_cues:
            signal = "mo_rong_tin_hieu_quy_tac"
        return bool(matched or broaden_cues), signal, ""
