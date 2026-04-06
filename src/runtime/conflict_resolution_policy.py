"""Basic legal-style conflict pruning between candidate rules (phase 3)."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from schemas.rule import RuleRecord
from rulebase.rule_identity import global_rule_key

logger = logging.getLogger(__name__)


def _priority_specificity(rule: RuleRecord) -> tuple[int, float]:
    md = rule.metadata or {}
    mr = md.get("mr_v1") if isinstance(md.get("mr_v1"), dict) else {}
    pr = int(mr.get("priority_level") or md.get("priority_level") or 0)
    sp = float(mr.get("specificity_score") or md.get("specificity_score") or min(2.0, 0.15 + len(rule.body) * 0.03))
    return pr, sp


def _exception_override_bonus(rule: RuleRecord, bucket_rules: list[RuleRecord]) -> tuple[int, int]:
    """(exception_bonus, override_bonus) — higher wins."""
    md = rule.metadata or {}
    mr = md.get("mr_v1") if isinstance(md.get("mr_v1"), dict) else {}
    other_ids = {x.rule_id for x in bucket_rules}
    ex_of = mr.get("exception_of") or md.get("exception_of")
    exc_bonus = 1 if ex_of and str(ex_of) in other_ids else 0
    ovr = mr.get("overrides") or md.get("overrides") or []
    if not isinstance(ovr, list):
        ovr = [ovr] if ovr else []
    ov_bonus = 1 if any(str(x) in other_ids for x in ovr) else 0
    return exc_bonus, ov_bonus


def head_bucket(rule: RuleRecord) -> tuple[Any, ...]:
    """Bucket by full head shape — predicate + arity + args (not only predicate/arity)."""
    a = rule.head.args or []
    return (str(rule.head.predicate), len(a), tuple(str(x) for x in a))


def prune_conflicting_candidates(
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
) -> tuple[list[tuple[RuleRecord, float, dict[str, Any]]], list[dict[str, Any]]]:
    """
    Within each head-bucket, keep the best rule by (priority, specificity, retrieval score).
    """
    buckets: dict[tuple[Any, ...], list[tuple[RuleRecord, float, dict[str, Any]]]] = defaultdict(list)
    for r, s, d in ranked:
        buckets[head_bucket(r)].append((r, s, dict(d)))

    kept: list[tuple[RuleRecord, float, dict[str, Any]]] = []
    rejected: list[dict[str, Any]] = []

    for _bk, items in buckets.items():
        if len(items) == 1:
            r, s, d = items[0]
            d2 = dict(d)
            d2["conflict_resolution"] = {"status": "unique_in_bucket"}
            kept.append((r, s, d2))
            continue
        brules = [x[0] for x in items]
        scored: list[tuple[RuleRecord, float, dict[str, Any], int, int, int, float, float]] = []
        for r, s, d in items:
            pr, sp = _priority_specificity(r)
            eb, ob = _exception_override_bonus(r, brules)
            scored.append((r, s, d, eb, ob, pr, sp))
        scored.sort(key=lambda x: (-x[3], -x[4], -x[5], -x[6], -x[1]))
        win = scored[0]
        r_w, s_w, d_w, eb_w, ob_w, pr_w, sp_w = win
        d_out = dict(d_w)
        d_out["conflict_resolution"] = {
            "status": "winner",
            "priority": pr_w,
            "specificity": sp_w,
            "exception_bonus": eb_w,
            "override_bonus": ob_w,
        }
        kept.append((r_w, s_w, d_out))
        for loser in scored[1:]:
            r_l, s_l, d_l, eb_l, ob_l, pr_l, sp_l = loser
            rejected.append(
                {
                    "rule_id": r_l.rule_id,
                    "global_key": global_rule_key(r_l),
                    "reason": "conflict_lower_rank",
                    "winner_rule_id": r_w.rule_id,
                    "winner_global_key": global_rule_key(r_w),
                    "detail": {
                        "priority": pr_l,
                        "specificity": sp_l,
                        "winner_priority": pr_w,
                        "exception_bonus": eb_l,
                        "override_bonus": ob_l,
                    },
                }
            )
            logger.info(
                "[conflict] dropped %s in favor of %s (priority %s vs %s)",
                r_l.rule_id,
                r_w.rule_id,
                pr_l,
                pr_w,
            )

    kept.sort(key=lambda x: -x[1])
    return kept, rejected
