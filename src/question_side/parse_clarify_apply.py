"""Apply user answers that resolve parse-time ambiguities."""

from __future__ import annotations

import re
from typing import Any

from schemas.session import SessionState


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
