"""Layer-1 / Layer-2 parsing v5: heuristic, normalizer mapping, orchestrator wiring."""

from __future__ import annotations

from question_side.heuristic_layer1 import parse_question_layer1_heuristic
from question_side.question_normalizer import build_layer2
from question_side.question_parser import parse_question_layer1
from schemas.question_parse import Layer1Parse, Layer2Parse
from verification.engine import NeSyEngine


def test_heuristic_conditional_utterance() -> None:
    l1 = parse_question_layer1_heuristic(
        "Nếu công ty chưa đăng ký thì có phải nộp hồ sơ bổ sung không?"
    )
    assert l1.utterance_type in ("conditional_legal_question", "hypothetical_question", "direct_question")
    assert l1.condition_text or l1.action_text


def test_heuristic_deadline_snippet() -> None:
    l1 = parse_question_layer1_heuristic("Thời hạn nộp hồ sơ là bao nhiêu ngày kể từ khi được thông báo?")
    assert l1.question_focus == "deadline" or l1.deadline_text or l1.time_text


def test_heuristic_exception_phrase() -> None:
    l1 = parse_question_layer1_heuristic("Trừ trường hợp đã được miễn, công ty có phải nộp không?")
    assert l1.question_focus == "exception" or l1.exception_text


def test_layer2_subject_type_not_only_company_x() -> None:
    l1 = Layer1Parse(
        subject_text="Cổ đông A",
        action_text="bán cổ phần",
        modality_text="được",
        question_focus="permission",
        assertion_status="hypothetical",
    )
    l2 = build_layer2(l1, user_facts=["fact_user_1"])
    assert l2.subject_type_guess in ("shareholder", "enterprise", "company", "unknown")
    assert l2.subject_normalized != ""


def test_assertion_hypothetical_no_asserted_fact_slug() -> None:
    l1 = Layer1Parse(
        subject_text="Công ty",
        condition_text="nếu chưa đăng ký",
        action_text="nộp hồ sơ",
        question_focus="obligation",
        assertion_status="hypothetical",
    )
    l2 = build_layer2(l1, user_facts=[])
    assert not any(x.startswith("asserted:") for x in l2.facts)
    assert l2.diagnostics.get("hypothetical_condition_refs")


def test_asserted_adds_condition_slug_fact() -> None:
    l1 = Layer1Parse(
        subject_text="DN",
        condition_text="đã đăng ký thay đổi",
        action_text="cập nhật",
        question_focus="obligation",
        assertion_status="asserted",
    )
    l2 = build_layer2(l1, user_facts=["u1"])
    assert any(x.startswith("asserted:") for x in l2.facts)


def test_query_rule_candidate_includes_utterance_and_atoms() -> None:
    l1 = Layer1Parse(
        utterance_type="direct_question",
        subject_text="Công ty X",
        action_text="đăng ký",
        question_focus="obligation",
        assertion_status="ambiguous",
    )
    l2 = build_layer2(l1, user_facts=[])
    assert "ut=" in l2.query_rule_candidate and "focus=" in l2.query_rule_candidate


def test_parse_facade_heuristic_preferred() -> None:
    l1 = parse_question_layer1("Công ty có bắt buộc nộp báo cáo tài chính không?", prefer_llm=False)
    assert l1.parse_metadata.get("parser_backend") == "heuristic"
    assert l1.parse_metadata.get("fallback_used") is False
    assert l1.parse_metadata.get("fallback_reason") == "prefer_heuristic"


def test_verify_parse_runtime_smoke() -> None:
    l1 = parse_question_layer1("Công ty có nghĩa vụ cập nhật thông tin cổ đông đúng hạn không?", prefer_llm=False)
    l2 = build_layer2(l1, user_facts=[])
    eng = NeSyEngine(nesy_nli_mock=True)
    rec = eng.verify_parse(l1, l2, question_text="Công ty có nghĩa vụ cập nhật thông tin cổ đông đúng hạn không?")
    assert rec.mode == "parse_verification"
    assert rec.final_decision in ("ACCEPT", "REJECT", "REPAIR")
