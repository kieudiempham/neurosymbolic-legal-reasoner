"""Cross-domain jump policy with sophisticated reasoning about when to activate shared layer, stay single-domain, or jump."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from schemas.rule import RuleRecord

logger = logging.getLogger(__name__)


class JumpDecision(Enum):
    """Policy decision on cross-domain jumping."""

    STAY_PRIMARY = "stay_primary"  # Stay within primary domain
    ACTIVATE_SHARED = "activate_shared"  # Activate shared layer facts
    JUMP_SECONDARY = "jump_secondary"  # Jump to secondary domain with bridge
    BLOCKED = "blocked"  # Jump blocked by policy


class CrossDomainJumpPolicy:
    """Sophisticated policy for determining when to jump domains or activate shared layer."""

    def __init__(
        self,
        allow_shared_to_domain: bool = True,
        allow_primary_to_secondary: bool = True,
        require_bridge_for_secondary_jump: bool = True,
        shared_layer_activation_threshold: int = 3,  # Activate shared after N unmet requirements
        max_cross_domain_hops: int = 2,
    ) -> None:
        self.allow_shared_to_domain = allow_shared_to_domain
        self.allow_primary_to_secondary = allow_primary_to_secondary
        self.require_bridge_for_secondary_jump = require_bridge_for_secondary_jump
        self.shared_layer_activation_threshold = shared_layer_activation_threshold
        self.max_cross_domain_hops = max_cross_domain_hops

    def decide_jump(
        self,
        current_domain: str,
        target_domain: str,
        primary_domains: list[str],
        secondary_domains: list[str],
        current_cross_hops: int,
        unmet_requirements: list[str],
        available_bridges: list[str],
    ) -> tuple[JumpDecision, str]:
        """
        Decide whether to jump, stay, or activate shared layer.
        
        Returns:
            (decision, reason)
        """
        # Check policy limits
        if current_cross_hops >= self.max_cross_domain_hops:
            return JumpDecision.BLOCKED, f"policy_max_hops_exceeded ({current_cross_hops}/{self.max_cross_domain_hops})"

        # Already in target domain
        if current_domain == target_domain:
            return JumpDecision.STAY_PRIMARY, "already_in_domain"

        # Check if target is primary
        if target_domain in primary_domains:
            return JumpDecision.STAY_PRIMARY, "target_in_primary_domains"

        # Check if target is secondary
        if target_domain in secondary_domains:
            if not self.allow_primary_to_secondary:
                return JumpDecision.BLOCKED, "policy_primary_to_secondary_disabled"
            
            if self.require_bridge_for_secondary_jump and not available_bridges:
                return JumpDecision.BLOCKED, "secondary_jump_requires_bridge"
            
            return JumpDecision.JUMP_SECONDARY, "secondary_domain_with_bridge"

        # Check if we should activate shared layer
        if self.allow_shared_to_domain and len(unmet_requirements) >= self.shared_layer_activation_threshold:
            return JumpDecision.ACTIVATE_SHARED, f"unmet_requirements_threshold ({len(unmet_requirements)}/{self.shared_layer_activation_threshold})"

        return JumpDecision.BLOCKED, "target_domain_not_accessible"

    def should_activate_shared_layer(
        self,
        unmet_requirements: int,
        current_domain_coverage: float,
    ) -> bool:
        """
        Determine if shared layer should be activated based on requirements coverage.
        
        Args:
            unmet_requirements: Count of unmet requirements
            current_domain_coverage: Percentage of requirements covered by current domain (0-1)
        """
        if unmet_requirements < self.shared_layer_activation_threshold:
            return False
        if current_domain_coverage > 0.7:  # If current domain covers >70%, don't need shared
            return False
        return self.allow_shared_to_domain

    def to_trace_dict(self) -> dict[str, Any]:
        """Export policy as dict for proof trace."""
        return {
            "allow_shared_to_domain": self.allow_shared_to_domain,
            "allow_primary_to_secondary": self.allow_primary_to_secondary,
            "require_bridge_for_secondary_jump": self.require_bridge_for_secondary_jump,
            "shared_layer_activation_threshold": self.shared_layer_activation_threshold,
            "max_cross_domain_hops": self.max_cross_domain_hops,
        }


class CrossDomainJumpDetector:
    """Detects when a cross-domain jump opportunity exists."""

    def __init__(self, policy: CrossDomainJumpPolicy) -> None:
        self.policy = policy

    def detect_jump_opportunity(
        self,
        current_domain: str,
        missing_requirement: str,
        primary_domains: list[str],
        secondary_domains: list[str],
        available_rules_by_domain: dict[str, list[RuleRecord]],
        current_cross_hops: int,
        available_bridges: list[str],
    ) -> tuple[str | None, JumpDecision, str]:
        """
        Detect if jumping to another domain would help satisfy a missing requirement.
        
        Returns:
            (target_domain_if_any, decision, reason)
        """
        # Check each secondary domain
        for sec_domain in secondary_domains:
            rules_in_domain = available_rules_by_domain.get(sec_domain, [])
            
            # Check if any rule in this domain could help
            for rule in rules_in_domain:
                rule_dom = getattr(rule, 'metadata', {}).get('domain', 'enterprise')
                if missing_requirement.lower() in str(rule.head or "").lower():
                    # Jump detected: secondary domain has rule
                    decision, reason = self.policy.decide_jump(
                        current_domain,
                        sec_domain,
                        primary_domains,
                        secondary_domains,
                        current_cross_hops,
                        [missing_requirement],
                        available_bridges,
                    )
                    return sec_domain, decision, reason

        return None, JumpDecision.STAY_PRIMARY, "no_jump_opportunity_detected"
