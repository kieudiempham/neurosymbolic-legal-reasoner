"""Basic temporal viability for rules at question time (phase 3)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from schemas.rule import RuleRecord
from schemas.rule_metadata import get_normalized_meta
from rulebase.rule_identity import global_rule_key

logger = logging.getLogger(__name__)


def resolve_question_time(
    explicit: str | None,
    *,
    trace: dict[str, Any] | None = None,
) -> datetime:
    """Use explicit ISO time, else UTC now; log default."""
    if explicit and str(explicit).strip():
        try:
            t = datetime.fromisoformat(str(explicit).replace("Z", "+00:00"))
            if trace is not None:
                trace["question_time_source"] = "request_or_context"
            return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
        except Exception:
            logger.warning("[temporal] bad question_time %r — using now", explicit)
    now = datetime.now(timezone.utc)
    if trace is not None:
        trace["question_time_source"] = "default_system_now_utc"
        trace["question_time_default_note"] = "no_valid_question_time"
    return now


def _parse_dt(s: str | None) -> datetime | None:
    if not s or not str(s).strip():
        return None
    try:
        t = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def rule_temporally_valid(rule: RuleRecord, at: datetime) -> tuple[bool, str | None]:
    """Return (ok, fail_reason)."""
    m = get_normalized_meta(rule)
    if not m:
        return True, None
    ef = _parse_dt(m.effective_from)
    et = _parse_dt(m.effective_to) if m.effective_to else None
    if ef and at < ef:
        return False, "not_yet_effective"
    if et and at > et:
        return False, "expired"
    return True, None


def filter_ranked_by_temporal(
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    at: datetime,
) -> tuple[list[tuple[RuleRecord, float, dict[str, Any]]], list[dict[str, Any]]]:
    kept: list[tuple[RuleRecord, float, dict[str, Any]]] = []
    rejected: list[dict[str, Any]] = []
    for r, s, d in ranked:
        ok, reason = rule_temporally_valid(r, at)
        d2 = dict(d)
        d2["temporal_check"] = {"ok": ok, "reason": reason}
        if ok:
            kept.append((r, s, d2))
        else:
            rejected.append(
                {
                    "rule_id": r.rule_id,
                    "global_key": global_rule_key(r),
                    "reason": reason or "temporal_fail",
                }
            )
    return kept, rejected


def temporal_snapshot_for_proof(at: datetime) -> dict[str, Any]:
    return {"question_time_utc": at.isoformat(), "policy": "effective_window_v1"}
