"""Sanity checks for Pydantic schemas."""

from __future__ import annotations

from schemas.legal_frame_schema import LegalFrame
from schemas.proof_schema import Proof, ProofStep
from schemas.question_schema import Layer1SemanticSlots, Layer2LogicObjects, SemanticSlot
from schemas.rule_schema import Rule


def test_question_layers_roundtrip() -> None:
    l1 = Layer1SemanticSlots(
        question_id="q1",
        raw_text="test",
        slots=[SemanticSlot(name="issue", value="tax")],
    )
    l2 = Layer2LogicObjects(question_id="q1", objects=[])
    assert l1.question_id == l2.question_id


def test_legal_frame_rule_proof() -> None:
    f = LegalFrame(frame_id="f1", source_doc_id="d1")
    r = Rule(rule_id="r1", head="holds(X)")
    p = Proof(proof_id="p1", steps=[ProofStep(step_id="s1", kind="fact", description="f")])
    assert f.frame_id and r.rule_id and p.proof_id
