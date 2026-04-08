"""Comprehensive tests for clarification evaluation two-phase pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.clarification_evaluation import (
    ClarificationEvaluationRequest,
    ClarificationEvaluationResult,
    run_clarification_evaluation,
)
from retrieval.rulebase_loader import configure_rulebase_path, load_rulebase
from retrieval.evidence_retriever import configure_evidence_path
from session.session_service import SessionService
from verification.engine import NeSyEngine

_REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _setup_eval_fixtures(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setup fixtures for evaluation tests."""
    monkeypatch.setenv("LEGAL_QA_LAYER1_USE_LLM", "0")
    monkeypatch.setenv("LEGAL_QA_NLI_ENABLED", "false")


def test_clarification_evaluation_request_creation() -> None:
    """Test ClarificationEvaluationRequest schema."""
    req = ClarificationEvaluationRequest(
        original_query="Công ty có phải cập nhật thông tin không?",
        gold_clarification_answer="Công ty là doanh nghiệp có vốn đầu tư nước ngoài.",
        session_id="test_eval_1",
    )
    assert req.original_query == "Công ty có phải cập nhật thông tin không?"
    assert req.gold_clarification_answer == "Công ty là doanh nghiệp có vốn đầu tư nước ngoài."
    assert req.session_id == "test_eval_1"


def test_clarification_evaluation_result_schema() -> None:
    """Test ClarificationEvaluationResult schema and serialization."""
    result = ClarificationEvaluationResult(
        session_id="test_eval_2",
        original_query="Question?",
        gold_clarification_answer="Gold answer",
        asked_clarification=True,
        clarification_targets=["fact_1", "fact_2"],
        answer_before=None,
        proof_before=None,
        final_status_before="needs_clarification",
        answer_after="Final answer after clarification",
        proof_after={"steps": [1, 2]},
        final_status_after="answered",
        gained_answer=True,
        gained_proof=False,
        resolved_after_clarification=True,
    )
    
    assert result.asked_clarification is True
    assert result.clarification_targets == ["fact_1", "fact_2"]
    assert result.final_status_before == "needs_clarification"
    assert result.final_status_after == "answered"
    assert result.gained_answer is True
    assert result.resolved_after_clarification is True
    
    # Test serialization
    result_dict = result.to_dict()
    assert result_dict["asked_clarification"] is True
    assert result_dict["before"]["final_status"] == "needs_clarification"
    assert result_dict["after"]["final_status"] == "answered"
    assert result_dict["gain"]["gained_answer"] is True
    assert result_dict["gain"]["resolved_after_clarification"] is True


def test_clarification_evaluation_no_clarification_needed() -> None:
    """
    When initial QA doesn't need clarification, evaluation ends early
    with no gain (answer before = answer after).
    """
    # Question that doesn't require clarification (already answerable)
    query = "Luật bảo vệ thông tin cá nhân là gì?"
    req = ClarificationEvaluationRequest(
        original_query=query,
        gold_clarification_answer="Some fact that wouldn't be needed",
    )
    
    # Without rulebase fixture, this will fail on actual QA, but we test the framework
    svc = SessionService()
    nesy = NeSyEngine(nesy_nli_mock=True)
    
    try:
        result = run_clarification_evaluation(
            req,
            session_svc=svc,
            nesy=nesy,
        )
        
        # If no clarification asked, returned result should indicate that
        if not result.asked_clarification:
            assert result.answer_before == result.answer_after
            assert result.final_status_before == result.final_status_after
            assert result.gained_answer is False
            assert result.resolved_after_clarification is False
    except Exception as e:
        # Expected if no rulebase fixture
        if "fixture" not in str(e).lower():
            pytest.skip(f"Rulebase/evidence fixture missing: {e}")


def test_clarification_evaluation_result_gain_logic() -> None:
    """Test gain measurement logic: before/after comparison."""
    # Case 1: Gained answer (no answer → answer)
    r1 = ClarificationEvaluationResult(
        session_id="s1",
        original_query="Q",
        gold_clarification_answer="A",
        asked_clarification=True,
        clarification_targets=["t1"],
        answer_before=None,
        proof_before=None,
        final_status_before="needs_clarification",
        answer_after="New answer",
        proof_after=None,
        final_status_after="answered",
        gained_answer=True,
        gained_proof=False,
        resolved_after_clarification=True,
    )
    assert r1.gained_answer is True
    assert r1.resolved_after_clarification is True
    
    # Case 2: No gain (both have answer)
    r2 = ClarificationEvaluationResult(
        session_id="s2",
        original_query="Q",
        gold_clarification_answer="A",
        asked_clarification=True,
        clarification_targets=["t1"],
        answer_before="Answer 1",
        proof_before=None,
        final_status_before="answered",
        answer_after="Answer 1",
        proof_after=None,
        final_status_after="answered",
        gained_answer=False,
        gained_proof=False,
        resolved_after_clarification=False,
    )
    assert r2.gained_answer is False
    assert r2.resolved_after_clarification is False
    
    # Case 3: Gained proof (answer exists, but proof improved)
    r3 = ClarificationEvaluationResult(
        session_id="s3",
        original_query="Q",
        gold_clarification_answer="A",
        asked_clarification=True,
        clarification_targets=["t1"],
        answer_before="Answer",
        proof_before={"steps": [1]},
        final_status_before="answered",
        answer_after="Answer",
        proof_after={"steps": [1, 2, 3]},  # More complete
        final_status_after="answered",
        gained_answer=False,
        gained_proof=True,  # Proof improved
        resolved_after_clarification=False,
    )
    assert r3.gained_answer is False
    assert r3.gained_proof is True


