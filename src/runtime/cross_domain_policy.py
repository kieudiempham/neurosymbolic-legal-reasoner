"""Cross-domain jump policy for multi-rulebase reasoning (phase 2)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from schemas.rule import RuleRecord
from schemas.rule_metadata import get_normalized_meta

logger = logging.getLogger(__name__)


@dataclass
class CrossDomainPolicy:
    allow_shared_to_domain: bool = True
    allow_primary_to_secondary: bool = False
    require_bridge_for_secondary_jump: bool = True
    max_cross_domain_hops: int = 1

    def to_trace_dict(self) -> dict[str, Any]:
        return {
            "allow_shared_to_domain": self.allow_shared_to_domain,
            "allow_primary_to_secondary": self.allow_primary_to_secondary,
            "require_bridge_for_secondary_jump": self.require_bridge_for_secondary_jump,
            "max_cross_domain_hops": self.max_cross_domain_hops,
        }


def _rule_domain(rule: RuleRecord) -> str:
    m = get_normalized_meta(rule)
    if m:
        return m.domain
    md = rule.metadata or {}
    return str(md.get("domain") or "enterprise")


def _rule_layer(rule: RuleRecord) -> str:
    m = get_normalized_meta(rule)
    if m:
        return m.layer
    md = rule.metadata or {}
    return str(md.get("layer") or "domain")


def filter_ranked_for_primary_phase(
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    *,
    primary_domains: list[str],
    include_shared: bool,
) -> tuple[list[tuple[RuleRecord, float, dict[str, Any]]], list[dict[str, Any]]]:
    """
    Keep only rules whose domain/layer is in primary domains or shared layer (if allowed).
    Returns (filtered, rejected_records for trace).
    """
    pset = set(primary_domains)
    out: list[tuple[RuleRecord, float, dict[str, Any]]] = []
    rejected: list[dict[str, Any]] = []
    for r, s, d in ranked:
        scope = str(d.get("retrieval_scope") or "")
        dom = _rule_domain(r)
        layer = _rule_layer(r)
        ok = False
        if include_shared and (layer == "shared" or scope == "shared" or dom == "shared"):
            ok = True
        elif dom in pset:
            ok = True
        elif scope and scope in pset:
            ok = True
        if ok:
            out.append((r, s, d))
        else:
            rejected.append(
                {
                    "rule_id": r.rule_id,
                    "reason": "domain_not_in_primary_phase",
                    "domain": dom,
                    "retrieval_scope": scope,
                }
            )
    return out, rejected


def merge_secondary_with_policy(
    primary_ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    full_ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    *,
    secondary_domains: list[str],
    policy: CrossDomainPolicy,
    triggered_bridges: list[str],
) -> tuple[list[tuple[RuleRecord, float, dict[str, Any]]], bool, list[str]]:
    """
    If policy allows, append secondary-domain candidates not already in primary list.
    Secondary jump requires bridge when ``require_bridge_for_secondary_jump`` unless no bridges configured.
    """
    if not secondary_domains or not policy.allow_primary_to_secondary:
        return primary_ranked, False, []

    need_bridge = policy.require_bridge_for_secondary_jump
    if need_bridge and not triggered_bridges:
        logger.info(
            "[cross_domain] secondary domains %s skipped: no triggered bridge",
            secondary_domains,
        )
        return primary_ranked, False, []

    seen = {r.rule_id for r, _, _ in primary_ranked}
    extra: list[tuple[RuleRecord, float, dict[str, Any]]] = []
    used_dom: list[str] = []
    sset = set(secondary_domains)
    for r, s, d in full_ranked:
        if r.rule_id in seen:
            continue
        dom = _rule_domain(r)
        if dom in sset:
            d2 = dict(d)
            d2["cross_domain_expansion"] = True
            d2["jump_from_policy"] = "secondary_allowed"
            extra.append((r, s, d2))
            seen.add(r.rule_id)
            if dom not in used_dom:
                used_dom.append(dom)
    merged = primary_ranked + extra
    return merged, bool(extra), used_dom


def default_policy_for_routing(
    *,
    allow_cross_domain_expansion: bool,
    triggered_bridges: list[str],
) -> CrossDomainPolicy:
    return CrossDomainPolicy(
        allow_shared_to_domain=True,
        allow_primary_to_secondary=allow_cross_domain_expansion,
        require_bridge_for_secondary_jump=True,
        max_cross_domain_hops=1 if allow_cross_domain_expansion else 0,
    )
