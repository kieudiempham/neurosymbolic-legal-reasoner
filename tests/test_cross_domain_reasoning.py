"""Tests for cross-domain reasoning with shared fact layer and bridge rules."""

from __future__ import annotations

import pytest

from runtime.activated_domains_artifact import (
    ActivatedDomainsArtifact,
    create_activated_domains_artifact,
)
from runtime.cross_domain_bridge_executor import (
    BridgeFact,
    BridgeRule,
    CrossDomainBridgeExecutor,
    SharedFactLayer,
)
from runtime.cross_domain_jump_policy import (
    CrossDomainJumpPolicy,
    CrossDomainJumpDetector,
    JumpDecision,
)
from runtime.cross_domain_executor import (
    CrossDomainReasoningExecutor,
    create_cross_domain_executor,
)


class TestActivatedDomainsArtifact:
    """Test activated domains artifact management."""

    def test_create_artifact_with_primary_domains(self):
        """Test creating artifact with primary domains."""
        artifact = create_activated_domains_artifact(
            query_id="test_1",
            primary_domains=["enterprise", "labor"],
        )
        
        assert artifact.query_id == "test_1"
        assert "enterprise" in artifact.active_domains
        assert "labor" in artifact.active_domains
        assert len(artifact.primary_domains) == 2

    def test_activate_domain_on_demand(self):
        """Test activating a domain at runtime."""
        artifact = create_activated_domains_artifact(
            query_id="test_2",
            primary_domains=["enterprise"],
            secondary_domains=["tax"],
        )
        
        assert "tax" not in artifact.active_domains
        artifact.activate_domain("tax", reason="secondary_bridged", step=5)
        assert "tax" in artifact.active_domains
        assert artifact.active_domains["tax"].activation_reason == "secondary_bridged"

    def test_trigger_bridge_records_transition(self):
        """Test bridge trigger records cross-domain transition."""
        artifact = create_activated_domains_artifact(
            query_id="test_3",
            primary_domains=["enterprise"],
            secondary_domains=["tax"],
        )
        
        artifact.trigger_bridge("bridge_ent_tax_001", "enterprise", "tax")
        
        assert "bridge_ent_tax_001" in artifact.triggered_bridges
        assert artifact.cross_domain_hops == 1

    def test_can_jump_to_domain_policy_checks(self):
        """Test policy checks for cross-domain jumps."""
        artifact = create_activated_domains_artifact(
            query_id="test_4",
            primary_domains=["enterprise"],
            secondary_domains=["tax"],
            max_hops=1,
        )
        
        # First jump should be allowed
        can_jump, reason = artifact.can_jump_to_domain("tax")
        assert can_jump is True
        
        # Second jump should be blocked (max_hops=1)
        artifact.cross_domain_hops = 1
        can_jump, reason = artifact.can_jump_to_domain("labor")
        assert can_jump is False
        assert "max_hops" in reason

    def test_use_shared_fact_tracking(self):
        """Test tracking of shared fact usage by domain."""
        artifact = create_activated_domains_artifact(
            query_id="test_5",
            primary_domains=["enterprise"],
        )
        
        artifact.use_shared_fact("shared_fact_001", "enterprise")
        
        assert "shared_fact_001" in artifact.active_domains["enterprise"].shared_facts_used


class TestSharedFactLayer:
    """Test shared fact layer management."""

    def test_add_bridge_fact_and_retrieve(self):
        """Test adding and retrieving bridge facts."""
        layer = SharedFactLayer()
        
        fact = BridgeFact(
            fact_id="fact_001",
            fact_content="Both employees and contractors need same benefits",
            predicate="needs_benefits",
            to_domains=["enterprise", "labor"],
        )
        
        layer.add_bridge_fact(fact)
        
        # Should be indexed for both domains
        facts_ent = layer.get_facts_for_domain("enterprise")
        facts_lab = layer.get_facts_for_domain("labor")
        
        assert any(f.fact_id == "fact_001" for f in facts_ent)
        assert any(f.fact_id == "fact_001" for f in facts_lab)

    def test_bridge_fact_predicate_indexing(self):
        """Test bridge facts indexed by predicate."""
        layer = SharedFactLayer()
        
        fact = BridgeFact(
            fact_id="fact_002",
            fact_content="Tax implications for benefits",
            predicate="tax_implication",
            to_domains=["enterprise", "tax"],
        )
        
        layer.add_bridge_fact(fact)
        
        facts_by_pred = layer.get_facts_by_predicate("tax_implication")
        assert len(facts_by_pred) == 1
        assert facts_by_pred[0].fact_id == "fact_002"


