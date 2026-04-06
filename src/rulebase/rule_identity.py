"""Canonical rule identity for safe dedupe across domains (phase 3)."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from schemas.rule import RuleRecord
from schemas.rule_metadata import get_normalized_meta, meta_for_proof_and_trace

logger = logging.getLogger(__name__)


def global_rule_key(rule: RuleRecord) -> str:
    """
    Stable key: domain + rulebase_id + source_doc + source_article + local rule_id.

    Falls back to hashed blob if metadata incomplete.
    """
    m = meta_for_proof_and_trace(rule)
    dom = str(m.get("domain") or "")
    rb = str(m.get("rulebase_id") or "")
    sd = str(m.get("source_doc") or "")
    sa = str(m.get("source_article") or "")
    rid = str(rule.rule_id or "")
    raw = f"{dom}|{rb}|{sd}|{sa}|{rid}"
    if not sd and not sa:
        nm = get_normalized_meta(rule)
        if nm and (nm.source_doc or nm.source_article):
            raw = f"{dom}|{rb}|{nm.source_doc}|{nm.source_article}|{rid}"
    key = raw
    if len(key) > 512:
        key = hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:40]
    return key


def warn_on_rule_id_collision(rule_a: RuleRecord, rule_b: RuleRecord) -> None:
    if rule_a.rule_id == rule_b.rule_id and global_rule_key(rule_a) != global_rule_key(rule_b):
        logger.warning(
            "[rule_identity] same rule_id %r but different global keys — domains %s vs %s",
            rule_a.rule_id,
            meta_for_proof_and_trace(rule_a).get("domain"),
            meta_for_proof_and_trace(rule_b).get("domain"),
        )
