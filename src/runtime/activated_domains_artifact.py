"""Activated domains artifact — tracks which domains are active during reasoning (phase 2+)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ActivatedDomainInfo:
    """Metadata about one activated domain during reasoning."""

    domain_id: str
    domain_name: str
    activation_reason: str | None = None  # "primary", "secondary_bridged", "shared_layer", etc.
    activation_step: int | None = None  # Which reasoning step activated it
    bridge_rule_ids: list[str] = field(default_factory=list)  # Bridge rules that enabled activation
    shared_facts_used: list[str] = field(default_factory=list)  # Shared facts referenced from this domain


@dataclass
class ActivatedDomainsArtifact:
    """Runtime artifact tracking multi-domain reasoning state."""

    query_id: str
    primary_domains: list[str] = field(default_factory=list)  # Domains that must be included
    secondary_domains: list[str] = field(default_factory=list)  # Domains available if bridged
    active_domains: dict[str, ActivatedDomainInfo] = field(default_factory=dict)  # Domains currently active
    shared_layer_active: bool = False  # Whether shared fact layer is being used
    triggered_bridges: list[str] = field(default_factory=list)  # Bridge rule IDs that have been resolved
    cross_domain_hops: int = 0  # Count of domain transitions
    max_cross_domain_hops: int = 1  # Policy limit
    
    def activate_domain(
        self,
        domain_id: str,
        domain_name: str | None = None,
        reason: str | None = None,
        step: int | None = None,
    ) -> None:
        """Activate a domain for reasoning."""
        if domain_id not in self.active_domains:
            self.active_domains[domain_id] = ActivatedDomainInfo(
                domain_id=domain_id,
                domain_name=domain_name or domain_id,
                activation_reason=reason,
                activation_step=step,
            )
            logger.debug(
                "[activated_domains] activated %s (reason=%s, step=%s)",
                domain_id,
                reason,
                step,
            )

    def trigger_bridge(
        self,
        bridge_rule_id: str,
        from_domain: str,
        to_domain: str,
    ) -> None:
        """Record a bridge rule trigger between domains."""
        if bridge_rule_id not in self.triggered_bridges:
            self.triggered_bridges.append(bridge_rule_id)
            self.cross_domain_hops += 1
            logger.debug(
                "[bridge_trigger] %s: %s -> %s",
                bridge_rule_id,
                from_domain,
                to_domain,
            )
            # Activate the target domain if not already active
            if to_domain not in self.active_domains:
                self.activate_domain(
                    to_domain,
                    reason="secondary_bridged",
                )
            # Record bridge in source domain info
            if from_domain in self.active_domains:
                self.active_domains[from_domain].bridge_rule_ids.append(bridge_rule_id)

    def use_shared_fact(
        self,
        fact_id: str,
        from_domain: str,
    ) -> None:
        """Record usage of a shared fact by a domain."""
        if from_domain in self.active_domains:
            if fact_id not in self.active_domains[from_domain].shared_facts_used:
                self.active_domains[from_domain].shared_facts_used.append(fact_id)

    def can_jump_to_domain(self, target_domain: str) -> tuple[bool, str]:
        """Check if cross-domain jump to target_domain is permitted."""
        if target_domain in self.active_domains:
            return True, "already_active"
        if self.cross_domain_hops >= self.max_cross_domain_hops:
            return False, f"policy_max_hops_reached ({self.cross_domain_hops}/{self.max_cross_domain_hops})"
        if target_domain not in self.secondary_domains and target_domain not in self.primary_domains:
            return False, "target_domain_not_available"
        if target_domain in self.secondary_domains:
            # Allow jump to secondary if in allowed list; bridge enforcement happens in executor
            pass
        return True, "allowed"

    def is_domain_accessible(self, domain_id: str) -> bool:
        """Check if domain is currently accessible for reasoning."""
        return domain_id in self.active_domains or domain_id in self.primary_domains

    def to_dict(self) -> dict[str, Any]:
        """Export artifact as JSON-serializable dict."""
        return {
            "query_id": self.query_id,
            "primary_domains": self.primary_domains,
            "secondary_domains": self.secondary_domains,
            "active_domains": {
                did: {
                    "domain_id": info.domain_id,
                    "domain_name": info.domain_name,
                    "activation_reason": info.activation_reason,
                    "activation_step": info.activation_step,
                    "bridge_rule_ids": info.bridge_rule_ids,
                    "shared_facts_used": info.shared_facts_used,
                }
                for did, info in self.active_domains.items()
            },
            "shared_layer_active": self.shared_layer_active,
            "triggered_bridges": self.triggered_bridges,
            "cross_domain_hops": self.cross_domain_hops,
            "max_cross_domain_hops": self.max_cross_domain_hops,
        }


def create_activated_domains_artifact(
    query_id: str,
    primary_domains: list[str] | None = None,
    secondary_domains: list[str] | None = None,
    max_hops: int = 1,
) -> ActivatedDomainsArtifact:
    """Factory to create a new activated domains artifact."""
    primary_doms = primary_domains or ["enterprise"]
    secondary_doms = secondary_domains or []
    
    artifact = ActivatedDomainsArtifact(
        query_id=query_id,
        primary_domains=primary_doms,
        secondary_domains=secondary_doms,
        max_cross_domain_hops=max_hops,
    )
    
    # Activate all primary domains immediately
    for dom in primary_doms:
        artifact.activate_domain(dom, reason="primary")
    
    return artifact
