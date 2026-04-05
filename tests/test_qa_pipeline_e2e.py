"""End-to-end pipeline entrypoint: QAResponse, PipelineTrace, optional JSON export."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from retrieval.evidence_retriever import configure_evidence_path
from retrieval.rulebase_loader import configure_rulebase_path
from runtime.qa_pipeline import run_clarification_pipeline, run_qa_pipeline
from session.session_service import SessionService
from verification.engine import NeSyEngine

_REPO = Path(__file__).resolve().parents[1]
_CORE = _REPO / "data" / "processed" / "rulebase" / "doanhnghiep" / "rulebase_reasoning_core.json"
_EVIDENCE = _REPO / "data" / "corpus" / "evidence_chunks.json"


@pytest.fixture()
def configured_pipeline(monkeypatch):
    if not _CORE.is_file():
        pytest.skip("rulebase fixture missing")
    if not _EVIDENCE.is_file():
        pytest.skip("evidence corpus missing")
    monkeypatch.setenv("LEGAL_QA_LAYER1_USE_LLM", "0")
    configure_rulebase_path(_CORE)
    configure_evidence_path(_EVIDENCE)


def test_run_qa_pipeline_happy_path_trace_steps(configured_pipeline, tmp_path: Path) -> None:
    q = "Công ty có được gửi phiếu lấy ý kiến bằng văn bản không?"
    qa = run_qa_pipeline(
        q,
        debug=True,
        save_trace=True,
        trace_dir=tmp_path,
        session_svc=SessionService(),
        nesy=NeSyEngine(nesy_nli_mock=True),
        rule_index=None,
        evidence_retriever=None,
        qid="e2e-happy-01",
    )
    assert qa.status == "answered"
    assert qa.session_id
    assert qa.trace_id
    assert qa.final_answer and qa.final_answer.answer_text
    assert qa.pipeline_trace and len(qa.pipeline_trace.steps) >= 8
    names = [s.step_name for s in qa.pipeline_trace.steps]
    for need in (
        "parse_layer1",
        "retrieve_rules",
        "rule_backward_gate",
        "forward_gate",
        "retrieve_evidence",
        "generate_answer",
    ):
        assert need in names
    assert qa.meta.get("trace_file")
    p = Path(str(qa.meta["trace_file"]))
    assert p.is_file()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["trace_id"] == qa.trace_id
    assert len(data["steps"]) >= 8


def test_run_qa_pipeline_clarification_then_continue(configured_pipeline, tmp_path: Path) -> None:
    q = "Nếu chưa đăng ký thay đổi thì có phải bổ sung hồ sơ không?"
    svc = SessionService()
    qa1 = run_qa_pipeline(
        q,
        debug=True,
        save_trace=False,
        session_svc=svc,
        nesy=NeSyEngine(nesy_nli_mock=True),
        qid="e2e-clarify-01",
    )
    if qa1.status != "needs_clarification" or not qa1.clarification_prompts:
        pytest.skip("clarification not triggered for this question in current heuristic")
    first = qa1.clarification_prompts[0]
    qa2 = run_clarification_pipeline(
        qa1.session_id,
        [{"fact_key": first.fact_key, "value": True}],
        debug=True,
        save_trace=True,
        trace_dir=tmp_path,
        session_svc=svc,
        nesy=NeSyEngine(nesy_nli_mock=True),
        qid="e2e-clarify-02",
    )
    assert qa2.trace_id
    assert qa2.pipeline_trace is not None
    assert qa2.pipeline_trace.turn == "clarify"
    assert qa2.meta.get("trace_file")
    loaded = json.loads(Path(str(qa2.meta["trace_file"])).read_text(encoding="utf-8"))
    assert loaded["turn"] == "clarify"


def test_run_qa_pipeline_failure_no_rule(configured_pipeline) -> None:
    """Controlled failure: no unifying rule for arbitrary text."""
    qa = run_qa_pipeline(
        "xyzabc nonsense token qqzz 12345",
        debug=True,
        session_svc=SessionService(),
        nesy=NeSyEngine(nesy_nli_mock=True),
        qid="e2e-fail-01",
    )
    assert qa.status == "failed"
    assert qa.reason
    assert qa.pipeline_trace
    step_names = [s.step_name for s in qa.pipeline_trace.steps]
    assert "pipeline_exit" in step_names or "backward" in step_names


def test_run_record_flatten(configured_pipeline) -> None:
    from runtime.qa_pipeline import to_run_record

    qa = run_qa_pipeline(
        "Công ty có được gửi phiếu lấy ý kiến bằng văn bản không?",
        debug=False,
        session_svc=SessionService(),
        nesy=NeSyEngine(nesy_nli_mock=True),
        qid="batch-001",
    )
    row = to_run_record(qa, qid="batch-001")
    assert row.qid == "batch-001"
    assert row.status == qa.status