class TestCrossDomainBridgeExecutor:
    """Test bridge execution for cross-domain reasoning."""

    def test_register_bridge_rule(self):
        """Test registering a bridge rule."""
        artifact = create_activated_domains_artifact("test_6")
        executor = CrossDomainBridgeExecutor(artifact)
        
        bridge = BridgeRule(
            rule_id="bridge_ent_tax_001",
            from_domain="enterprise",
            to_domain="tax",
            priority=10,
        )
        
        executor.register_bridge_rule(bridge)
        
        assert "bridge_ent_tax_001" in executor.bridge_rules

    def test_can_cross_to_domain_success(self):
        """Test checking if domain crossing is possible."""
        artifact = create_activated_domains_artifact(
            query_id="test_7",
            primary_domains=["enterprise"],
            secondary_domains=["tax"],
        )
        executor = CrossDomainBridgeExecutor(artifact)
        
        bridge = BridgeRule(
            rule_id="bridge_001",
            from_domain="enterprise",
            to_domain="tax",
        )
        executor.register_bridge_rule(bridge)
        
        can_cross, reason = executor.can_cross_to_domain("tax")
        assert can_cross is True

    def test_execute_bridge_crossing_activates_domain(self):
        """Test that bridge crossing activates target domain."""
        artifact = create_activated_domains_artifact(
            query_id="test_8",
            primary_domains=["enterprise"],
            secondary_domains=["tax"],
        )
        executor = CrossDomainBridgeExecutor(artifact)
        
        # Register bridge and fact
        bridge = BridgeRule(
            rule_id="bridge_001",
            from_domain="enterprise",
            to_domain="tax",
        )
        executor.register_bridge_rule(bridge)
        
        fact = BridgeFact(
            fact_id="fact_001",
            fact_content="Tax rule for benefits",
            to_domains=["tax"],
        )
        executor.register_bridge_fact(fact)
        
        # Execute crossing
        success, reason, facts = executor.execute_bridge_crossing(
            "enterprise",
            "tax",
        )
        
        assert success is True
        assert "tax" in artifact.active_domains
        assert len(facts) > 0

    def test_execute_bridge_crossing_blocked_no_policy(self):
        """Test that bridge crossing is blocked when policy forbids it."""
        artifact = create_activated_domains_artifact(
            query_id="test_9",
            primary_domains=["enterprise"],
            secondary_domains=["tax"],
            max_hops=0,  # No jumps allowed
        )
        executor = CrossDomainBridgeExecutor(artifact)
        
        bridge = BridgeRule(
            rule_id="bridge_001",
            from_domain="enterprise",
            to_domain="tax",
        )
        executor.register_bridge_rule(bridge)
        
        success, reason, facts = executor.execute_bridge_crossing(
            "enterprise",
            "tax",
        )
        
        assert success is False
        assert "max_hops" in reason.lower()


