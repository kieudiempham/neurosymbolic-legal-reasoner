from __future__ import annotations

from reasoning.proof_builder import build_proof
from reasoning.semantics.forward_engine import run_forward_path
from schemas.rule import RuleHead, RuleRecord


def _rule(
    rule_id: str,
    *,
    logic_form: str,
    head_predicate: str,
    head_args: list[str] | None = None,
    body: list[dict[str, object]] | None = None,
    shared: bool = False,
) -> RuleRecord:
    metadata = {"domain": "shared", "layer": "shared"} if shared else {"domain": "enterprise", "layer": "domain"}
    return RuleRecord(
        rule_id=rule_id,
        logic_form=logic_form,
        head=RuleHead(predicate=head_predicate, args=head_args or []),
        body=body or [],
        metadata=metadata,
    )


def test_shared_rule_unknown_head_is_blocked_early() -> None:
    rule = _rule(
        "shared_motif_weak_1",
        logic_form="unknown",
        head_predicate="unknown",
        shared=True,
    )

    res = run_forward_path(
        rule=rule,
        goal={"predicate": "obligation", "args": ["company_x", "nop_ho_so"]},
        known_facts={},
        substitution={},
    )

    assert not res.goal_reached
    assert res.failure_reason in {"unknown_rule_head", "weak_shared_template"}
    assert not res.proof_steps


def test_unknown_goal_atom_fails_with_structured_reason() -> None:
    rule = _rule(
        "RULE_OK_HEAD",
        logic_form="obligation",
        head_predicate="obligation",
        head_args=["company_x", "nop_ho_so"],
        body=[{"predicate": "applies_if", "args": ["company_x", "eligible"]}],
    )

    res = run_forward_path(
        rule=rule,
        goal={"predicate": "unknown", "args": ["company_x", "nop_ho_so"]},
        known_facts={},
        substitution={},
    )

    assert not res.goal_reached
    assert res.failure_reason == "unknown_goal_atom"
    assert not res.proof_steps


def test_noncanonical_surface_goal_is_rejected_by_quality_gate() -> None:
    rule = _rule(
        "RULE_CANONICAL",
        logic_form="obligation",
        head_predicate="obligation",
        head_args=["company_x", "nop_ho_so"],
    )

    res = run_forward_path(
        rule=rule,
        goal={
            "predicate": "Doanh nghiệp có bắt buộc phải nộp hồ sơ đúng hạn theo quy định hiện hành hay không",
            "args": ["company_x", "nop_ho_so"],
        },
        known_facts={},
        substitution={},
    )

    assert not res.goal_reached
    assert res.failure_reason == "noncanonical_goal_surface"


def test_predicate_family_mismatch_has_specific_reason() -> None:
    rule = _rule(
        "RULE_DEADLINE",
        logic_form="deadline",
        head_predicate="deadline",
        head_args=["company_x", "nop_ho_so"],
    )

    res = run_forward_path(
        rule=rule,
        goal={"predicate": "obligation", "args": ["company_x", "nop_ho_so"]},
        known_facts={},
        substitution={},
    )

    assert not res.goal_reached
    assert res.failure_reason == "predicate_family_mismatch"


def test_failed_quality_gate_proof_is_not_grounded_looking() -> None:
    rule = _rule(
        "shared_motif_weak_2",
        logic_form="unknown",
        head_predicate="unknown",
        shared=True,
    )

    res = run_forward_path(
        rule=rule,
        goal={"predicate": "obligation", "args": ["company_x", "nop_ho_so"]},
        known_facts={},
        substitution={},
    )
    assert not res.goal_reached

    proof = build_proof(
        rule=rule,
        used_facts=[],
        conclusion="",
        forward_result=res.model_dump(mode="json"),
        requirement_artifact=None,
    )

    assert proof.proof_steps
    assert proof.proof_steps[0].step_type == "forward_failure"
    assert proof.fail_stage in {"runtime_quality_gate", "unification_gate"}
    assert not any((step.conclusion or {}).get("kind") == "final" for step in proof.proof_steps)
