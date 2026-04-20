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
    actor_entity_id: str = "unknown_subject_x"
    actor_role: str = "unknown"
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
    hits = sum(1 for t in toks if re.search(rf"\b{re.escape(t)}\b", b))
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


_ROLE_ALLOWED_DOMAINS: dict[str, set[str]] = {
    "employee": {"labor", "procedure", "deadline", "exception", "legal_effect", ""},
    "employer": {"labor", "procedure", "deadline", "exception", "legal_effect", ""},
    "labor_leasing_enterprise": {"labor", "procedure", "deadline", "exception", "legal_effect", ""},
    "taxpayer": {"tax", "procedure", "deadline", "legal_effect", ""},
    "business_household": {"registration", "tax", "procedure", "deadline", "legal_effect", ""},
}

_SUBJECT_ROLE_ALIASES: dict[str, str] = {
    "company": "unknown",
    "individual": "unknown",
    "authority": "unknown",
    "employee": "employee",
    "employer": "employer",
    "taxpayer": "taxpayer",
    "business_household": "business_household",
}

_DOMAIN_GROUPS: dict[str, str] = {
    "enterprise": "enterprise",
    "enterprise_registration": "enterprise",
    "registration": "registration",
    "corporate": "enterprise",
    "corporate_governance": "enterprise",
    "tax": "tax",
    "labor": "labor",
    "procedure": "procedure",
    "authority": "procedure",
    "deadline": "deadline",
    "exception": "exception",
    "legal_effect": "legal_effect",
}

_FOCUS_TO_FAMILY: dict[str, str] = {
    "deadline": "deadline",
    "threshold": "threshold",
    "exception": "exception",
    "legal_effect": "legal_effect_trigger",
    "legal_consequence": "legal_effect_trigger",
    "obligation": "obligation_trigger",
    "prohibition": "prohibition_trigger",
    "permission": "applicability",
    "applicability": "applicability",
    "procedure": "applicability",
    "dossier": "applicability",
    "authority": "applicability",
}

_FAMILY_BUCKETS: tuple[str, ...] = (
    "applicability",
    "threshold",
    "deadline",
    "exception",
    "eligibility",
    "obligation_trigger",
    "prohibition_trigger",
    "legal_effect_trigger",
)

_PREDICATE_FAMILY_EXPLICIT: dict[str, str] = {
    "truong_hop_ngoai_le": "exception",
    "qua_thoi_han": "deadline",
    "trong_thoi_han": "deadline",
    "dang_ky_thay_doi_trong_thoi_han": "deadline",
    "xu_phat_hanh_chinh": "legal_effect_trigger",
    "tu_choi_ho_so": "legal_effect_trigger",
    "phat_sinh_nghia_vu": "obligation_trigger",
}

_DOMAIN_FAMILY_EXPLICIT: dict[str, str] = {
    "exception": "exception",
    "deadline": "deadline",
    "legal_effect": "legal_effect_trigger",
}

_FAMILY_SIGNAL_PATTERNS: dict[str, tuple[str, ...]] = {
    "exception": ("ngoai le", "tru truong hop", "mien tru"),
    "deadline": ("thoi han", "qua han", "dung han", "trong vong", "cham nhat"),
    "threshold": ("tu bao nhieu", "it nhat", "toi thieu", "muc", "nguong", "%", "phan tram"),
    "eligibility": (
        "du dieu kien",
        "dieu kien",
        "duoc khau tru",
        "khau tru thue",
        "duoc huong",
        "ap dung doi voi",
    ),
    "obligation_trigger": ("phat sinh nghia vu", "phai", "bat buoc", "co nghia vu"),
    "prohibition_trigger": ("khong duoc", "bi cam", "cam", "khong cho phep"),
    "legal_effect_trigger": ("xu phat", "che tai", "hau qua", "tu choi", "vo hieu"),
    "applicability": ("truong hop", "ap dung", "khi", "neu", "doi voi"),
}


def _norm_key(s: str | None) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", lower_fold((s or "").strip())).strip("_")


def _coarse_domain(domain: str) -> str:
    d = _norm_key(domain)
    return _DOMAIN_GROUPS.get(d, d)


