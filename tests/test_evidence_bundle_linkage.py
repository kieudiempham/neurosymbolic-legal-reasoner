from __future__ import annotations

from runtime.evidence_stage import build_evidence_bundle
from schemas.evidence import EvidenceSnippet
from schemas.proof import ProofObject, ProofStep
from schemas.reasoning import RequirementItem
from schemas.rule import RuleHead, RuleRecord
from verification.engine import NeSyEngine


def _rule() -> RuleRecord:
    return RuleRecord(
        rule_id="RULE_EVI_01",
        logic_form="obligation",
        head=RuleHead(predicate="obligation", args=["a", "b", "c"]),
        body=[],
        metadata={"provenance": {"domain": "enterprise"}},
    )


def test_evidence_bundle_links_subgoals_with_provenance() -> None:
    reqs = [RequirementItem(key="applies_if(a, eligible)", description="")]
    proof = ProofObject(
        proof_id="p1",
        conclusion="ok",
        derived_conclusion="ok",
        proof_steps=[
            ProofStep(
                step_id=1,
                description="check",
                fact_keys=["applies_if(a, eligible)"],
            )
        ],
    )
    snippets = [
        EvidenceSnippet(
            chunk_id="c1",
            text="Điều kiện applies_if(a, eligible) được nêu rõ trong Điều 10 khoản 2.",
            source_doc="LUAT-DN",
            article_clause="Điều 10 khoản 2",
            article="Điều 10",
            clause="khoản 2",
            score=0.91,
            source_ref="article=10",
            doc_id="doc_luat_dn",
        )
    ]

    bundle = build_evidence_bundle(
        query="Doanh nghiệp có đủ điều kiện không?",
        selected_rule=_rule(),
        requirement_set=reqs,
        proof=proof,
        snippets=snippets,
    )

    assert bundle.items
    item = bundle.items[0]
    assert item.evidence_id
    assert item.source_type == "corpus_chunk"
    assert item.article == "Điều 10"
    assert item.clause == "khoản 2"
    assert item.linked_subgoal == "applies_if(a, eligible)"
    assert item.support_score is not None
    assert bundle.linkage_map.get("applies_if(a, eligible)")


def test_answer_verifier_reads_same_evidence_bundle() -> None:
    bundle = build_evidence_bundle(
        query="q",
        selected_rule=_rule(),
        requirement_set=[],
        proof=None,
        snippets=[EvidenceSnippet(chunk_id="c1", text="text", score=0.2)],
    )

    eng = NeSyEngine(nesy_nli_mock=True)
    rec = eng.verify_answer(
        answer_text="Theo chứng cứ, kết luận là obligation(a,b,c).",
        conclusion="obligation(a,b,c)",
        proof={"proof_steps": [{"description": "x"}]},
        evidence_bundle=bundle.model_dump(mode="json"),
        modality_expected="",
        goal_action="b",
        action_token_in_answer="obligation(a,b,c)",
    )

    assert "evidence_bundle" in rec.normalized_inputs
    assert rec.normalized_inputs["evidence_bundle"].get("bundle_id") == bundle.bundle_id
