"""v5 blocks: hybrid rule retrieval, typed clarification, BM25 evidence, grounded answer."""

from __future__ import annotations

from pathlib import Path

import pytest

from generation.answer_generator import generate_answer, safe_regenerate_answer
from reasoning.clarification_types import infer_target_kind, priority_for_kind
from retrieval.evidence_retriever import EvidenceRetriever
from retrieval.retrieval_query import build_evidence_retrieval_query, build_rule_retrieval_query
from retrieval.rule_retriever import retrieve_rules, rule_document_text
from retrieval.rulebase_loader import load_rulebase
from schemas.evidence import EvidenceSnippet
from schemas.proof import ProofObject, ProofStep
from schemas.question_parse import Layer1Parse, Layer2Parse

_REPO = Path(__file__).resolve().parents[1]
_CORE = _REPO / "data" / "processed" / "rulebase" / "doanhnghiep" / "rulebase_reasoning_core.json"
_EVIDENCE = _REPO / "data" / "corpus" / "evidence_chunks.json"


@pytest.fixture()
def rule_index():
    if not _CORE.is_file():
        pytest.skip("rulebase fixture missing")
    return load_rulebase(_CORE)


def test_rule_retrieval_query_uses_layer2_signals() -> None:
    l1 = Layer1Parse(
        subject_text="Công ty",
        action_text="nộp hồ sơ",
        modality_text="phải",
        question_focus="obligation",
        deadline_text="30 ngày",
        exception_text="trừ khi được miễn",
    )
    l2 = Layer2Parse(
        goal={"predicate": "obligation", "args": ["company_x", "nop_ho_so", "doi_tuong"]},
        condition_atoms=["nop_ho_so(company_x)"],
        subject_normalized="company_x",
        subject_type_guess="company",
    )
    q = build_rule_retrieval_query(l1, l2)
    assert "obligation" in q
    assert "company_x" in q
    assert "nop_ho_so" in q or "30" in q


def test_hybrid_rule_retrieval_score_breakdown(rule_index) -> None:
    l1 = Layer1Parse(
        subject_text="công ty",
        action_text="gửi phiếu lấy ý kiến",
        modality_text="được",
        question_focus="permission",
    )
    l2 = Layer2Parse(
        goal={"predicate": "permission", "args": ["company_x", "gui_phieu", "phieu_lay_y_kien"]},
        condition_atoms=[],
        subject_normalized="company_x",
    )
    ranked = retrieve_rules(layer1=l1, layer2=l2, top_k=6, index=rule_index)
    assert ranked
    _r, score, diag = ranked[0]
    assert diag.get("bm25_raw") is not None
    assert "structured_raw" in diag
    assert "matched_features" in diag
    assert "score_components" in diag
    assert score >= 0


def test_rule_document_text_non_empty(rule_index) -> None:
    rules = rule_index.all()
    if not rules:
        pytest.skip("empty rulebase")
    doc = rule_document_text(rules[0])
    assert len(doc) > 10


def test_clarification_typed_kinds() -> None:
    assert infer_target_kind("constraint:threshold:x", "constraint") == "missing_numeric_input"
    assert infer_target_kind("constraint:deadline:x", "constraint") == "missing_time_input"
    assert infer_target_kind("exception_applies(y)", None) == "missing_exception_check"
    assert priority_for_kind("missing_exception_check") < priority_for_kind("missing_fact")


def test_evidence_query_grounded_not_question_only() -> None:
    q = build_evidence_retrieval_query(
        question="test?",
        conclusion="ket_luan_A",
        proof_summary="buoc 1 buoc 2",
        goal={"predicate": "obligation", "args": ["a", "b"]},
        source_ref="Điều 149",
        rule_id="R1",
        modality_text="phải",
    )
    assert "ket_luan_A" in q
    assert "buoc 1" in q
    assert "R1" in q


def test_evidence_bm25_returns_snippets_with_breakdown() -> None:
    if not _EVIDENCE.is_file():
        pytest.skip("evidence corpus missing")
    er = EvidenceRetriever(_EVIDENCE)
    from schemas.rule import RuleHead, RuleRecord

    rule = RuleRecord(
        rule_id="RULE_LUATDN_D149_K4_E000117_H791FDF195CF0__e9bb79707b2c9c",
        logic_form="permission",
        head=RuleHead(predicate="permission", args=["x", "y", "z"]),
        body=[],
        metadata={"provenance": {"source_ref": "Điều 149"}},
    )
    ev = er.retrieve(
        question="cổ đông gửi phiếu",
        rule=rule,
        conclusion="duoc gui phieu",
        top_k=3,
        proof_summary="unify goal",
        goal={"predicate": "permission", "args": []},
        modality_text="được",
    )
    assert ev
    assert ev[0].score_breakdown
    assert "bm25_raw" in ev[0].score_breakdown


def test_template_answer_contains_conclusion_proof_evidence() -> None:
    proof = ProofObject(
        proof_id="p1",
        derived_conclusion="obligation holds",
        proof_steps=[
            ProofStep(step_id=1, description="Áp rule R: điều kiện đã đủ", rule_id="R1"),
        ],
    )
    ev = [
        EvidenceSnippet(
            chunk_id="c1",
            text="Điều luật minh họa.",
            article_clause="Điều 1 khoản 1",
            source_doc="Luật demo",
            score=0.9,
        )
    ]
    fa = generate_answer(
        question="Q?",
        conclusion="obligation holds",
        proof=proof,
        evidence=ev,
        goal_achieved=True,
    )
    assert "obligation holds" in fa.answer_text
    assert "Áp rule" in fa.answer_text or "rule" in fa.answer_text.lower()
    assert "Điều" in fa.answer_text or "minh họa" in fa.answer_text
    assert fa.generation_mode == "template_grounded"
    assert fa.proof_summary
    assert fa.legal_citations and fa.citation_spans
    assert "opening" in fa.answer_sections and "analysis" in fa.answer_sections


def test_safe_regenerate_uses_proof_evidence() -> None:
    p = ProofObject(proof_id="x", proof_steps=[ProofStep(step_id=1, description="step A", rule_id="r")])
    e = [EvidenceSnippet(chunk_id="1", text="ref", score=0.5)]
    t = safe_regenerate_answer("c", proof=p, evidence=e)
    assert "c" in t
    assert "step A" in t or "Cơ sở" in t


def test_pipeline_retrieval_connects_to_backward_types(rule_index) -> None:
    """Backward expects list[tuple[RuleRecord, float, dict]] — shape preserved."""
    l1 = Layer1Parse(question_focus="obligation", action_text="dang ky")
    l2 = Layer2Parse(goal={"predicate": "obligation", "args": ["c", "act", "o"]})
    ranked = retrieve_rules(layer1=l1, layer2=l2, top_k=4, index=rule_index)
    assert all(len(t) == 3 for t in ranked)
