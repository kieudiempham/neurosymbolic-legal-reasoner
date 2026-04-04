"""Condition text -> structured frame -> canonical atoms (+ alternatives, confidence)."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from question_side.condition_lexicon import ENTRIES
from utils.text import lower_fold, slug_token


class ConditionFrame(BaseModel):
    """Intermediate representation before atoms."""

    event_type: str = "unknown"
    actor_entity_id: str = "company_x"
    actor_role: str = "company"
    time_hint: str | None = None
    exception_hint: str | None = None
    status: str = "hypothetical"
    source_text: str = ""


class ConditionNormalizeResult(BaseModel):
    frame: ConditionFrame
    primary_atom: str = ""
    alternative_atoms: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    canonical_predicate: str = ""
    domain: str = ""
    ambiguity_reason: str = ""


def _pattern_match_score(blob: str, pattern: str) -> float:
    """Score a single pattern against blob; rewards longer / full substring hits."""
    b = blob
    pl = lower_fold(pattern.strip())
    if len(pl) < 2:
        return 0.0
    if pl in b:
        return 0.72 + min(0.27, len(pl) / 120.0)
    toks = [t for t in pl.split() if len(t) > 2]
    hits = sum(1 for t in toks if t in b)
    if not toks:
        return 0.0
    ratio = hits / len(toks)
    # Partial token hits must not score like full phrase matches (avoid over-match).
    if ratio >= 0.85:
        return 0.42 + 0.12 * ratio
    if ratio >= 0.66:
        return 0.22 + 0.18 * ratio
    if ratio >= 0.34:
        return 0.12 + 0.12 * ratio
    return 0.0


def _entry_raw_score(blob: str, entry: dict[str, Any]) -> float:
    patterns: list[str] = []
    for p in entry.get("trigger_patterns") or []:
        patterns.append(p)
    for p in entry.get("synonyms") or []:
        patterns.append(p)
    best = 0.0
    for p in patterns:
        best = max(best, _pattern_match_score(blob, p))
    return best


def _effective_rank_score(raw: float, entry: dict[str, Any], max_nongeneric: float) -> float:
    pri = float(entry.get("priority", 5))
    eff = raw + pri / 1000.0
    if entry.get("generic") and max_nongeneric >= 0.58:
        eff *= 0.82
    return eff


def normalize_condition_text(
    condition_text: str,
    *,
    actor_entity_id: str,
    actor_role: str,
    assertion_status: str,
) -> ConditionNormalizeResult:
    """
    Map free condition text to canonical atoms; may return alternatives + confidence.
    """
    src = (condition_text or "").strip()
    if not src:
        return ConditionNormalizeResult(
            frame=ConditionFrame(
                actor_entity_id=actor_entity_id,
                actor_role=actor_role,
                status="asserted" if assertion_status in ("asserted", "factual") else "hypothetical",
                source_text="",
            ),
            primary_atom="",
            confidence=1.0,
        )

    blob = lower_fold(src)
    ast = assertion_status
    st = "asserted" if ast in ("asserted", "factual") else ("hypothetical" if ast == "hypothetical" else "ambiguous")

    candidates: list[tuple[float, dict[str, Any]]] = []
    for e in ENTRIES:
        raw = _entry_raw_score(blob, e)
        if raw > 0:
            candidates.append((raw, e))

    max_nongeneric = max((r for r, ee in candidates if not ee.get("generic")), default=0.0)
    candidates.sort(key=lambda t: -_effective_rank_score(t[0], t[1], max_nongeneric))

    top_e = candidates[0][1] if candidates else None
    top_raw = candidates[0][0] if candidates else 0.0
    second_raw = candidates[1][0] if len(candidates) > 1 else 0.0
    gap = top_raw - second_raw if len(candidates) > 1 else 1.0

    pred = top_e["canonical_predicate"] if top_e else "stated_condition"
    primary = (
        f"{pred}({actor_entity_id})"
        if pred != "stated_condition"
        else f"stated_condition({slug_token(blob)[:48] or 'cond'})"
    )

    alts: list[str] = []
    amb_reason = ""
    conf = top_raw if top_raw > 0 else 0.45

    if len(candidates) > 1 and gap < 0.12 and second_raw > 0.4 and top_e:
        p2 = candidates[1][1]["canonical_predicate"]
        if p2 != pred:
            alts.append(f"{p2}({actor_entity_id})")
            conf = min(conf, 0.68)
            amb_reason = "close_lexicon_alternatives"

    if top_raw < 0.5 or not top_e:
        primary = f"stated_condition({slug_token(blob)[:56] or 'cond'})"
        pred = "stated_condition"
        conf = 0.42
        amb_reason = amb_reason or "low_lexicon_match"

    if gap < 0.08 and len(candidates) > 1 and second_raw > 0.35:
        amb_reason = amb_reason or "score_tie"

    tm = re.search(
        r"(trong vòng|trong vo|thời hạn|thoi han|\d+\s*ngày)",
        blob,
        re.IGNORECASE,
    )
    exm = re.search(r"(trừ|ngoại trừ|ngoại lệ|tru truong hop)", blob, re.IGNORECASE)

    frame = ConditionFrame(
        event_type=pred,
        actor_entity_id=actor_entity_id,
        actor_role=actor_role,
        time_hint=tm.group(0) if tm else None,
        exception_hint=exm.group(0) if exm else None,
        status=st,
        source_text=src,
    )

    return ConditionNormalizeResult(
        frame=frame,
        primary_atom=primary,
        alternative_atoms=alts,
        confidence=round(min(1.0, max(0.0, conf)), 3),
        canonical_predicate=pred,
        domain=(top_e or {}).get("domain", "") if top_e else "",
        ambiguity_reason=amb_reason,
    )
