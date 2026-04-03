from __future__ import annotations

from verification.engine import NeSyEngine
from question_side.question_normalizer import build_layer2
from question_side.question_parser import parse_question_layer1


def test_parse_verification_accepts_typical_question():
    q = "Công ty tôi đổi người đại diện theo pháp luật thì có phải đăng ký thay đổi không?"
    l1 = parse_question_layer1(q)
    l2 = build_layer2(l1, user_facts=[])
    eng = NeSyEngine()
    rec = eng.verify_parse(l1, l2)
    assert rec.mode == "parse_verification"
    assert rec.final_decision in ("ACCEPT", "REPAIR", "REJECT")
