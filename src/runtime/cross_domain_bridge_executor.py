"""Cross-domain bridge executor — manages shared fact layer and bridge rule resolution."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from schemas.structured_fact import StructuredFact
from runtime.activated_domains_artifact import ActivatedDomainsArtifact

logger = logging.getLogger(__name__)


@dataclass
class BridgeFact:
    """A fact that bridges multiple domains (shared layer)."""

    fact_id: str
    fact_content: str
    predicate: str | None = None
    from_domain: str | None = None  # Source domain if extracted
    to_domains: list[str] = None  # Target domains
    bridge_priority: int = 0  # Higher = more priority
    statute_reference: str | None = None  # Legal grounding
    
    def __post_init__(self) -> None:
        if self.to_domains is None:
            self.to_domains = []


@dataclass
class BridgeRule:
    """A rule that enables jumping from one domain to another."""

    rule_id: str
    from_domain: str
    to_domain: str
    condition: str | None = None  # Optional: condition for bridge activation
    bridge_type: str = "standard"  # "standard", "temporal", "conflict_resolution"
    priority: int = 0  # Higher = applied first
    
    def is_applicable(self) -> bool:
        """Simple applicability check (can be extended)."""
        if self.condition is None:
            return True
        # Placeholder: more complex condition evaluation would go here
        return True


class SharedFactLayer:
    """Manages facts that are shared across domains."""

    def __init__(self) -> None:
        self.bridge_facts: dict[str, BridgeFact] = {}  # fact_id -> BridgeFact
        self.fact_index_by_domain: dict[str, list[str]] = {}  # domain -> [fact_ids]
        self.fact_index_by_predicate: dict[str, list[str]] = {}  # predicate -> [fact_ids]

    def add_bridge_fact(self, fact: BridgeFact) -> None:
        """Register a bridge fact in the shared layer."""
        self.bridge_facts[fact.fact_id] = fact
        
        # Index by target domains
        for dom in fact.to_domains or []:
            if dom not in self.fact_index_by_domain:
                self.fact_index_by_domain[dom] = []
            if fact.fact_id not in self.fact_index_by_domain[dom]:
                self.fact_index_by_domain[dom].append(fact.fact_id)
        
        # Index by predicate
        if fact.predicate:
            if fact.predicate not in self.fact_index_by_predicate:
                self.fact_index_by_predicate[fact.predicate] = []
            if fact.fact_id not in self.fact_index_by_predicate[fact.predicate]:
                self.fact_index_by_predicate[fact.predicate].append(fact.fact_id)

    def get_facts_for_domain(self, domain: str) -> list[BridgeFact]:
        """Retrieve all bridge facts available for a domain."""
        fact_ids = self.fact_index_by_domain.get(domain, [])
        return [self.bridge_facts[fid] for fid in fact_ids if fid in self.bridge_facts]

    def get_facts_by_predicate(self, predicate: str) -> list[BridgeFact]:
        """Retrieve bridge facts by predicate."""
        fact_ids = self.fact_index_by_predicate.get(predicate, [])
        return [self.bridge_facts[fid] for fid in fact_ids if fid in self.bridge_facts]

    def to_dict(self) -> dict[str, Any]:
        """Export shared layer state as dict."""
        return {
            "bridge_facts": {
                fid: {
                    "fact_id": f.fact_id,
                    "fact_content": f.fact_content,
                    "predicate": f.predicate,
                    "from_domain": f.from_domain,
                    "to_domains": f.to_domains,
                    "bridge_priority": f.bridge_priority,
                    "statute_reference": f.statute_reference,
                }
                for fid, f in self.bridge_facts.items()
            },
            "indexed_domains": list(self.fact_index_by_domain.keys()),
            "indexed_predicates": list(self.fact_index_by_predicate.keys()),
        }


class CrossDomainBridgeExecutor:
    """Coordinates bridge resolution and shared fact layer activation."""

    def __init__(self, activated_domains: ActivatedDomainsArtifact) -> None:
        self.activated_domains = activated_domains
        self.shared_layer = SharedFactLayer()
        self.bridge_rules: dict[str, BridgeRule] = {}  # rule_id -> BridgeRule

    def register_bridge_rule(self, rule: BridgeRule) -> None:
        """Register a bridge rule in the executor."""
        self.bridge_rules[rule.rule_id] = rule
        logger.debug(
            "[bridge_executor] registered bridge %s: %s -> %s",
            rule.rule_id,
            rule.from_domain,
            rule.to_domain,
        )

    def register_bridge_fact(self, fact: BridgeFact) -> None:
        """Register a bridge fact in the shared layer."""
        self.shared_layer.add_bridge_fact(fact)
        self.activated_domains.shared_layer_active = True
        logger.debug(
            "[bridge_executor] registered bridge fact %s for domains %s",
            fact.fact_id,
            fact.to_domains,
        )

    def can_cross_to_domain(self, target_domain: str) -> tuple[bool, str]:
        """Check if we can jump to target domain using available bridges."""
        can_jump, reason = self.activated_domains.can_jump_to_domain(target_domain)
        if not can_jump:
            return False, reason

        # Check if we have a bridge to this domain
        applicable_bridges = [
            br for br in self.bridge_rules.values()
            if br.to_domain == target_domain and br.is_applicable()
        ]
        
        if not applicable_bridges:
            return False, f"no_applicable_bridge_to_{target_domain}"
        
        return True, "bridge_available"

    def execute_bridge_crossing(
        self,
        from_domain: str,
        to_domain: str,
        bridge_rule_id: str | None = None,
    ) -> tuple[bool, str, list[BridgeFact]]:
        """Execute a domain crossing via bridge, returning facts that became available."""
        can_cross, reason = self.can_cross_to_domain(to_domain)
        if not can_cross:
            return False, reason, []

        # Find best applicable bridge
        applicable = [
            br for br in self.bridge_rules.values()
            if br.to_domain == to_domain and br.is_applicable()
        ]
        
        if not applicable:
            return False, "no_applicable_bridge", []

        selected_bridge = max(applicable, key=lambda br: br.priority)
        
        # Record the bridge trigger
        self.activated_domains.trigger_bridge(
            selected_bridge.rule_id,
            from_domain,
            to_domain,
        )
        
        # Get facts that become accessible in target domain
        available_facts = self.shared_layer.get_facts_for_domain(to_domain)
        
        # Record usage
        for fact in available_facts:
            self.activated_domains.use_shared_fact(fact.fact_id, to_domain)
        
        logger.info(
            "[bridge_crossing] %s: %s -> %s via bridge %s, %d facts available",
            bridge_rule_id or "auto",
            from_domain,
            to_domain,
            selected_bridge.rule_id,
            len(available_facts),
        )
        
        return True, "bridge_crossing_succeeded", available_facts

    def get_accessible_facts_for_domain(self, domain: str) -> list[BridgeFact]:
        """Get all bridge facts that are currently accessible to a domain."""
        if not self.activated_domains.shared_layer_active:
            return []
        if domain not in self.activated_domains.active_domains:
            return []
        return self.shared_layer.get_facts_for_domain(domain)

    def to_trace_dict(self) -> dict[str, Any]:
        """Export executor state for proof trace."""
        return {
            "activated_domains": self.activated_domains.to_dict(),
            "shared_layer": self.shared_layer.to_dict(),
            "bridge_rules": {
                rid: {
                    "rule_id": r.rule_id,
                    "from_domain": r.from_domain,
                    "to_domain": r.to_domain,
                    "priority": r.priority,
                    "bridge_type": r.bridge_type,
                }
                for rid, r in self.bridge_rules.items()
            },
        }