class TestCrossDomainJumpPolicy:
    """Test cross-domain jump policy decisions."""

    def test_stay_primary_decision(self):
        """Test policy decides to stay in primary domain."""
        policy = CrossDomainJumpPolicy()
        
        decision, reason = policy.decide_jump(
            current_domain="enterprise",
            target_domain="enterprise",
            primary_domains=["enterprise"],
            secondary_domains=["tax"],
            current_cross_hops=0,
            unmet_requirements=[],
            available_bridges=["bridge_001"],
        )
        
        assert decision == JumpDecision.STAY_PRIMARY
        assert "already_in_domain" in reason

    def test_jump_secondary_decision(self):
        """Test policy decides to jump to secondary domain."""
        policy = CrossDomainJumpPolicy(allow_primary_to_secondary=True)
        
        decision, reason = policy.decide_jump(
            current_domain="enterprise",
            target_domain="tax",
            primary_domains=["enterprise"],
            secondary_domains=["tax"],
            current_cross_hops=0,
            unmet_requirements=["tax_rate"],
            available_bridges=["bridge_001"],
        )
        
        assert decision == JumpDecision.JUMP_SECONDARY

    def test_jump_blocked_by_policy(self):
        """Test policy blocks jump when disabled."""
        policy = CrossDomainJumpPolicy(allow_primary_to_secondary=False)
        
        decision, reason = policy.decide_jump(
            current_domain="enterprise",
            target_domain="tax",
            primary_domains=["enterprise"],
            secondary_domains=["tax"],
            current_cross_hops=0,
            unmet_requirements=["tax_rate"],
            available_bridges=[],
        )
        
        assert decision == JumpDecision.BLOCKED

    def test_jump_blocked_at_hop_limit(self):
        """Test policy blocks jump when hop limit reached."""
        policy = CrossDomainJumpPolicy(max_cross_domain_hops=1)
        
        decision, reason = policy.decide_jump(
            current_domain="enterprise",
            target_domain="labor",
            primary_domains=["enterprise"],
            secondary_domains=["labor", "tax"],
            current_cross_hops=1,  # Already at limit
            unmet_requirements=["labor_law"],
            available_bridges=["bridge_001"],
        )
        
        assert decision == JumpDecision.BLOCKED
        assert "max_hops" in reason

    def test_activate_shared_layer_on_high_unmet(self):
        """Test shared layer activation when many requirements unmet."""
        policy = CrossDomainJumpPolicy(shared_layer_activation_threshold=3)
        
        should_activate = policy.should_activate_shared_layer(
            unmet_requirements=5,  # >= threshold
            current_domain_coverage=0.3,  # <70%
        )
        
        assert should_activate is True

    def test_skip_shared_layer_on_good_coverage(self):
        """Test shared layer not activated when domain coverage is good."""
        policy = CrossDomainJumpPolicy(shared_layer_activation_threshold=3)
        
        should_activate = policy.should_activate_shared_layer(
            unmet_requirements=5,
            current_domain_coverage=0.8,  # >70%
        )
        
        assert should_activate is False