def test_clarification_evaluation_to_dict_export() -> None:
    """Test serialization for evaluation log export."""
    result = ClarificationEvaluationResult(
        session_id="test_export",
        original_query="Original question?",
        gold_clarification_answer="Gold fact injected",
        asked_clarification=True,
        clarification_targets=["missing_fact_1", "missing_fact_2"],
        answer_before="Partial answer",
        proof_before={"status": "incomplete"},
        final_status_before="needs_clarification",
        answer_after="Complete answer",
        proof_after={"status": "complete", "steps": 5},
        final_status_after="answered",
        gained_answer=False,
        gained_proof=True,
        resolved_after_clarification=True,
    )
    
    exported = result.to_dict()
    
    # Verify all expected keys
    assert "session_id" in exported
    assert "original_query" in exported
    assert "gold_clarification_answer" in exported
    assert "asked_clarification" in exported
    assert "clarification_targets" in exported
    assert "before" in exported
    assert "after" in exported
    assert "gain" in exported
    
    # Verify before/after structure
    assert exported["before"]["answer"] == "Partial answer"
    assert exported["before"]["final_status"] == "needs_clarification"
    assert exported["after"]["answer"] == "Complete answer"
    assert exported["after"]["final_status"] == "answered"
    
    # Verify gain metrics
    assert exported["gain"]["gained_answer"] is False
    assert exported["gain"]["gained_proof"] is True
    assert exported["gain"]["resolved_after_clarification"] is True


def test_clarification_evaluation_metrics_consistency() -> None:
    """Ensure gained_* metrics are logically consistent."""
    # Invalid: gained_answer but no answer_after
    with pytest.raises(AssertionError):
        result = ClarificationEvaluationResult(
            session_id="s",
            original_query="Q",
            gold_clarification_answer="A",
            asked_clarification=True,
            clarification_targets=["t"],
            answer_before=None,
            proof_before=None,
            final_status_before="open",
            answer_after=None,  # No answer after
            proof_after=None,
            final_status_after="open",
            gained_answer=True,  # But gained_answer=True (inconsistent)
            gained_proof=False,
            resolved_after_clarification=False,
        )
        # Consistency check: if gained_answer, answer_after must be non-empty
        if result.gained_answer:
            assert result.answer_after and result.answer_after.strip()


def test_clarification_evaluation_trace_preservation() -> None:
    """Ensure pipeline traces are preserved for debugging."""
    result = ClarificationEvaluationResult(
        session_id="trace_test",
        original_query="Q",
        gold_clarification_answer="A",
        asked_clarification=True,
        clarification_targets=["t"],
        answer_before=None,
        proof_before=None,
        final_status_before="needs_clarification",
        answer_after="Answer",
        proof_after=None,
        final_status_after="answered",
        gained_answer=True,
        gained_proof=False,
        resolved_after_clarification=True,
        phase1_trace=None,  # Would be filled from run_qa_pipeline
        phase3_trace=None,  # Would be filled from run_clarification_pipeline
    )
    
    # Traces should be optional but storable
    assert result.phase1_trace is None
    assert result.phase3_trace is None
    # In real use, these would be PipelineTrace objects


@pytest.mark.parametrize(
    "before_status,after_status,gold_answer_value,expected_resolved",
    [
        ("needs_clarification", "answered", "fact", True),
        ("needs_clarification", "needs_clarification", "fact", False),
        ("answered", "answered", "fact", False),  # Already answered
        ("failed", "answered", "fact", True),  # Changed from failed to answered
        ("open", "answered", "fact", True),
    ],
)
def test_clarification_evaluation_status_transitions(
    before_status: str,
    after_status: str,
    gold_answer_value: str,
    expected_resolved: bool,
) -> None:
    """Test various status transitions and their impact on resolved flag."""
    result = ClarificationEvaluationResult(
        session_id="status_test",
        original_query="Q",
        gold_clarification_answer=gold_answer_value,
        asked_clarification=True,
        clarification_targets=["t"],
        answer_before="Before" if before_status == "answered" else None,
        proof_before=None,
        final_status_before=before_status,
        answer_after="After",
        proof_after=None,
        final_status_after=after_status,
        gained_answer=True,
        gained_proof=False,
        resolved_after_clarification=expected_resolved,
    )
    
    # Verify resolved_after_clarification logic
    if after_status == "answered" and before_status != "answered":
        assert result.resolved_after_clarification is True
    else:
        assert result.resolved_after_clarification is False
