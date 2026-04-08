"""Integration of cross-domain reasoning into QA pipeline."""

from __future__ import annotations

import logging
from typing import Any

from runtime.activated_domains_artifact import ActivatedDomainsArtifact
from runtime.cross_domain_executor import CrossDomainReasoningExecutor
from runtime.cross_domain_jump_policy import CrossDomainJumpPolicy
from schemas.proof import ProofObject, ProofStep

logger = logging.getLogger(__name__)


class CrossDomainProofBuilder:
    """Builds proofs with cross-domain tracking for multi-rulebase reasoning."""

    def __init__(
        self,
        executor: CrossDomainReasoningExecutor,
    ) -> None:
        self.executor = executor

    def add_proof_step(
        self,
        step_num: int,
        description: str,
        current_domain: str,
        rule_id: str | None = None,
        statute_reference: str | None = None,
        additional_context: dict[str, Any] | None = None,
    ) -> ProofStep:
        """
        Add a proof step with automatic domain tracking.
        
        This method integrates domain state from the executor.
        """
        return self.executor.log_proof_step_with_domain(
            step_id=step_num,
            description=description,
            domain=current_domain,
            rule_id=rule_id,
            statute=statute_reference,
            additional_data=additional_context,
        )

    def mark_domain_transition(
        self,
        from_domain: str,
        to_domain: str,
        bridge_rule_id: str,
        reason: str | None = None,
    ) -> ProofStep:
        """
        Record a domain transition in the proof with bridge information.
        """
        step_num = len(self.executor._proof_steps) + 1
        return self.executor.log_proof_step_with_domain(
            step_id=step_num,
            description=f"Bridge crossing from {from_domain} to {to_domain}",
            domain=to_domain,
            rule_id=bridge_rule_id,
            crossed_from=from_domain,
            crossed_to=to_domain,
            additional_data={"reason": reason} if reason else None,
        )

    def finalize_proof(
        self,
        proof_id: str,
        conclusion: str,
        selected_rule: str | None = None,
    ) -> ProofObject:
        """
        Finalize a proof with cross-domain information.
        
        Includes:
        - All proof steps with domain tracking
        - Domain transitions and bridges used
        - Final statute grounding
        """
        # Validate consistency
        is_valid, errors = self.executor.validate_reasoning_consistency()
        if not errors:
            logger.debug("[cross_domain_proof] validation passed")
        else:
            logger.warning("[cross_domain_proof] validation failed: %s", errors)

        # Build proof
        proof = ProofObject(
            proof_id=proof_id,
            selected_rule=selected_rule,
            conclusion=conclusion,
            derived_conclusion=conclusion,
            proof_steps=self.executor._proof_steps,
            provenance={
                "cross_domain_trace": self.executor.get_proof_trace(),
                "final_statute": self.executor.get_final_grounding_statute(),
                "activated_domains": list(self.executor.get_current_accessible_domains()),
                "bridges_triggered": self.executor.activated_domains.triggered_bridges,
                "domain_hops": self.executor.activated_domains.cross_domain_hops,
            },
        )
        
        return proof


def should_enable_cross_domain_reasoning(
    domains_detected: list[str],
    min_domains_for_cross: int = 2,
) -> bool:
    """
    Determine if cross-domain reasoning should be enabled based on detected domains.
    
    Parameters:
        domains_detected: Domains inferred from the query
        min_domains_for_cross: Minimum unique domains to enable cross-domain
    
    Returns:
        True if cross-domain reasoning should be active
    """
    unique_domains = set(domains_detected)
    return len(unique_domains) >= min_domains_for_cross


def get_recommended_secondary_domains(
    primary_domain: str,
    all_available_domains: list[str],
) -> list[str]:
    """
    Get recommended secondary domains based on primary domain and query context.
    
    This is a heuristic for domain expansion:
    - enterprise -> includes tax, labor
    - labor -> includes enterprise, shared_benefit_rules
    - tax -> includes enterprise, labor
    """
    recommendations = {
        "enterprise": ["labor", "tax"],
        "labor": ["enterprise"],
        "tax": ["enterprise"],
    }
    
    recommended = recommendations.get(primary_domain, [])
    # Filter to only available domains
    return [d for d in recommended if d in all_available_domains]
