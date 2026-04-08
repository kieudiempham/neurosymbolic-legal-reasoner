"""Layer-1 / Layer-2 parsing v5: heuristic, normalizer mapping, orchestrator wiring."""

from __future__ import annotations

from question_side.heuristic_layer1 import parse_question_layer1_heuristic
from question_side.question_normalizer import build_layer2
from question_side.question_parser import parse_question_layer1
from question_side.query_parser_v5 import parse as parse_query_v5
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


def test_parse_real_llm_success_metadata(monkeypatch) -> None:
    monkeypatch.setenv("LEGAL_QA_LAYER1_USE_LLM", "1")
    monkeypatch.setenv("LEGAL_QA_LLM_API_KEY", "fake-key")

    def _fake_parse_layer1_llm(*args, **kwargs):
        l1 = Layer1Parse(
            utterance_type="direct_question",
            subject_text="Công ty",
            action_text="nộp hồ sơ",
            question_focus="obligation",
            assertion_status="ambiguous",
            parse_metadata={
                "parser_backend": "llm",
                "parser_provider": "api.groq.com",
                "parser_model": "llama-3.1-8b-instant",
                "parser_prompt_version": "v5_layer1_slot_prompt_1",
                "parser_latency_ms": 10.5,
                "parser_backend_mode": "real",
                "fallback_used": False,
            },
        )
        return l1, dict(l1.parse_metadata)

    monkeypatch.setattr("question_side.question_parser.parse_layer1_llm", _fake_parse_layer1_llm)
    l1 = parse_question_layer1("Công ty có phải nộp hồ sơ không?")

    assert l1.parse_metadata.get("parser_backend") == "llm"
    assert l1.parse_metadata.get("parser_provider") == "api.groq.com"
    assert l1.parse_metadata.get("parser_prompt_version") == "v5_layer1_slot_prompt_1"
    assert l1.parse_metadata.get("parser_backend_mode") == "real"
    assert l1.parse_metadata.get("fallback_used") is False


def test_parse_degraded_fallback_when_llm_provider_fails(monkeypatch) -> None:
    monkeypatch.setenv("LEGAL_QA_LAYER1_USE_LLM", "1")
    monkeypatch.setenv("LEGAL_QA_LLM_API_KEY", "fake-key")
    monkeypatch.setattr(
        "question_side.question_parser.parse_layer1_llm",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("api rate limit")),
    )

    l1 = parse_question_layer1("Công ty có phải nộp hồ sơ không?")
    assert l1.parse_metadata.get("parser_backend") == "heuristic"
    assert l1.parse_metadata.get("fallback_used") is True
    assert l1.parse_metadata.get("fallback_reason") == "llm_provider_error"
    assert l1.parse_metadata.get("parser_backend_mode") == "degraded"


def test_parse_malformed_output_classified_and_fallback(monkeypatch) -> None:
    monkeypatch.setenv("LEGAL_QA_LAYER1_USE_LLM", "1")
    monkeypatch.setenv("LEGAL_QA_LLM_API_KEY", "fake-key")
    monkeypatch.setattr(
        "question_side.question_parser.parse_layer1_llm",
        lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("layer1_llm_not_object")),
    )

    l1 = parse_question_layer1("Công ty có phải nộp hồ sơ không?")
    assert l1.parse_metadata.get("parser_backend") == "heuristic"
    assert l1.parse_metadata.get("fallback_used") is True
    assert l1.parse_metadata.get("fallback_reason") == "llm_malformed_output"
    assert l1.parse_metadata.get("parser_backend_mode") == "degraded"


def test_query_parser_v5_unified_interface(monkeypatch) -> None:
    monkeypatch.setenv("LEGAL_QA_LAYER1_USE_LLM", "0")
    l1, l2, meta = parse_query_v5("Doanh nghiệp có phải nộp báo cáo định kỳ không?", user_facts=["u1"])
    assert isinstance(l1, Layer1Parse)
    assert isinstance(l2, Layer2Parse)
    assert meta.get("query_parser_version") == "v5"
    assert meta.get("layer2_built") is True
    assert meta.get("parser_backend_mode") in ("fallback", "real", "degraded")
