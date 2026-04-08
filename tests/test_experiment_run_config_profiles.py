from __future__ import annotations

from types import SimpleNamespace

import pytest

from runtime.experiment_run_config import ExperimentRunConfig, resolve_experiment_run_config
from runtime.qa_pipeline import run_clarification_pipeline, run_qa_pipeline, to_run_record
from schemas.http_response import AskResponse, ClarifyResponse
from verification.engine import NeSyEngine


PROFILE_NAMES = [
    "E0",
    "E1",
    "E2",
    "E3",
    "E4",
    "ablation_shared_off",
    "ablation_clarification_off",
    "ablation_repair_off",
    "ablation_backward_off",
]


class _FakeSessionService:
    def get(self, session_id: str) -> SimpleNamespace:
        return SimpleNamespace(original_question=f"question-for-{session_id}")


@pytest.mark.parametrize("profile_name", PROFILE_NAMES)
def test_run_qa_pipeline_profile_smoke(monkeypatch: pytest.MonkeyPatch, profile_name: str) -> None:
    captured: dict[str, object] = {}
    bootstrap_calls = {"count": 0}
    observed_eval_log: dict[str, object] = {}

    def fake_bootstrap(*, nesy=None, nli_verifier=None, settings=None):
        bootstrap_calls["count"] += 1
        return NeSyEngine(nesy_nli_mock=True), {"verifier_class": "NeSyEngine", "source": "fake_bootstrap"}

    def fake_run_ask(**kwargs):
        captured.update(kwargs)
        rc = kwargs["run_config"]
        assert isinstance(rc, ExperimentRunConfig)
        resp = AskResponse(
            session_id="sess-ask",
            needs_clarification=False,
            verification_trace=[],
            debug_trace={
                "query_text": kwargs["question"],
                "run_config": rc.to_trace_dict(),
            },
        )
        assert resp.evaluation_log is not None
        observed_eval_log.update(resp.evaluation_log.model_dump(mode="json"))
        return resp

    monkeypatch.setattr("runtime.qa_pipeline.resolve_pipeline_nesy_engine", fake_bootstrap)
    monkeypatch.setattr("runtime.qa_pipeline.run_ask", fake_run_ask)

    settings = SimpleNamespace(rule_retrieval_top_k=8, answer_reject_allow_fallback=False)
    expected = resolve_experiment_run_config(profile_name)
    qa = run_qa_pipeline(
        "test question",
        debug=False,
        settings=settings,
        run_config=profile_name,
    )

    assert qa.meta["run_config"]["profile_name"] == expected.profile_name
    assert observed_eval_log["run_config"] is not None
    assert observed_eval_log["run_config"]["enable_backward_chaining"] == expected.enable_backward_chaining
    assert captured["max_repair_attempts_parse"] == (2 if expected.enable_repair_loop else 0)
    assert captured["max_repair_attempts_answer"] == (2 if expected.enable_repair_loop else 0)
    assert captured["max_repair_attempts_rule"] == (2 if expected.enable_repair_loop else 0)
    assert captured["max_repair_attempts_backward"] == (1 if expected.enable_repair_loop else 0)
    assert captured["max_repair_attempts_forward"] == (1 if expected.enable_repair_loop else 0)
    if expected.enable_nli_verifier:
        assert bootstrap_calls["count"] == 1
        assert qa.meta["nli_runtime"]["source"] == "fake_bootstrap"
    else:
        assert bootstrap_calls["count"] == 0
        assert qa.meta["nli_runtime"]["source"] == "disabled_by_run_config"

    row = to_run_record(qa, qid="qid-1")
    assert row.run_config is not None
    assert row.run_config["profile_name"] == expected.profile_name


@pytest.mark.parametrize("profile_name", PROFILE_NAMES)
def test_run_clarification_pipeline_profile_smoke(monkeypatch: pytest.MonkeyPatch, profile_name: str) -> None:
    captured: dict[str, object] = {}
    bootstrap_calls = {"count": 0}
    observed_eval_log: dict[str, object] = {}

    def fake_bootstrap(*, nesy=None, nli_verifier=None, settings=None):
        bootstrap_calls["count"] += 1
        return NeSyEngine(nesy_nli_mock=True), {"verifier_class": "NeSyEngine", "source": "fake_bootstrap"}

    def fake_run_clarify(**kwargs):
        captured.update(kwargs)
        rc = kwargs["run_config"]
        assert isinstance(rc, ExperimentRunConfig)
        resp = ClarifyResponse(
            session_id=kwargs["session_id"],
            needs_clarification=False,
            verification_trace=[],
            debug_trace={
                "query_text": f"question-for-{kwargs['session_id']}",
                "run_config": rc.to_trace_dict(),
            },
        )
        assert resp.evaluation_log is not None
        observed_eval_log.update(resp.evaluation_log.model_dump(mode="json"))
        return resp

    monkeypatch.setattr("runtime.qa_pipeline.resolve_pipeline_nesy_engine", fake_bootstrap)
    monkeypatch.setattr("runtime.qa_pipeline.run_clarify", fake_run_clarify)

    settings = SimpleNamespace(rule_retrieval_top_k=8, answer_reject_allow_fallback=False)
    expected = resolve_experiment_run_config(profile_name)
    qa = run_clarification_pipeline(
        "sess-clarify",
        [{"fact_key": "x", "value": True}],
        debug=False,
        settings=settings,
        session_svc=_FakeSessionService(),
        run_config=profile_name,
    )

    assert qa.meta["run_config"]["profile_name"] == expected.profile_name
    assert observed_eval_log["run_config"] is not None
    assert observed_eval_log["run_config"]["enable_clarification"] == expected.enable_clarification
    assert captured["max_repair_attempts_parse"] == (2 if expected.enable_repair_loop else 0)
    assert captured["max_repair_attempts_backward"] == (1 if expected.enable_repair_loop else 0)
    if expected.enable_nli_verifier:
        assert bootstrap_calls["count"] == 1
        assert qa.meta["nli_runtime"]["source"] == "fake_bootstrap"
    else:
        assert bootstrap_calls["count"] == 0
        assert qa.meta["nli_runtime"]["source"] == "disabled_by_run_config"


def test_run_config_adapter_overrides_routing_and_policy() -> None:
    from runtime.cross_domain_policy import CrossDomainPolicy
    from schemas.domain_routing import DomainRoutingPlan

    rc = resolve_experiment_run_config("ablation_shared_off")
    routing = DomainRoutingPlan(
        primary_domains=["enterprise"],
        secondary_domains=["tax"],
        include_shared=True,
        allow_cross_domain_expansion=True,
        triggered_bridges=["bridge-1"],
    )
    policy = CrossDomainPolicy(
        allow_shared_to_domain=True,
        allow_primary_to_secondary=True,
        require_bridge_for_secondary_jump=True,
        max_cross_domain_hops=1,
    )

    routed = rc.apply_routing_plan(routing)
    gated = rc.apply_cross_domain_policy(policy)

    assert routed.include_shared is False
    assert routed.allow_cross_domain_expansion is True
    assert gated.allow_shared_to_domain is False
    assert gated.allow_primary_to_secondary is True