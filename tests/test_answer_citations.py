"""Answer package: legal citations, spans, sections, PDF-oriented payload."""

from __future__ import annotations

from generation.answer_generator import (
    apply_answer_text_and_refresh_citations,
    generate_answer,
    safe_regenerate_final_answer,
)
from generation.legal_citations import build_legal_citations_from_evidence, format_citation_display_label
from schemas.evidence import EvidenceSnippet
from schemas.proof import ProofObject, ProofStep
from schemas.rule import RuleHead, RuleRecord


def test_format_citation_display_label() -> None:
    s = format_citation_display_label(
        article_clause="Điều 13 khoản 2",
        article=None,
        clause=None,
        point=None,
        source_doc="Luật Doanh nghiệp 2014",
    )
    assert "Điều 13" in s
    assert "Luật" in s


def test_build_citations_from_evidence_has_excerpt_and_pdf_payload() -> None:
    ev = [
        EvidenceSnippet(
            chunk_id="c1",
            text="Người đại diện theo pháp luật là cá nhân đại diện cho doanh nghiệp (demo).",
            article_clause="Điều 13",
            source_doc="Luật Doanh nghiệp (demo stub)",
            doc_id="luat_dn_demo",
            source_ref="Điều 13",
            page=12,
            score=0.9,
        )
    ]
    cites = build_legal_citations_from_evidence(ev, rule=None)
    assert len(cites) == 1
    c = cites[0]
    assert c.citation_id == "cit_1"
    assert c.excerpt
    assert c.open_pdf_payload is not None
    assert c.open_pdf_payload.doc_id == "luat_dn_demo"
    assert c.open_pdf_payload.page == 12
    assert c.pdf_anchor is not None
    assert c.pdf_anchor.page == 12
    assert f"[{c.display_label}]" in f"x [{c.display_label}] y"


def test_template_answer_structure_and_citation_spans() -> None:
    proof = ProofObject(
        proof_id="p1",
        derived_conclusion="permission holds",
        proof_steps=[
            ProofStep(step_id=1, description="Áp rule R: điều kiện đã đủ", rule_id="R1"),
        ],
    )
    ev = [
        EvidenceSnippet(
            chunk_id="c1",
            text="Điều luật minh họa ngắn.",
            article_clause="Điều 1 khoản 1",
            source_doc="Luật demo",
            score=0.9,
        )
    ]
    fa = generate_answer(
        question="Q?",
        conclusion="permission holds",
        proof=proof,
        evidence=ev,
        goal_achieved=True,
    )
    assert "Kính gửi" in fa.answer_text or "Cảm ơn" in fa.answer_text
    assert "Về nguyên tắc" in fa.answer_text
    assert "Tuy nhiên" in fa.answer_text or "Trân trọng" in fa.answer_text
    assert "permission holds" in fa.answer_text
    assert "Áp rule" in fa.answer_text or "rule" in fa.answer_text.lower()
    assert fa.answer_sections.get("opening")
    assert fa.answer_sections.get("analysis")
    assert fa.legal_citations
    assert any("Điều" in c.display_label for c in fa.legal_citations)
    assert fa.citation_spans, "spans map bracket labels to citation_id"
    assert fa.citation_spans[0].citation_id == "cit_1"


def test_citation_from_rule_when_evidence_empty() -> None:
    rule = RuleRecord(
        rule_id="R_TEST",
        logic_form="permission",
        head=RuleHead(predicate="p", args=[]),
        body=[],
        metadata={
            "provenance": {
                "source_ref_full": "Điều 149 khoản 4",
                "source_ref": "article=149|clause=4",
                "source_text": "Văn bản gốc minh họa cho kiểm thử.",
            }
        },
    )
    cites = build_legal_citations_from_evidence([], rule=rule)
    assert len(cites) == 1
    assert cites[0].excerpt or cites[0].source_ref


def test_apply_answer_text_refresh_spans() -> None:
    from generation.legal_citations import link_answer_text_to_citations

    ev = [
        EvidenceSnippet(
            chunk_id="x",
            text="t",
            article_clause="Điều 5",
            source_doc="Luật X",
            score=1.0,
        )
    ]
    fa = generate_answer(
        question="q",
        conclusion="c",
        proof=None,
        evidence=ev,
        goal_achieved=True,
    )
    apply_answer_text_and_refresh_citations(fa, fa.answer_text)
    assert fa.citation_spans == link_answer_text_to_citations(fa.answer_text, fa.legal_citations)


def test_safe_regenerate_final_keeps_citations() -> None:
    ev = [
        EvidenceSnippet(
            chunk_id="z",
            text="ref",
            article_clause="Điều 2",
            source_doc="Luật Y",
            score=0.5,
        )
    ]
    fa = safe_regenerate_final_answer("concl", evidence=ev, goal_achieved=True)
    assert fa.legal_citations
    assert fa.citation_spans is not None
    assert "concl" in fa.answer_text