class TestCrossDomainReasoningExecutor:
    """Test main cross-domain executor."""

    def test_single_domain_no_jump(self):
        """Test single-domain reasoning without any cross-domain jumps."""
        executor = create_cross_domain_executor(
            query_id="query_001",
            primary_domains=["enterprise"],
            max_hops=0,  # Prevent jumps
        )
        
        # Check initial state
        accessible = executor.get_current_accessible_domains()
        assert "enterprise" in accessible
        
        # Check stay_single_domain policy
        should_stay = executor.should_stay_single_domain(
            "enterprise",
            unmet_requirements=[],
        )
        assert should_stay is True

    def test_cross_domain_jump_successful(self):
        """Test successful cross-domain jump via bridge."""
        executor = create_cross_domain_executor(
            query_id="query_002",
            primary_domains=["enterprise"],
            secondary_domains=["tax"],
            allow_cross_jump=True,
            max_hops=2,
        )
        
        # Register bridge and fact
        executor.add_bridge_rule("enterprise", "tax", rule_id="bridge_001")
        executor.add_bridge_fact(
            "Tax rate for benefits",
            ["tax"],
            fact_id="fact_001",
        )
        
        # Execute jump
        success, reason, facts = executor.execute_domain_jump("enterprise", "tax")
        
        assert success is True
        assert "tax" in executor.get_current_accessible_domains()

    def test_cross_domain_jump_blocked_by_policy(self):
        """Test cross-domain jump blocked when policy forbids it."""
        executor = create_cross_domain_executor(
            query_id="query_003",
            primary_domains=["enterprise"],
            secondary_domains=["tax"],
            allow_cross_jump=False,  # Disable cross-domain
            max_hops=2,
        )
        
        # Register bridge
        executor.add_bridge_rule("enterprise", "tax", rule_id="bridge_001")
        
        # Attempt jump (should fail)
        success, reason, facts = executor.execute_domain_jump("enterprise", "tax")
        
        assert success is False

    def test_shared_layer_activation(self):
        """Test shared layer is activated when appropriate."""
        executor = create_cross_domain_executor(
            query_id="query_004",
            primary_domains=["enterprise"],
            allow_shared=True,
        )
        
        # Add shared layer facts
        executor.add_bridge_fact(
            "Shared: Benefits apply to all",
            ["enterprise"],
            fact_id="shared_001",
        )
        
        # Check if shared layer should be activated
        should_activate = executor.should_activate_shared_layer(
            "enterprise",
            unmet_requirements=5,  # Many unmet
            satisfied_requirements=2,  # Few satisfied
        )
        
        assert should_activate is True

    def test_proof_logging_with_domain_tracking(self):
        """Test proof steps logged with domain and bridge information."""
        executor = create_cross_domain_executor(
            query_id="query_005",
            primary_domains=["enterprise"],
        )
        
        # Log proof step in primary domain
        executor.log_proof_step_with_domain(
            step_id=1,
            description="Check employment status",
            domain="enterprise",
            rule_id="rule_001",
            statute="Labor Code Article 10",
        )
        
        # Log cross-domain jump
        executor.log_proof_step_with_domain(
            step_id=2,
            description="Check tax implications",
            domain="tax",
            rule_id="tax_rule_001",
            crossed_from="enterprise",
            crossed_to="tax",
            statute="Tax Code Article 5",
        )
        
        # Verify trace captures both steps
        trace = executor.get_proof_trace()
        assert len(trace["proof_steps"]) == 2
        assert "domain" in trace["proof_steps"][0]
        assert trace["proof_steps"][1]["cross_domain_from"] == "enterprise"

    def test_validate_reasoning_consistency(self):
        """Test validation of reasoning consistency."""
        executor = create_cross_domain_executor(
            query_id="query_006",
            primary_domains=["enterprise"],
            secondary_domains=["tax"],
            max_hops=2,
        )
        
        # Register valid bridge
        executor.add_bridge_rule("enterprise", "tax", rule_id="bridge_001")
        
        # Execute valid jump
        executor.execute_domain_jump("enterprise", "tax")
        
        # Validation should pass
        is_valid, errors = executor.validate_reasoning_consistency()
        assert is_valid is True
        assert len(errors) == 0

    def test_final_grounding_statute(self):
        """Test retrieving final statute grounding."""
        executor = create_cross_domain_executor(
            query_id="query_007",
            primary_domains=["enterprise"],
        )
        
        executor.log_proof_step_with_domain(
            step_id=1,
            description="Initial rule",
            domain="enterprise",
            statute="Labor Code Article 1",
        )
        
        executor.log_proof_step_with_domain(
            step_id=2,
            description="Final rule",
            domain="enterprise",
            statute="Labor Code Article 2",
        )
        
        statute = executor.get_final_grounding_statute()
        assert statute == "Labor Code Article 2"


@pytest.mark.parametrize(
    "domain,unmet,stay_expected",
    [
        ("enterprise", [], True),  # No unmet -> stay
        ("enterprise", ["need_1"], True),  # Few unmet -> stay
        ("enterprise", ["need_1", "need_2", "need_3", "need_4"], False),  # Many unmet -> jump
    ],
)
def test_should_stay_single_domain_parametrized(domain, unmet, stay_expected):
    """Parametrized test for single-domain reasoning decision."""
    executor = create_cross_domain_executor(
        query_id="query_param",
        primary_domains=["enterprise"],
    )
    
    result = executor.should_stay_single_domain(domain, unmet)
    assert result == stay_expected
