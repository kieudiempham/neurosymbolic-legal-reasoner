"""Rule-based rubric scoring for paper-oriented review spreadsheets.

This module adds lightweight, human-review-friendly heuristics to classify:
- candidate normative sentences (keep / split / drop)
- extracted legal frames (frame quality for rule building)

The rubric targets your two Excel files:
- `candidate_normative_sentences.xlsx`
- `legal_frames_review.xlsx`
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


def _norm(s: Any) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return str(s)


def _has_any(text: str, patterns: list[re.Pattern[str]]) -> bool:
    return any(p.search(text) for p in patterns)


def _count_occurrences(text: str, patterns: list[re.Pattern[str]]) -> int:
    c = 0
    for p in patterns:
        c += len(p.findall(text))
    return c


def modality_label_from_candidate_row(row: pd.Series) -> str | None:
    """Infer coarse modality label from `modality_span` / sentence text."""
    sentence = _norm(row.get("sentence_text", ""))
    span = _norm(row.get("modality_span", ""))
    t = (span + " " + sentence).lower()

    if re.search(r"\bkhông được\b", t, flags=re.IGNORECASE):
        return "prohibition"
    if re.search(r"\bnghiêm cấm\b", t, flags=re.IGNORECASE):
        return "prohibition"
    if re.search(r"\bđược\b", t, flags=re.IGNORECASE) or re.search(
        r"\bcó quyền\b", t, flags=re.IGNORECASE
    ) or re.search(r"\bcó thể\b", t, flags=re.IGNORECASE):
        return "permission"
    if re.search(r"\bphải\b", t, flags=re.IGNORECASE) or re.search(
        r"\bcó nghĩa vụ\b", t, flags=re.IGNORECASE
    ) or re.search(r"\bchịu trách nhiệm\b", t, flags=re.IGNORECASE) or re.search(
        r"\bcó trách nhiệm\b", t, flags=re.IGNORECASE
    ):
        return "obligation"
    return None


def _subject_regexes() -> list[re.Pattern[str]]:
    return [
        re.compile(r"\bdoanh nghiệp\b", re.I | re.U),
        re.compile(r"\bcông ty\b", re.I | re.U),
        re.compile(r"\bcông ty cổ phần\b", re.I | re.U),
        re.compile(r"\bngười thành lập\b", re.I | re.U),
        re.compile(r"\bngười nộp\b", re.I | re.U),
        re.compile(r"\bhồ sơ\b", re.I | re.U),  # sometimes appears as subject; rubric wants penalize later
        re.compile(r"\bcơ quan\b", re.I | re.U),
        re.compile(r"\bcơ quan đăng ký kinh doanh\b", re.I | re.U),
        re.compile(r"\bcơ quan đăng ký kinh doanh cấp tỉnh\b", re.I | re.U),
        re.compile(r"\bủy ban\b", re.I | re.U),
        re.compile(r"\bban\b", re.I | re.U),
    ]


def _action_regexes() -> list[re.Pattern[str]]:
    return [
        re.compile(r"\bđăng ký\b", re.I | re.U),
        re.compile(r"\bthông báo\b", re.I | re.U),
        re.compile(r"\bgửi\b", re.I | re.U),
        re.compile(r"\bnộp\b", re.I | re.U),
        re.compile(r"\b cấp \b", re.I | re.U),
        re.compile(r"\bcấp\b", re.I | re.U),
        re.compile(r"\bxác nhận\b", re.I | re.U),
        re.compile(r"\btrách nhiệm xem xét\b", re.I | re.U),
        re.compile(r"\btrừ\b", re.I | re.U),
        re.compile(r"\bra quyết định\b", re.I | re.U),
        re.compile(r"\bthực hiện\b", re.I | re.U),
        re.compile(r"\btiếp nhận\b", re.I | re.U),
        re.compile(r"\b từ chối \b", re.I | re.U),
        re.compile(r"\btừ chối\b", re.I | re.U),
        re.compile(r"\bthay đổi\b", re.I | re.U),
        re.compile(r"\bcập nhật\b", re.I | re.U),
        re.compile(r"\bthủ tục\b", re.I | re.U),
        re.compile(r"\bchịu trách nhiệm\b", re.I | re.U),
        re.compile(r"\bsoạn\b", re.I | re.U),
    ]


def _normative_markers_regexes() -> dict[str, list[re.Pattern[str]]]:
    return {
        "obligation": [
            re.compile(r"\bphải\b", re.I | re.U),
            re.compile(r"\bcó nghĩa vụ\b", re.I | re.U),
            re.compile(r"\bchịu trách nhiệm\b", re.I | re.U),
            re.compile(r"\bcó trách nhiệm\b", re.I | re.U),
        ],
        "prohibition": [
            re.compile(r"\bkhông được\b", re.I | re.U),
            re.compile(r"\bnghiêm cấm\b", re.I | re.U),
        ],
        "permission": [
            re.compile(r"\bđược\b", re.I | re.U),
            re.compile(r"\bcó quyền\b", re.I | re.U),
            re.compile(r"\bcó thể\b", re.I | re.U),
        ],
        "deadline": [
            re.compile(r"\btrong\s+(thời\s+hạn|vòng)\b", re.I | re.U),
            re.compile(r"\btrong\s+vòng\b", re.I | re.U),
            re.compile(r"\bkể từ ngày\b", re.I | re.U),
            re.compile(r"\bchậm nhất\b", re.I | re.U),
        ],
        "dossier": [
            re.compile(r"\bhồ sơ bao gồm\b", re.I | re.U),
            re.compile(r"\bkèm theo\b", re.I | re.U),
            re.compile(r"\bbao gồm các giấy tờ\b", re.I | re.U),
            re.compile(r"\bbao gồm các tài liệu\b", re.I | re.U),
        ],
        "authority": [
            re.compile(r"\bcó trách nhiệm xem xét\b", re.I | re.U),
            re.compile(r"\bcấp\b", re.I | re.U),
            re.compile(r"\btừ chối\b", re.I | re.U),
            re.compile(r"\bthông báo\b", re.I | re.U),
        ],
    }


def score_candidate_row(row: pd.Series) -> dict[str, Any]:
    """Score one candidate normative sentence row."""
    sentence_text = _norm(row.get("sentence_text", "")).strip()
    subject_span = _norm(row.get("subject_span", "")).strip()
    action_span = _norm(row.get("action_span", "")).strip()
    modality_span = _norm(row.get("modality_span", "")).strip()
    time_span = _norm(row.get("time_span", "")).strip()
    document_span = _norm(row.get("document_span", "")).strip()
    authority_span = _norm(row.get("authority_span", "")).strip()

    text_lower = sentence_text.lower()
    marker_cfg = _normative_markers_regexes()

    has_marker = (
        _has_any(sentence_text, marker_cfg["obligation"])
        or _has_any(sentence_text, marker_cfg["prohibition"])
        or _has_any(sentence_text, marker_cfg["permission"])
        or _has_any(sentence_text, marker_cfg["deadline"])
        or _has_any(sentence_text, marker_cfg["dossier"])
        or _has_any(sentence_text, marker_cfg["authority"])
    )

    # Definition / definition-like heuristic.
    is_definition_like = bool(re.search(r"\b(là|được hiểu là)\b", sentence_text, re.I | re.U)) and not (
        _has_any(sentence_text, marker_cfg["obligation"])
        or _has_any(sentence_text, marker_cfg["prohibition"])
        or _has_any(sentence_text, marker_cfg["permission"])
    )
    is_named_definition = bool(
        re.search(r"^\s*(Doanh nghiệp|Chi nhánh|Cổ đông)\s+là\b", sentence_text, re.I | re.U)
    )

    # Too long / multi-rule.
    too_long = len(sentence_text) > 650
    swallow_points = bool(re.search(r"\b[a-zđ]\)\s+", sentence_text, re.I | re.U)) and bool(
        len(re.findall(r"\b[a-zđ]\)\s+", sentence_text, flags=re.I)) > 2
    )

    # Central action: action_span should include legal verbs.
    action_res = _action_regexes()
    has_action = bool(action_span) and _has_any(action_span, action_res)
    if not has_action:
        # Sometimes action_span is missing but sentence still includes legal verbs.
        has_action = _has_any(sentence_text, action_res)

    # Subject: look for entity words.
    subj_res = _subject_regexes()
    has_subject = bool(subject_span) and _has_any(subject_span, subj_res)
    if not has_subject:
        has_subject = _has_any(sentence_text, subj_res)

    # If subject seems to be only a time phrase => penalize.
    subject_mixed_with_deadline = bool(
        subject_span
        and (
            re.search(r"trong\s+thời\s+hạn|kể\s+từ\s+ngày|chậm\s+nhất", subject_span, re.I | re.U)
            or (time_span and subject_span.strip() == time_span.strip())
        )
    )

    # Deadline-in-window: if there is deadline cue, ensure time_span exists and is relatively short.
    has_deadline_cue = _has_any(sentence_text, marker_cfg["deadline"])
    deadline_window_ok = True
    if has_deadline_cue:
        deadline_window_ok = bool(time_span) and len(time_span) <= 120

    # "Not multiple independent rules": proxy by counting modality occurrences.
    modal_triggers = (
        marker_cfg["obligation"]
        + marker_cfg["prohibition"]
        + marker_cfg["permission"]
    )
    modal_count = _count_occurrences(sentence_text, modal_triggers)
    multi_rule_suspected = modal_count >= 2

    # Build 4/5 rubric criteria.
    c1 = has_marker
    c2 = has_subject and not subject_mixed_with_deadline
    c3 = has_action
    c4 = deadline_window_ok
    c5 = not (too_long or multi_rule_suspected or swallow_points)

    criteria_true = sum([1 if x else 0 for x in [c1, c2, c3, c4, c5]])

    # Decide error_type with priority.
    error_type: str | None = None
    if is_named_definition or is_definition_like:
        error_type = "definition_not_norm"
    elif too_long:
        error_type = "too_long_multi_rule"
    elif swallow_points:
        error_type = "bad_split_clause_point"
    elif not has_action:
        error_type = "missing_action"
    elif not c2:
        error_type = "missing_subject"
    elif sentence_text.strip().startswith(("trong thời hạn", "kể từ ngày", "trường hợp")) and not has_action:
        error_type = "case_without_main_clause"
    elif subject_mixed_with_deadline:
        error_type = "subject_lost_or_mixed"

    # Scoring mapping.
    if error_type in {"definition_not_norm", "too_long_multi_rule", "bad_split_clause_point"}:
        score = 0
        keep_or_split_or_drop = "drop"
    elif error_type in {"missing_action", "missing_subject", "subject_lost_or_mixed", "case_without_main_clause"}:
        score = 1 if criteria_true >= 3 else 0
        keep_or_split_or_drop = "split" if score == 1 else "drop"
    else:
        # Default: keep if 4/5, else 1 if useful.
        if criteria_true >= 4:
            score = 2
            keep_or_split_or_drop = "keep"
        elif criteria_true >= 3:
            score = 1
            keep_or_split_or_drop = "split"
        else:
            score = 0
            keep_or_split_or_drop = "drop"

    review_notes_parts: list[str] = []
    review_notes_parts.append(f"markers={int(c1)} subject={int(c2)} action={int(c3)} deadline_ok={int(c4)} simple={int(c5)}")
    if error_type:
        review_notes_parts.append(f"error={error_type}")
    if time_span:
        review_notes_parts.append(f"time_span_len={len(time_span)}")
    if document_span:
        review_notes_parts.append(f"doc_span_len={len(document_span)}")

    return {
        "rubric_candidate_score": score,
        "candidate_error_type": error_type,
        "keep_or_split_or_drop": keep_or_split_or_drop,
        "review_notes": "; ".join(review_notes_parts),
    }


def apply_candidate_rubric(df_candidates: pd.DataFrame) -> pd.DataFrame:
    """Return a new DF with extra rubric columns appended."""
    results = df_candidates.apply(score_candidate_row, axis=1, result_type="expand")
    return pd.concat([df_candidates, results], axis=1)


def score_frame_row(row: pd.Series, df_candidates_by_ns_id: pd.DataFrame) -> dict[str, Any]:
    """Score one legal frame row based on the candidate sentence ns_id."""
    ns_id = _norm(row.get("ns_id", ""))
    cand_row = df_candidates_by_ns_id.get(ns_id)

    frame_type = _norm(row.get("frame_type", ""))
    subject_type = _norm(row.get("subject_type", "")).strip() or None
    action_predicate = _norm(row.get("action_predicate", "")).strip()
    condition_predicates = _norm(row.get("condition_predicates", "")).strip()
    required_documents = _norm(row.get("required_documents", "")).strip()
    recipient_authority = _norm(row.get("recipient_authority", "")).strip()
    deadline_value = _norm(row.get("deadline_value", "")).strip()

    # Defaults when candidate not found.
    sentence_text = ""
    time_span = None
    document_span = None
    authority_span = None
    candidate_rule_type = ""
    modality_span = ""
    if cand_row is not None:
        sentence_text = _norm(cand_row.get("sentence_text", ""))
        time_span = _norm(cand_row.get("time_span", "")).strip() or None
        document_span = _norm(cand_row.get("document_span", "")).strip() or None
        authority_span = _norm(cand_row.get("authority_span", "")).strip() or None
        candidate_rule_type = _norm(cand_row.get("candidate_rule_type", "")).strip()
        modality_span = _norm(cand_row.get("modality_span", "")).strip()

    # Determine modality label (permission/obligation/prohibition).
    modality_label = modality_label_from_candidate_row(
        pd.Series({"modality_span": modality_span, "sentence_text": sentence_text})
    )

    # Heuristics: subject
    wrong_subject = subject_type is None or subject_type == "" or subject_type == "unknown"
    # Penalize if action predicate looks like "Luật số..." (not a central action).
    lower_action = action_predicate.lower()
    wrong_action = bool(
        action_predicate
        and (
            "luật" in lower_action
            or "điều" in lower_action
            or lower_action.strip().startswith(("trường hợp", "trong thời hạn", "kể từ ngày"))
        )
    )

    # Frame type mismatch: use modality cues when available.
    wrong_frame_type = False
    if modality_label == "permission" and frame_type != "status_rule":
        # In this corpus, permission-like frames tend to map to status_rule.
        wrong_frame_type = True
    if modality_label in {"obligation", "prohibition"} and frame_type == "status_rule":
        wrong_frame_type = True
    if document_span and frame_type != "document_rule":
        wrong_frame_type = True

    # Condition too broad: if condition_predicates contain modal markers or are extremely long.
    condition_too_broad = False
    if condition_predicates:
        if len(condition_predicates) > 240:
            condition_too_broad = True
        if re.search(r"\b(phải|không được|được|có quyền|có thể)\b", condition_predicates, re.I | re.U):
            condition_too_broad = True

    # Deadline wrong: if deadline_value set but candidate has no time cue.
    deadline_wrong = False
    if deadline_value:
        if not time_span:
            deadline_wrong = True

    # Documents mixed: required_documents exist but candidate document_span missing or too long.
    documents_mixed = False
    if required_documents:
        if not document_span:
            documents_mixed = True
        if len(required_documents) > 320:
            documents_mixed = True
        if re.search(r"\bcơ quan\b", required_documents, re.I | re.U):
            documents_mixed = True

    # Authority missing: if candidate has authority cues but recipient_authority is empty.
    authority_missing = False
    if authority_span:
        if not recipient_authority:
            authority_missing = True

    # Exception / legal effect: keep mild.
    error_types: list[str] = []
    hard_error_types: list[str] = []

    if wrong_frame_type:
        error_types.append("wrong_frame_type")
        hard_error_types.append("wrong_frame_type")
    if wrong_subject:
        error_types.append("wrong_subject")
        hard_error_types.append("wrong_subject")
    if wrong_action:
        error_types.append("wrong_action")
        hard_error_types.append("wrong_action")
    if condition_too_broad:
        error_types.append("condition_too_broad")
        hard_error_types.append("condition_too_broad")

    if deadline_wrong:
        error_types.append("deadline_wrong")
    if documents_mixed:
        error_types.append("documents_mixed")
    if authority_missing:
        error_types.append("authority_missing")

    # Scoring (2/1/0).
    if hard_error_types:
        score = 0
        fix_needed = "redo_frame"
    elif any(t in error_types for t in ["deadline_wrong", "documents_mixed", "authority_missing"]):
        score = 1
        fix_needed = "fix_fields"
    else:
        score = 2
        fix_needed = "keep_for_rule_building"

    review_notes_parts: list[str] = []
    review_notes_parts.append(f"frame_type={frame_type}")
    review_notes_parts.append(f"subject_type={subject_type or ''}")
    review_notes_parts.append(f"action_predicate_len={len(action_predicate)}")
    if condition_predicates:
        review_notes_parts.append(f"cond_len={len(condition_predicates)}")
    if deadline_value:
        review_notes_parts.append(f"deadline_value={deadline_value}")
    if required_documents:
        review_notes_parts.append(f"docs_len={len(required_documents)}")
    if recipient_authority:
        review_notes_parts.append(f"authority_present")
    if error_types:
        review_notes_parts.append("errors=" + ",".join(error_types))

    return {
        "rubric_frame_score": score,
        "frame_error_type": ";".join(error_types) if error_types else None,
        "fix_needed": fix_needed,
        "review_notes": "; ".join(review_notes_parts),
    }


def apply_frame_rubric(df_frames: pd.DataFrame, df_candidates: pd.DataFrame) -> pd.DataFrame:
    """Return frames DF with rubric_frame_score + error columns appended."""
    # Build a lookup map ns_id -> row dict.
    df_candidates_by_ns_id = {
        str(ns): row for ns, row in zip(df_candidates["ns_id"].astype(str), df_candidates.to_dict("records"))
    }

    results = df_frames.apply(lambda r: score_frame_row(r, df_candidates_by_ns_id), axis=1, result_type="expand")

    return pd.concat([df_frames, results], axis=1)

