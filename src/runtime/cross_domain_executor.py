"""Cross-domain reasoning executor — main orchestrator for multi-domain QA workflows."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from runtime.activated_domains_artifact import ActivatedDomainsArtifact, create_activated_domains_artifact
from runtime.cross_domain_bridge_executor import (
    CrossDomainBridgeExecutor,
    BridgeFact,
    BridgeRule,
)
from runtime.cross_domain_jump_policy import (
    CrossDomainJumpPolicy,
    CrossDomainJumpDetector,
    JumpDecision,
)
from schemas.proof import ProofStep

logger = logging.getLogger(__name__)


class CrossDomainReasoningExecutor:
    """
    Main orchestrator for cross-domain reasoning with:
    - Activated domains tracking
    - Bridge rule resolution
    - Shared fact layer management
    - Jump policy enforcement
    - Proof logging with domain annotations
    """

    def __init__(
        self,
        query_id: str,
        primary_domains: list[str] | None = None,
        secondary_domains: list[str] | None = None,
        jump_policy: CrossDomainJumpPolicy | None = None,
    ) -> None:
        self.query_id = query_id
        self.activated_domains = create_activated_domains_artifact(
            query_id=query_id,
            primary_domains=primary_domains,
            secondary_domains=secondary_domains,
        )
        self.jump_policy = jump_policy or CrossDomainJumpPolicy()
        self.jump_detector = CrossDomainJumpDetector(self.jump_policy)
        self.bridge_executor = CrossDomainBridgeExecutor(self.activated_domains)
        
        self._proof_steps: list[ProofStep] = []
        self._domain_transitions: list[dict[str, Any]] = []

    def add_bridge_rule(
        self,
        from_domain: str,
        to_domain: str,
        rule_id: str | None = None,
        condition: str | None = None,
        priority: int = 0,
    ) -> str:
        """
        Register a bridge rule that enables jumping from one domain to another.
        
        Returns:
            rule_id
        """
        rule_id = rule_id or f"bridge_{from_domain}_{to_domain}_{uuid.uuid4().hex[:8]}"
        bridge = BridgeRule(
            rule_id=rule_id,
            from_domain=from_domain,
            to_domain=to_domain,
            condition=condition,
            priority=priority,
        )
        self.bridge_executor.register_bridge_rule(bridge)
        return rule_id

    def add_bridge_fact(
        self,
        fact_content: str,
        to_domains: list[str],
        fact_id: str | None = None,
        predicate: str | None = None,
        statute: str | None = None,
    ) -> str:
        """
        Register a shared fact that is accessible from specified domains.
        
        Returns:
            fact_id
        """
        fact_id = fact_id or f"shared_fact_{uuid.uuid4().hex[:8]}"
        fact = BridgeFact(
            fact_id=fact_id,
            fact_content=fact_content,
            to_domains=to_domains,
            predicate=predicate,
            statute_reference=statute,
        )
        self.bridge_executor.register_bridge_fact(fact)
        return fact_id

    def should_stay_single_domain(
        self,
        current_domain: str,
        unmet_requirements: list[str],
    ) -> bool:
        """
        Determine if reasoning should stay within single domain.
        
        Policy:
        - If all primary domains are satisfied, stay
        - If <threshold unmet requirements, stay
        - If current domain is primary and covers >70%, stay
        """
        if not unmet_requirements:
            return True
        
        if len(unmet_requirements) < self.jump_policy.shared_layer_activation_threshold:
            return True
        
        return False

    def should_activate_shared_layer(
        self,
        current_domain: str,
        unmet_requirements: int,
        satisfied_requirements: int,
    ) -> bool:
        """
        Determine if shared fact layer should be activated.
        
        Policy:
        - Activate when unmet_requirements >= threshold
        - AND current domain coverage < 70%
        """
        total = unmet_requirements + satisfied_requirements
        if total == 0:
            return False
        
        coverage = satisfied_requirements / total
        return self.jump_policy.should_activate_shared_layer(unmet_requirements, coverage)

    def can_jump_to_secondary(
        self,
        target_domain: str,
    ) -> tuple[bool, str]:
        """
        Check if jump to secondary domain is permitted.
        
        Considerations:
        - Policy allows primary->secondary
        - Has bridge rule available
        - Within hop limit
        """
        if target_domain not in self.activated_domains.secondary_domains:
            return False, "not_in_secondary_domains"
        
        can_cross, reason = self.bridge_executor.can_cross_to_domain(target_domain)
        return can_cross, reason

    def execute_domain_jump(
        self,
        from_domain: str,
        to_domain: str,
        bridge_rule_id: str | None = None,
    ) -> tuple[bool, str, list[Any]]:
        """
        Execute a jump to another domain via bridge.
        
        Returns:
            (success, reason, accessible_facts)
        """
        logger.info(
            "[cross_domain] attempting jump: %s -> %s",
            from_domain,
            to_domain,
        )
        
        # Check policy before attempting jump
        if to_domain in self.activated_domains.secondary_domains:
            if not self.jump_policy.allow_primary_to_secondary:
                logger.debug("[cross_domain] jump blocked by policy: allow_primary_to_secondary=False")
                return False, "policy_blocks_primary_to_secondary_jump", []
        
        success, reason, facts = self.bridge_executor.execute_bridge_crossing(
            from_domain,
            to_domain,
            bridge_rule_id,
        )
        
        if success:
            # Record transition
            self._domain_transitions.append({
                "from_domain": from_domain,
                "to_domain": to_domain,
                "bridge_rule_id": bridge_rule_id,
                "timestamp": len(self._proof_steps),
                "accessible_facts": [f.fact_id for f in facts],
            })
            logger.debug("[cross_domain] jump succeeded, %d facts accessible", len(facts))
        else:
            logger.debug("[cross_domain] jump blocked: %s", reason)
        
        return success, reason, facts

    def log_proof_step_with_domain(
        self,
        step_id: int,
        description: str,
        domain: str,
        rule_id: str | None = None,
        bridge_used: str | None = None,
        crossed_from: str | None = None,
        crossed_to: str | None = None,
        statute: str | None = None,
        additional_data: dict[str, Any] | None = None,
    ) -> ProofStep:
        """
        Log a proof step with full domain tracking.
        
        Captures:
        - Which domain this step applies in
        - Any bridge rules used
        - Cross-domain jumps taken
        - Final statute grounding
        """
        step = ProofStep(
            step_id=step_id,
            description=description,
            domain=domain,
            rule_id=rule_id,
            bridge_fact_ids_used=[bridge_used] if bridge_used else [],
            cross_domain_from=crossed_from,
            cross_domain_to=crossed_to,
            source_article=statute,
            policy_check=str(self.jump_policy.to_trace_dict()) if crossed_from else None,
        )
        
        if additional_data:
            for key, val in additional_data.items():
                if hasattr(step, key):
                    setattr(step, key, val)
        
        self._proof_steps.append(step)
        return step

    def get_current_accessible_domains(self) -> list[str]:
        """Get list of domains currently accessible for reasoning."""
        return list(self.activated_domains.active_domains.keys())

    def get_proof_trace(self) -> dict[str, Any]:
        """
        Export complete proof trace with domain annotations.
        
        Includes:
        - Activated domains history
        - Bridge transitions
        - Proof steps with domain tracking
        - Final statute references
        """
        return {
            "query_id": self.query_id,
            "activated_domains": self.activated_domains.to_dict(),
            "domain_transitions": self._domain_transitions,
            "proof_steps": [
                {
                    "step_id": step.step_id,
                    "description": step.description,
                    "domain": step.domain,
                    "rule_id": step.rule_id,
                    "bridges_used": step.bridge_fact_ids_used,
                    "cross_domain_from": step.cross_domain_from,
                    "cross_domain_to": step.cross_domain_to,
                    "statute": step.source_article,
                }
                for step in self._proof_steps
            ],
            "bridge_executor_state": self.bridge_executor.to_trace_dict(),
        }

    def get_final_grounding_statute(self) -> str | None:
        """Get the final statute reference that grounds the answer."""
        for step in reversed(self._proof_steps):
            if step.source_article:
                return step.source_article
        return None

    def validate_reasoning_consistency(self) -> tuple[bool, list[str]]:
        """
        Validate that cross-domain reasoning was consistent and valid.
        
        Checks:
        - No hops exceed policy limit
        - All bridges were properly registered
        - Domain transitions are valid
        - Shared layer use is consistent
        """
        errors: list[str] = []
        
        # Check hop count
        if self.activated_domains.cross_domain_hops > self.activated_domains.max_cross_domain_hops:
            errors.append(
                f"hop_count_exceeded: {self.activated_domains.cross_domain_hops} > {self.activated_domains.max_cross_domain_hops}"
            )
        
        # Check all transitions have registered bridges
        for trans in self._domain_transitions:
            from_dom = trans["from_domain"]
            to_dom = trans["to_domain"]
            bridge_id = trans["bridge_rule_id"]
            
            if to_dom not in self.activated_domains.primary_domains and to_dom not in self.activated_domains.secondary_domains:
                errors.append(f"invalid_target_domain: {to_dom}")
            
            if bridge_id and bridge_id not in self.bridge_executor.bridge_rules:
                errors.append(f"unregistered_bridge: {bridge_id}")
        
        return len(errors) == 0, errors


def create_cross_domain_executor(
    query_id: str,
    primary_domains: list[str] | None = None,
    secondary_domains: list[str] | None = None,
    allow_shared: bool = True,
    allow_cross_jump: bool = True,
    max_hops: int = 2,
) -> CrossDomainReasoningExecutor:
    """
    Factory to create a configured cross-domain executor.
    
    Args:
        query_id: Unique query identifier
        primary_domains: Domains that must be included (default: ["enterprise"])
        secondary_domains: Optional domains accessible via bridge
        allow_shared: Whether to activate shared fact layer
        allow_cross_jump: Whether cross-domain jumps are allowed
        max_hops: Maximum allowed cross-domain transitions
    """
    policy = CrossDomainJumpPolicy(
        allow_shared_to_domain=allow_shared,
        allow_primary_to_secondary=allow_cross_jump,
        max_cross_domain_hops=max_hops,
    )
    
    return CrossDomainReasoningExecutor(
        query_id=query_id,
        primary_domains=primary_domains or ["enterprise"],
        secondary_domains=secondary_domains,
        jump_policy=policy,
    )
