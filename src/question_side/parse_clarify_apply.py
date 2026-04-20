"""Apply user answers that resolve parse-time ambiguities."""

from __future__ import annotations

from datetime import date, datetime
import re
from typing import Any

from schemas.session import SessionState


def _to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"1", "true", "yes", "y", "co", "có", "dung", "đúng"}:
            return True
        if v in {"0", "false", "no", "n", "khong", "không", "sai"}:
            return False
    return None


def _normalize_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    raw = value.strip().replace(" ", "")
    if not raw:
        return None
    if not re.fullmatch(r"[-+]?\d+(?:[.,]\d+)?", raw):
        return None
    try:
        return float(raw.replace(",", "."))
    except Exception:
        return None


def _normalize_text(value: Any) -> str | None:
    if isinstance(value, str):
        v = value.strip()
        return v or None
    return None


def _normalize_choice(value: Any, options: list[str]) -> str | None:
    txt = _normalize_text(value)
    if txt is None:
        return None
    if not options:
        return txt
    by_fold = {str(opt).strip().lower(): str(opt).strip() for opt in options if str(opt).strip()}
    return by_fold.get(txt.lower())


def _normalize_date_like(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    txt = _normalize_text(value)
    if txt is None:
        return None

    raw = txt.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
        return dt.isoformat()
    except Exception:
        pass

    m = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", txt)
    if m:
        dd, mm, yyyy = m.groups()
        try:
            return date(int(yyyy), int(mm), int(dd)).isoformat()
        except Exception:
            return None

    m = re.fullmatch(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", txt)
    if m:
        yyyy, mm, dd = m.groups()
        try:
            return date(int(yyyy), int(mm), int(dd)).isoformat()
        except Exception:
            return None

    return None


def _normalize_duration(value: Any) -> str | None:
    txt = _normalize_text(value)
    if txt is None:
        return None
    low = txt.lower()
    if re.fullmatch(r"p\d+[dymh]", low):
        return txt
    if re.fullmatch(r"\d+(?:[.,]\d+)?\s*(ngày|ngay|tháng|thang|năm|nam|day|days|month|months|year|years)", low):
        return txt
    if re.fullmatch(r"\d+(?:[.,]\d+)?\s*(working\s*days?|ngày\s*làm\s*việc|ngay\s*lam\s*viec)", low):
        return txt
    return None


def normalize_clarification_answers_with_diagnostics(
    answers: list[dict[str, Any]],
    clarification_questions: list[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Normalize clarification answers and return (valid_rows, invalid_rows)."""
    by_key = {str(q.get("fact_key") or ""): q for q in (clarification_questions or [])}
    normalized: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    for ans in answers:
        fk = str(ans.get("fact_key") or "").strip()
        if not fk:
            continue
        q = by_key.get(fk)
        if q is None:
            invalid.append(
                {
                    "fact_key": fk,
                    "source_fact_key": fk,
                    "expected_type": "unknown",
                    "error": "unknown_fact_key",
                    "value": ans.get("value"),
                }
            )
            continue

        expected = str(q.get("expected_type") or "").strip().lower()
        if not expected:
            expected = "short_text"
        value = ans.get("value")
        source_fk = str(q.get("source_fact_key") or fk).strip() or fk
        options = [str(x) for x in (q.get("options") or []) if str(x).strip()]

        norm: Any = None
        if expected == "yes_no":
            norm = _to_bool(value)
        elif expected == "number":
            norm = _normalize_number(value)
        elif expected == "choice":
            norm = _normalize_choice(value, options)
        elif expected in {"text", "document", "short_text", "time"}:
            norm = _normalize_text(value)
        elif expected == "date":
            norm = _normalize_date_like(value)
        elif expected == "duration":
            norm = _normalize_duration(value)
        else:
            norm = _normalize_text(value)

        if norm is None:
            invalid.append(
                {
                    "fact_key": fk,
                    "source_fact_key": source_fk,
                    "expected_type": expected,
                    "error": "invalid_type",
                    "value": value,
                    "options": options,
                }
            )
            continue

        normalized.append({"fact_key": source_fk, "value": norm})
    return normalized, invalid


def normalize_clarification_answers(
    answers: list[dict[str, Any]],
    clarification_questions: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Map user clarification to normalized fact values by expected answer type."""
    out, _invalid = normalize_clarification_answers_with_diagnostics(answers, clarification_questions)
    return out


def known_facts_for_reasoning(session: SessionState) -> dict[str, Any]:
    """Strip parse_amb:* keys so backward/forward do not treat them as domain facts."""
    return {k: v for k, v in session.known_facts.items() if not str(k).startswith("parse_amb:")}


def structured_facts_for_reasoning(session: SessionState) -> dict[str, dict[str, Any]]:
    """Structured facts (bridge/user/derived) for logic-layer matching — Chặng A."""
    return dict(session.structured_facts or {})


def extract_resolved_condition_atoms_from_known_facts(known_facts: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for k, v in known_facts.items():
        if not str(k).startswith("parse_amb:"):
            continue
        if isinstance(v, str) and "(" in v:
            out.append(v.strip())
    return out


def extract_forced_atoms_from_answers(answers: list[dict[str, Any]]) -> list[str]:
    """fact_key format: parse_amb:<type>:<idx> ; value = chosen atom string."""
    out: list[str] = []
    for a in answers:
        fk = str(a.get("fact_key") or "")
        if not fk.startswith("parse_amb:"):
            continue
        v = a.get("value")
        if isinstance(v, str) and v.strip():
            out.append(v.strip())
        elif v is True and fk:
            # allow fact_key carrying atom in suffix parse_amb:...:atom(...)
            m = re.search(r"(?:change_|stated_)[a-z_]+\([^)]+\)", fk)
            if m:
                out.append(m.group(0))
    return out


def apply_forced_atoms_to_session(session: SessionState, forced: list[str]) -> None:
    if not forced or not session.layer2:
        return
    d = dict(session.layer2.diagnostics or {})
    d["forced_condition_atoms"] = forced
    session.layer2 = session.layer2.model_copy(update={"diagnostics": d})


def strip_parse_ambiguity_fact_keys(session: SessionState) -> None:
    """Remove parse_amb:* keys from known_facts after resolution (optional cleanup)."""
    if not session.known_facts:
        return
    keys = [k for k in session.known_facts if str(k).startswith("parse_amb:")]
    for k in keys:
        session.known_facts.pop(k, None)
