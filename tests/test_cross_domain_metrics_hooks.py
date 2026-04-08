from __future__ import annotations

from evaluation.cross_domain_metrics_aggregator import aggregate_contribution_metrics
from schemas.evaluation_log import build_evaluation_log_artifact


def _sample_debug_trace() -> dict:
    return {
        "query_text": "Kiem tra thue va lao dong",
        "reasoning_context": {
            "primary_domains": ["enterprise"],
            "secondary_domains": ["tax", "labor"],
        },
        "cross_domain_metrics": {
            "cross_domain_jumps_attempted": 2,
            "cross_domain_jumps_success": 1,
            "cross_domain_jumps_blocked": 1,
        },
    }


def _sample_proof() -> dict:
    return {
        "proof_id": "p1",
        "proof_steps": [
            {
                "step_id": 1,
                "description": "enterprise step",
                "domain": "enterprise",
                "bridge_fact_ids_used": [],
                "source_article": "Enterprise Law Art 10",
            },
            {
                "step_id": 2,
                "description": "tax bridge step",
                "domain": "tax",
                "bridge_fact_ids_used": ["bridge_ent_tax_01"],
                "source_article": "Tax Law Art 5",
            },
        ],
        "provenance": {
            "final_statute": "Tax Law Art 5",
            "bridges_triggered": ["bridge_ent_tax_01"],
            "cross_domain_trace": {
                "activated_domains": {
                    "active_domains": {
                        "enterprise": {},
                        "tax": {},
                    }
                },
                "domain_transitions": [
                    {
                        "from_domain": "enterprise",
                        "to_domain": "tax",
                        "bridge_rule_id": "bridge_ent_tax_01",
                    }
                ],
            },
        },
    }


def test_evaluation_log_has_mandatory_cross_domain_metrics() -> None:
    log = build_evaluation_log_artifact(
        session_id="s1",
        query_text="q",
        layer1=None,
        layer2=None,
        retrieved_rules=None,
        selected_rule=None,
        reasoning=None,
        proof=_sample_proof(),
        answer={"answer_text": "ok", "legal_citations": [{"statute": "Tax Law Art 5"}]},
        needs_clarification=False,
        clarification_questions=None,
        verification_trace=None,
        debug_trace=_sample_debug_trace(),
    )

    assert log.activated_domains is not None
    assert "enterprise" in log.activated_domains
    assert "tax" in log.activated_domains
    assert log.bridge_rules_used == ["bridge_ent_tax_01"]
    assert log.cross_domain_jumps_attempted == 2
    assert log.cross_domain_jumps_success == 1
    assert log.cross_domain_jumps_blocked == 1
    assert log.final_statute_grounding == "Tax Law Art 5"
    assert log.proof_domains is not None
    assert "enterprise" in log.proof_domains
    assert "tax" in log.proof_domains


def test_aggregator_builds_batch_ready_summary() -> None:
    records = [
        {
            "sample_id": "s1",
            "activated_domains": ["enterprise", "tax", "shared"],
            "bridge_rules_used": ["bridge_ent_tax_01"],
            "cross_domain_jumps_attempted": 2,
            "cross_domain_jumps_success": 1,
            "cross_domain_jumps_blocked": 1,
            "proof_domains": ["enterprise", "tax"],
            "final_statute_grounding": "Tax Law Art 5",
            "proof": {
                "provenance": {
                    "cross_domain_trace": {
                        "domain_transitions": [
                            {
                                "from_domain": "enterprise",
                                "to_domain": "tax",
                                "bridge_rule_id": "bridge_ent_tax_01",
                            }
                        ]
                    }
                }
            },
        },
        {
            "sample_id": "s2",
            "activated_domains": ["enterprise"],
            "bridge_rules_used": [],
            "cross_domain_jumps_attempted": 0,
            "cross_domain_jumps_success": 0,
            "cross_domain_jumps_blocked": 0,
            "proof_domains": ["enterprise"],
            "final_statute_grounding": "Enterprise Law Art 2",
            "proof": {
                "provenance": {
                    "cross_domain_trace": {
                        "domain_transitions": [
                            {
                                "from_domain": "enterprise",
                                "to_domain": "labor",
                                "bridge_rule_id": "bridge_ent_lab_01",
                            }
                        ]
                    }
                }
            },
        },
    ]

    summary = aggregate_contribution_metrics(records)

    assert summary["rows_total"] == 2
    assert summary["cross_domain_jumps_attempted_total"] == 2
    assert summary["cross_domain_jumps_success_total"] == 1
    assert summary["cross_domain_jumps_blocked_total"] == 1
    assert summary["contribution_metrics"]["shared_layer_activation_rate"] == 0.5
    assert summary["contribution_metrics"]["jump_success_rate"] == 0.5
    assert summary["domain_pair_transition_frequency"]["enterprise->tax"] == 1
    assert summary["domain_pair_transition_frequency"]["enterprise->labor"] == 1
    assert summary["domain_pair_bridge_frequency"]["enterprise->tax::bridge_ent_tax_01"] == 1
