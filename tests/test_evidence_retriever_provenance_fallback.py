from __future__ import annotations

import json

from retrieval.evidence_retriever import EvidenceRetriever
from schemas.rule import RuleHead, RuleRecord


def _rule_with_provenance() -> RuleRecord:
    return RuleRecord(
        rule_id="R149_4",
        logic_form="obligation",
        head=RuleHead(predicate="obligation", args=["company_x", "nop_ho_so", "ho_so"]),
        body=[],
        metadata={
            "provenance": {
                "source_ref_full": "Điều 149 khoản 4",
                "source_ref": "article=149|clause=4",
                "source_text": "Doanh nghiệp phải hoàn tất thủ tục theo quy định tại Điều 149 khoản 4.",
                "doc_code": "LUAT_DN",
            }
        },
    )


def test_retriever_prefers_article_clause_alignment(tmp_path) -> None:
    corpus = [
        {
            "chunk_id": "c_match",
            "text": "Quy định chi tiết tại Điều 149 khoản 4 về thủ tục nộp hồ sơ.",
            "source_doc": "Luật Doanh nghiệp",
            "article_clause": "Điều 149 khoản 4",
            "rule_ids": ["R149_4"],
        },
        {
            "chunk_id": "c_noise",
            "text": "Nội dung không liên quan trực tiếp đến điều khoản đang hỏi.",
            "source_doc": "Luật Khác",
            "article_clause": "Điều 2 khoản 1",
            "rule_ids": ["R2"],
        },
    ]
    p = tmp_path / "evidence.json"
    p.write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")

    retriever = EvidenceRetriever(path=p)
    out = retriever.retrieve(
        question="Doanh nghiệp có phải nộp hồ sơ không?",
        rule=_rule_with_provenance(),
        conclusion="obligation(company_x, nop_ho_so, ho_so)",
        top_k=2,
    )

    assert out
    assert out[0].chunk_id == "c_match"


def test_retriever_adds_rule_provenance_when_no_article_match(tmp_path) -> None:
    corpus = [
        {
            "chunk_id": "c_other",
            "text": "Điều 88 khoản 1 nói về nội dung khác.",
            "source_doc": "Luật Doanh nghiệp",
            "article_clause": "Điều 88 khoản 1",
            "rule_ids": ["R88"],
        }
    ]
    p = tmp_path / "evidence.json"
    p.write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")

    retriever = EvidenceRetriever(path=p)
    out = retriever.retrieve(
        question="Khi nào phải công bố thông tin?",
        rule=_rule_with_provenance(),
        conclusion="obligation(company_x, cong_bo_thong_tin, bao_cao)",
        top_k=2,
    )

    assert out
    assert out[0].chunk_id.startswith("rule_provenance:")
    assert "Điều 149" in (out[0].article_clause or "") or "Điều 149" in out[0].text
