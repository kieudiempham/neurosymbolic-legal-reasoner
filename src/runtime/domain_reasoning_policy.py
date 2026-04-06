"""Domain reasoning policy — centralizes allows_rule / allows_fact / allows_unification (Chặng A)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from schemas.rule import RuleRecord
from schemas.structured_fact import StructuredFact
from runtime.cross_domain_policy import CrossDomainPolicy, _rule_domain, _rule_layer


@dataclass
class DomainReasoningPolicy:
    """Wraps CrossDomainPolicy with explicit logic-layer decisions + debug reasons."""

    cross_domain_policy: CrossDomainPolicy

    def allows_rule(self, rule: RuleRecord, context: Any) -> tuple[bool, str | None]:
        """Whether this rule may be applied given active domains / bridges / shared."""
        ok, reason = self._domain_gate(rule, context)
        if not ok:
            return False, reason
        if bool(getattr(context, "strict_domain_enforcement", False)):
            rbs = list(getattr(context, "active_rulebases", None) or [])
            if rbs:
                md = rule.metadata or {}
                mr = md.get("mr_v1") if isinstance(md.get("mr_v1"), dict) else {}
                rb = str(mr.get("rulebase_id") or md.get("rulebase_id") or "")
                if rb and rb not in rbs:
                    return False, "rule_rejected_rulebase_not_active"
        return True, None

    def allows_unification(self, rule: RuleRecord, context: Any) -> tuple[bool, str | None]:
        """Alias for apply-time check (head unification uses same gate as full rule apply)."""
        return self.allows_rule(rule, context)

    def allows_fact(self, fact: StructuredFact, context: Any) -> tuple[bool, str | None]:
        """Bridge/shared facts may satisfy atoms only when policy permits."""
        dom = (fact.fact_domain or "").strip()
        origin = fact.fact_origin
        primary = set(getattr(context, "primary_domains", None) or [])
        secondary = set(getattr(context, "secondary_domains", None) or [])
        bridges = list(getattr(context, "triggered_bridges", None) or [])
        inc = bool(getattr(context, "include_shared", True))

        if origin == "bridge" or dom == "shared":
            if not inc:
                return False, "fact_rejected_shared_disabled"
            return True, None
        if dom in primary:
            return True, None
        if dom in secondary:
            if not self.cross_domain_policy.allow_primary_to_secondary:
                return False, "fact_rejected_secondary_not_allowed"
            if self.cross_domain_policy.require_bridge_for_secondary_jump and not bridges:
                return False, "fact_rejected_secondary_requires_bridge"
            return True, None
        if not dom:
            return True, None
        return False, "fact_rejected_domain_mismatch"

    def _domain_gate(self, rule: RuleRecord, context: Any) -> tuple[bool, str | None]:
        dom = _rule_domain(rule)
        layer = _rule_layer(rule)
        primary = set(getattr(context, "primary_domains", None) or [])
        secondary = set(getattr(context, "secondary_domains", None) or [])
        bridges = list(getattr(context, "triggered_bridges", None) or [])
        inc = bool(getattr(context, "include_shared", True))

        if layer == "shared" or dom == "shared":
            if not inc:
                return False, "unification_rejected_by_domain_shared_disabled"
            return True, None
        if dom in primary:
            return True, None
        if dom in secondary:
            if not self.cross_domain_policy.allow_primary_to_secondary:
                return False, "unification_rejected_by_domain_secondary_disallowed"
            if self.cross_domain_policy.require_bridge_for_secondary_jump and not bridges:
                return False, "unification_rejected_by_domain_no_bridge"
            return True, None
        if not bool(getattr(context, "strict_domain_enforcement", False)):
            return True, None
        return False, "unification_rejected_by_domain"


def policy_from_context(context: Any) -> DomainReasoningPolicy:
    """Build policy from ReasoningContext.cross_domain_policy or defaults."""
    cp = getattr(context, "cross_domain_policy", None)
    if isinstance(cp, CrossDomainPolicy):
        return DomainReasoningPolicy(cross_domain_policy=cp)
    return DomainReasoningPolicy(cross_domain_policy=CrossDomainPolicy())