def _candidate_family(entry: dict[str, Any]) -> str:
    pred = _norm_key(str(entry.get("canonical_predicate") or ""))
    domain = _coarse_domain(str(entry.get("domain") or ""))

    # Strongest signal: explicit predicate mapping.
    if pred in _PREDICATE_FAMILY_EXPLICIT:
        return _PREDICATE_FAMILY_EXPLICIT[pred]

    # Next: explicit domain-level families.
    if domain in _DOMAIN_FAMILY_EXPLICIT:
        return _DOMAIN_FAMILY_EXPLICIT[domain]

    # Entry-wide signal (predicate + trigger_patterns + synonyms + domain text).
    text_parts = [pred, domain]
    text_parts.extend(lower_fold(str(x)) for x in (entry.get("trigger_patterns") or []))
    text_parts.extend(lower_fold(str(x)) for x in (entry.get("synonyms") or []))
    signal_text = " ".join(p for p in text_parts if p).strip()

    votes: dict[str, float] = {fam: 0.0 for fam in _FAMILY_BUCKETS}

    # Domain prior for unresolved families.
    if domain in ("procedure", "registration", "enterprise", "tax", "labor"):
        votes["applicability"] += 0.7

    for family, cues in _FAMILY_SIGNAL_PATTERNS.items():
        for cue in cues:
            if cue and cue in signal_text:
                votes[family] += 1.0

    # Predicate-token cues remain useful, but weaker than explicit mapping.
    if "dieu_kien" in pred:
        votes["eligibility"] += 0.8
    if "cam" in pred:
        votes["prohibition_trigger"] += 0.8
    if "nghia_vu" in pred:
        votes["obligation_trigger"] += 0.8
    if "thoi_han" in pred:
        votes["deadline"] += 0.8
    if "ngoai_le" in pred:
        votes["exception"] += 0.8

    winner = max(votes.items(), key=lambda kv: kv[1])
    if winner[1] >= 1.0:
        return winner[0]

    # Weak fallback only when no strong signal exists.
    if domain in ("corporate", "corporate_governance", "enterprise", "registration", "procedure", "tax", "labor"):
        return "applicability"
    return "applicability"


def _hinted_family(question_focus: str | None, condition_family_hint: str | None) -> str | None:
    fam = _norm_key(condition_family_hint)
    if fam and fam != "unknown":
        return fam
    qf = _norm_key(question_focus)
    if not qf or qf == "unknown":
        return None
    return _FOCUS_TO_FAMILY.get(qf)


def _entry_pattern_blob(entry: dict[str, Any]) -> str:
    parts: list[str] = []
    parts.extend(str(x) for x in (entry.get("trigger_patterns") or []))
    parts.extend(str(x) for x in (entry.get("synonyms") or []))
    parts.append(str(entry.get("canonical_predicate") or ""))
    return lower_fold(" ".join(parts))


def _action_consistency_score(action_text: str | None, entry: dict[str, Any]) -> float:
    act = lower_fold((action_text or "").strip())
    if not act:
        return 0.0
    toks = [t for t in re.split(r"\W+", act) if len(t) > 2]
    if not toks:
        return 0.0
    hay = _entry_pattern_blob(entry)
    hits = sum(1 for t in toks if re.search(rf"\b{re.escape(t)}\b", hay))
    ratio = hits / len(toks)
    if ratio >= 0.5:
        return 0.12
    if ratio >= 0.25:
        return 0.06
    return -0.04


def _domain_score(entry: dict[str, Any], domain_hint: str | None) -> float:
    hint = _coarse_domain(domain_hint or "")
    if not hint or hint == "unknown":
        return 0.0
    cand = _coarse_domain(str(entry.get("domain") or ""))
    if not cand:
        return 0.0
    if hint == cand:
        return 0.14
    return -0.18


def _family_score(entry: dict[str, Any], expected_family: str | None) -> tuple[float, bool]:
    if not expected_family or expected_family == "unknown":
        return 0.0, False
    fam = _candidate_family(entry)
    if fam == expected_family:
        return 0.16, False
    # Keep threshold neutral for now because lexicon coverage for threshold is sparse.
    if expected_family == "threshold":
        return -0.04, True
    return -0.2, True


def _rerank_score(
    *,
    raw: float,
    entry: dict[str, Any],
    max_nongeneric: float,
    actor_role: str,
    action_text: str | None,
    domain_hint: str | None,
    expected_family: str | None,
) -> tuple[float, dict[str, Any]]:
    role_ok = _domain_is_compatible(actor_role, str(entry.get("domain") or ""))
    role_score = 0.05 if role_ok else -0.12
    dom_score = _domain_score(entry, domain_hint)
    fam_score, fam_mismatch = _family_score(entry, expected_family)
    act_score = _action_consistency_score(action_text, entry)

    score = _effective_rank_score(raw, entry, max_nongeneric) + role_score + dom_score + fam_score + act_score

    # Penalize lexical distractors: high lexical overlap but semantically off-family/domain.
    off_domain = dom_score < 0
    if raw >= 0.6 and (off_domain or fam_mismatch):
        score -= 0.18

    meta = {
        "role_ok": role_ok,
        "off_domain": off_domain,
        "family_mismatch": fam_mismatch,
        "candidate_family": _candidate_family(entry),
    }
    return score, meta


def _is_usable_candidate(raw: float, rerank: float, meta: dict[str, Any]) -> bool:
    if bool(meta.get("family_mismatch")) and rerank < 0.62:
        return False
    if bool(meta.get("off_domain")) and rerank < 0.64:
        return False
    if rerank >= 0.48:
        return True
    if raw >= 0.58 and not bool(meta.get("off_domain")) and not bool(meta.get("family_mismatch")):
        return True
    if raw >= 0.5 and rerank >= 0.42 and not bool(meta.get("family_mismatch")):
        return True
    return False


