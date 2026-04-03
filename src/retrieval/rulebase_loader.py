"""Load curated rulebase from rulebase_reasoning_core.json and build indexes."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from schemas.rule import RuleHead, RuleRecord

logger = logging.getLogger(__name__)

_configured_core_path: Path | None = None
_index: RulebaseIndex | None = None


class RulebaseIndex:
    def __init__(self, rules: list[RuleRecord]) -> None:
        self.rules = rules
        self.by_id: dict[str, RuleRecord] = {r.rule_id: r for r in rules}
        self.by_logic_form: dict[str, list[RuleRecord]] = {}
        self.by_head_predicate: dict[str, list[RuleRecord]] = {}
        self.by_action_atom: dict[str, list[RuleRecord]] = {}
        self.by_source_ref: dict[str, list[RuleRecord]] = {}

        for r in rules:
            lf = r.logic_form
            self.by_logic_form.setdefault(lf, []).append(r)
            hp = r.head.predicate
            self.by_head_predicate.setdefault(hp, []).append(r)
            prov = r.metadata.get("provenance") or {}
            sr = prov.get("source_ref")
            if isinstance(sr, str) and sr:
                self.by_source_ref.setdefault(sr, []).append(r)
            if r.head.predicate in ("obligation", "permission", "prohibition") and len(r.head.args) >= 2:
                act = str(r.head.args[1])
                self.by_action_atom.setdefault(act, []).append(r)

    def all(self) -> list[RuleRecord]:
        return list(self.rules)


def configure_rulebase_path(path: Path | None) -> None:
    """Set default path for get_rulebase_index / load_rulebase. Clears cache."""
    global _configured_core_path, _index
    _configured_core_path = path
    _index = None


def _parse_rule(obj: dict[str, Any]) -> RuleRecord | None:
    try:
        head = obj.get("head") or {}
        return RuleRecord(
            rule_id=str(obj["rule_id"]),
            logic_form=str(obj.get("logic_form") or "unknown"),
            head=RuleHead(
                predicate=str(head.get("predicate") or "unknown"),
                args=list(head.get("args") or []),
            ),
            body=list(obj.get("body") or []),
            metadata=dict(obj.get("metadata") or {}),
            selected_for_reasoning=obj.get("selected_for_reasoning"),
            auxiliary_clauses=list(obj.get("auxiliary_clauses") or []),
        )
    except (KeyError, TypeError, ValidationError) as e:
        logger.warning("skip malformed rule: %s", e)
        return None


def load_rulebase(path: Path | None = None) -> RulebaseIndex:
    p = path or _configured_core_path
    if p is None:
        logger.error("rulebase path not configured; call configure_rulebase_path()")
        return RulebaseIndex([])
    if not p.exists():
        logger.error("rulebase not found: %s", p)
        return RulebaseIndex([])
    data = json.loads(p.read_text(encoding="utf-8"))
    raw_rules = data.get("rules_reasoning_core") or data.get("rules") or []
    out: list[RuleRecord] = []
    for row in raw_rules:
        if not isinstance(row, dict):
            continue
        r = _parse_rule(row)
        if r:
            out.append(r)
    logger.info("loaded %s rules from %s", len(out), p)
    return RulebaseIndex(out)


def get_rulebase_index() -> RulebaseIndex:
    global _index
    if _index is None:
        _index = load_rulebase()
    return _index


def reset_rulebase_cache() -> None:
    global _index
    _index = None