def _domain_is_compatible(actor_role: str, entry_domain: str) -> bool:
    allowed = _ROLE_ALLOWED_DOMAINS.get((actor_role or "").strip().lower())
    if not allowed:
        return True
    if entry_domain in allowed:
        return True
    entry_coarse = _coarse_domain(entry_domain)
    allowed_coarse = {_coarse_domain(x) for x in allowed}
    return entry_coarse in allowed_coarse


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
    question_focus: str | None = None,
    action_text: str | None = None,
    subject_type: str | None = None,
    domain_hint: str | None = None,
    condition_family_hint: str | None = None,
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

    normalized_role = _norm_key(actor_role)
    normalized_subject_type = _norm_key(subject_type)
    if normalized_subject_type in _SUBJECT_ROLE_ALIASES and normalized_role in ("", "unknown"):
        normalized_role = _SUBJECT_ROLE_ALIASES[normalized_subject_type]

    expected_family = _hinted_family(question_focus, condition_family_hint)

    candidates: list[tuple[float, float, dict[str, Any], dict[str, Any]]] = []
    for e in ENTRIES:
        raw = _entry_raw_score(blob, e)
        if raw > 0:
            domain = str(e.get("domain") or "")
            if not _domain_is_compatible(normalized_role or actor_role, domain):
                # Only allow strong exact phrase matches to bypass role-domain guard.
                if raw < 0.86:
                    continue
            candidates.append((raw, 0.0, e, {}))

    max_nongeneric = max((r for r, _, ee, _ in candidates if not ee.get("generic")), default=0.0)
    reranked: list[tuple[float, float, dict[str, Any], dict[str, Any]]] = []
    for raw, _, entry, _ in candidates:
        rr, meta = _rerank_score(
            raw=raw,
            entry=entry,
            max_nongeneric=max_nongeneric,
            actor_role=normalized_role or actor_role,
            action_text=action_text,
            domain_hint=domain_hint,
            expected_family=expected_family,
        )
        reranked.append((raw, rr, entry, meta))
    reranked.sort(key=lambda t: (-t[1], -t[0]))

    top_e = reranked[0][2] if reranked else None
    top_raw = reranked[0][0] if reranked else 0.0
    top_rr = reranked[0][1] if reranked else 0.0
    top_meta = reranked[0][3] if reranked else {}
    second_rr = reranked[1][1] if len(reranked) > 1 else 0.0
    rr_gap = top_rr - second_rr if len(reranked) > 1 else 1.0

    pred = top_e["canonical_predicate"] if top_e else "stated_condition"
    primary = (
        f"{pred}({actor_entity_id})"
        if pred != "stated_condition"
        else f"stated_condition({slug_token(blob)[:48] or 'cond'})"
    )

    alts: list[str] = []
    amb_reason = ""
    conf = max(0.45, min(0.94, top_rr if top_rr > 0 else top_raw)) if top_e else 0.45

    if len(reranked) > 1 and rr_gap < 0.1 and second_rr > 0.38 and top_e:
        p2 = reranked[1][2]["canonical_predicate"]
        p2_meta = reranked[1][3]
        # Avoid promoting off-family/domain distractors as strong alternatives.
        if p2 != pred and not p2_meta.get("off_domain") and not p2_meta.get("family_mismatch"):
            alts.append(f"{p2}({actor_entity_id})")
            conf = min(conf, 0.72)
            amb_reason = "close_contextual_alternatives"

    # Keep diagnostics: include one weak alternative when available, even if not close.
    if not alts and len(reranked) > 1:
        p2 = reranked[1][2]["canonical_predicate"]
        p2_meta = reranked[1][3]
        if (
            p2 != pred
            and reranked[1][0] >= 0.55
            and reranked[1][1] >= 0.46
            and not p2_meta.get("off_domain")
            and not p2_meta.get("family_mismatch")
        ):
            alts.append(f"{p2}({actor_entity_id})")

    usable_top = bool(top_e) and _is_usable_candidate(top_raw, top_rr, top_meta)

    if not usable_top:
        if (
            top_e
            and str(top_e.get("canonical_predicate") or "") not in ("", "stated_condition")
            and not bool(top_meta.get("off_domain"))
            and not bool(top_meta.get("family_mismatch"))
            and top_raw >= 0.78
            and top_rr >= 0.52
        ):
            alt = f"{str(top_e.get('canonical_predicate'))}({actor_entity_id})"
            if alt not in alts:
                alts.append(alt)
        primary = f"stated_condition({slug_token(blob)[:56] or 'cond'})"
        pred = "stated_condition"
        conf = 0.42 if top_raw < 0.45 else 0.5
        amb_reason = amb_reason or "no_usable_contextual_match"
    else:
        # Prefer best-effort canonical candidate over generic fallback when semantically usable.
        conf = max(conf, 0.6 if top_raw >= 0.45 else 0.56)

    if rr_gap < 0.06 and len(reranked) > 1 and second_rr > 0.35:
        amb_reason = amb_reason or "contextual_score_tie"

    # Soften ambiguity in cases where the best candidate is usable and alternatives are weaker/off-family.
    if usable_top and amb_reason and rr_gap >= 0.08:
        amb_reason = ""

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
