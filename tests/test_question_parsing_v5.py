"""Layer-1 / Layer-2 parsing v5: heuristic, normalizer mapping, orchestrator wiring."""

from __future__ import annotations

import pytest

from question_side.heuristic_layer1 import parse_question_layer1_heuristic
from question_side.question_normalizer import build_layer2
from question_side.question_parser import ParserUnavailableError, parse_question_layer1
from question_side.query_parser_v5 import parse as parse_query_v5
from runtime.qa_orchestrator import _parse_query_for_runtime
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


def test_regression_b2_unilateral_leave_slots() -> None:
    q = "Người lao động đơn phương nghỉ việc thì phải báo trước bao nhiêu ngày?"
    l1 = parse_question_layer1_heuristic(q)
    assert "người lao động" in l1.subject_text.lower()
    assert "đơn phương nghỉ việc" in l1.condition_text.lower()
    assert "báo trước" in l1.action_text.lower()
    assert l1.action_text.strip().lower() != q.strip().lower()


def test_regression_b29_when_termination_clause_split() -> None:
    q = "Khi chấm dứt hợp đồng lao động, doanh nghiệp phải thanh toán các khoản liên quan trong thời hạn bao lâu?"
    l1 = parse_question_layer1_heuristic(q)
    assert "chấm dứt hợp đồng" in l1.condition_text.lower()
    assert "doanh nghiệp" in l1.subject_text.lower()
    assert "thanh toán" in l1.action_text.lower()
    assert l1.time_text or l1.deadline_text
    assert l1.subject_text.strip().lower() != q.strip().lower()


def test_regression_b29_trial_period_multi_clause() -> None:
    q = "Trong thời gian thử việc, người lao động có được trả lương không, và tối thiểu là bao nhiêu?"
    l1 = parse_question_layer1_heuristic(q)
    assert "thử việc" in l1.condition_text.lower()
    assert "người lao động" in l1.subject_text.lower()
    assert "trả lương" in l1.action_text.lower()
    assert l1.question_focus in ("permission", "threshold", "deadline", "unknown")
    assert l1.subject_text.strip().lower() != q.strip().lower()


def test_regression_b29_overtime_clause_split() -> None:
    q = "Làm thêm giờ thì người lao động được trả lương như thế nào?"
    l1 = parse_question_layer1_heuristic(q)
    assert "làm thêm giờ" in l1.condition_text.lower()
    assert "người lao động" in l1.subject_text.lower()
    assert "trả lương" in l1.action_text.lower()
    assert l1.action_text.strip().lower() != q.strip().lower()


def test_regression_b6_permission_not_forced_to_obligation() -> None:
    q = "Doanh nghiệp có được đơn phương chấm dứt hợp đồng lao động với người đang nghỉ ốm không?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l1.question_focus == "permission"
    assert l2.goal.get("predicate") == "permission"
    assert l2.goal.get("args", ["", ""])[1] == "don_phuong_cham_dut_hop_dong_lao_dong"


def test_regression_b6_grounds_not_deadline() -> None:
    q = "Người sử dụng lao động có quyền xử lý kỷ luật sa thải trong những trường hợp nào?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l1.question_focus == "applicability"
    assert l2.goal.get("predicate") == "applies_if"
    assert l2.goal.get("args", ["", ""])[1] == "xu_ly_ky_luat_sa_thai"


def test_regression_b6_how_question_to_legal_effect_family() -> None:
    q = "Làm thêm giờ thì người lao động được trả lương như thế nào?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l1.question_focus == "legal_effect"
    assert l2.goal.get("predicate") == "legal_effect"
    assert l2.goal.get("args", ["", ""])[1] == "tra_luong"


def test_regression_b24_duration_limit_maps_threshold() -> None:
    q = "Thời gian thử việc tối đa đối với nhân viên chuyên môn kỹ thuật là bao lâu?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l1.question_focus == "threshold"
    assert l2.goal.get("predicate") == "threshold"
    assert l2.goal.get("args", [""])[0] == "duration_limit_thoi_gian_thu_viec"


def test_regression_b7_case_pattern_maps_to_applicability_not_deadline() -> None:
    q = "Trường hợp nào doanh nghiệp bị thu hồi giấy chứng nhận đăng ký doanh nghiệp?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l1.question_focus == "applicability"
    assert l2.goal.get("predicate") == "applies_if"


def test_regression_b7_case_pattern_for_dismissal_grounds() -> None:
    q = "Người sử dụng lao động có quyền xử lý kỷ luật sa thải trong những trường hợp nào?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l1.question_focus == "applicability"
    assert l2.goal.get("predicate") == "applies_if"
    assert l2.goal.get("args", ["", ""])[1] == "xu_ly_ky_luat_sa_thai"


def test_regression_b8_how_question_maps_to_legal_effect_not_obligation() -> None:
    q = "Làm thêm giờ thì người lao động được trả lương như thế nào?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l1.question_focus in ("legal_effect", "compensation_rule", "payment_obligation_explanation")
    assert l2.goal.get("predicate") == "legal_effect"
    assert l2.goal.get("args", ["", ""])[1] in ("tra_luong", "tra_luong_lam_them")


def test_regression_b8_tax_penalty_how_question_maps_to_legal_effect() -> None:
    q = "Doanh nghiệp chậm nộp tiền thuế thì có thể bị xử lý như thế nào?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l1.question_focus in ("legal_effect", "legal_consequence")
    assert l2.goal.get("predicate") == "legal_effect"


def test_regression_b9_duration_limit_not_deadline_schema() -> None:
    q = "Thời gian thử việc tối đa đối với nhân viên chuyên môn kỹ thuật là bao lâu?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l1.question_focus == "threshold"
    assert l2.goal.get("predicate") == "threshold"
    assert l2.goal.get("args", [""])[0].startswith("duration_limit")
    assert l2.goal.get("predicate") != "deadline"


def test_regression_b24_trial_period_permission_goal_canonical() -> None:
    q = "Trong thời gian thử việc, người lao động có được trả lương không, và tối thiểu là bao nhiêu?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l1.question_focus == "permission"
    assert l2.goal.get("predicate") == "permission"
    assert l2.goal.get("args", ["", ""])[1] == "tra_luong"
    assert len(l2.goal.get("args", ["", "", ""])[1]) < 32


def test_regression_b11_multi_intent_trial_period_preserves_secondary_threshold() -> None:
    q = "Trong thời gian thử việc, người lao động có được trả lương không, và tối thiểu là bao nhiêu?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])

    assert l1.parse_metadata.get("has_multi_intent") is True
    units = l1.parse_metadata.get("intent_units") or []
    assert len(units) >= 2
    assert units[0].get("focus") == "permission"
    assert units[1].get("focus") == "threshold"

    istruct = (l2.diagnostics or {}).get("intent_structure") or {}
    sub_goals = istruct.get("sub_goals") or []
    assert len(sub_goals) >= 2
    assert sub_goals[0].get("predicate") == "permission"
    assert sub_goals[1].get("predicate") == "threshold"


def test_regression_b10_overtime_payment_explanation_family() -> None:
    q = "Làm thêm giờ thì người lao động được trả lương như thế nào?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l1.question_focus in ("legal_effect", "compensation_rule", "payment_obligation_explanation")
    assert l2.goal.get("predicate") == "legal_effect"
    assert l2.goal.get("args", ["", ""])[1] in ("tra_luong", "tra_luong_lam_them")


def test_regression_b10_refund_eligibility_not_obligation_default() -> None:
    q = "Trường hợp nào doanh nghiệp được hoàn thuế giá trị gia tăng?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l1.question_focus in ("refund_eligibility", "applicability")
    assert l2.goal.get("predicate") == "applies_if"
    assert l2.goal.get("predicate") != "obligation"


def test_regression_b10_tax_cost_deduction_eligibility_not_obligation() -> None:
    q = "Chi phí tiền lương muốn được tính vào chi phí được trừ khi tính thuế thì cần điều kiện gì?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l1.question_focus in ("entitlement_rule", "applicability")
    assert l2.goal.get("predicate") == "applies_if"
    assert l2.goal.get("predicate") != "obligation"


def test_regression_b11_if_yes_then_condition_decomposes_intents() -> None:
    q = "Hộ kinh doanh có được chuyển đổi thành doanh nghiệp không, nếu có thì cần điều kiện gì?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])

    assert l1.parse_metadata.get("has_multi_intent") is True
    units = l1.parse_metadata.get("intent_units") or []
    assert len(units) >= 2
    assert units[0].get("focus") in ("permission", "applicability")
    assert units[1].get("focus") == "applicability"

    istruct = (l2.diagnostics or {}).get("intent_structure") or {}
    sub_goals = istruct.get("sub_goals") or []
    assert len(sub_goals) >= 2
    assert sub_goals[0].get("predicate") in ("permission", "applies_if")
    assert sub_goals[1].get("predicate") == "applies_if"


def test_regression_b11_how_and_when_keeps_two_structured_intents() -> None:
    q = "Tiền lương làm thêm giờ được tính như thế nào và trong trường hợp nào áp dụng?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])

    assert l1.parse_metadata.get("has_multi_intent") is True
    istruct = (l2.diagnostics or {}).get("intent_structure") or {}
    sub_goals = istruct.get("sub_goals") or []
    assert len(sub_goals) >= 2
    assert sub_goals[0].get("predicate") == "legal_effect"
    assert sub_goals[1].get("predicate") == "applies_if"


def test_regression_b3_actor_employer_not_company_x() -> None:
    q = "Người sử dụng lao động có phải tham gia bảo hiểm xã hội cho người lao động không?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l2.subject_type_guess == "employer"
    assert l2.subject_normalized == "employer_x"
    assert all("company_x" not in a for a in l2.condition_atoms)


def test_regression_b4_trial_period_condition_semantics() -> None:
    q = "Trong thời gian thử việc, người lao động có được trả lương không, và tối thiểu là bao nhiêu?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l2.subject_type_guess == "employee"
    assert l2.subject_normalized == "employee_x"
    assert any("trong_thoi_gian_thu_viec" in a for a in l2.condition_atoms)
    assert all("shareholder_context" not in a for a in l2.condition_atoms)


def test_regression_b5_labor_not_shareholder_for_unilateral_leave() -> None:
    q = "Người lao động đơn phương nghỉ việc thì phải báo trước bao nhiêu ngày?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l2.subject_type_guess == "employee"
    assert l2.subject_normalized == "employee_x"
    assert all("shareholder_context" not in a for a in l2.condition_atoms)


def test_regression_b5_labor_not_shareholder_for_contract_termination() -> None:
    q = "Khi chấm dứt hợp đồng lao động, doanh nghiệp phải thanh toán các khoản liên quan trong thời hạn bao lâu?"
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])
    assert l2.subject_type_guess in ("company", "enterprise")
    assert l2.subject_normalized in ("company_x", "enterprise_x")
    assert any("cham_dut_hop_dong_lao_dong" in a for a in l2.condition_atoms)
    assert all("shareholder_context" not in a for a in l2.condition_atoms)


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


def test_parser_mode_heuristic_only_metadata_honest(monkeypatch) -> None:
    monkeypatch.setenv("QUESTION_PARSER_MODE", "heuristic_only")
    monkeypatch.delenv("QUESTION_PARSER_ALLOW_FALLBACK", raising=False)
    monkeypatch.delenv("LEGAL_QA_LLM_API_KEY", raising=False)

    l1 = parse_question_layer1("Công ty có bắt buộc nộp báo cáo tài chính không?")
    assert l1.parse_metadata.get("requested_mode") == "heuristic_only"
    assert l1.parse_metadata.get("actual_mode") == "heuristic_fallback"
    assert l1.parse_metadata.get("parser_backend") == "heuristic"
    assert l1.parse_metadata.get("provider") == "heuristic"
    assert l1.parse_metadata.get("model") == "heuristic_layer1_v2"
    assert l1.parse_metadata.get("fallback_used") is False
    assert l1.parse_metadata.get("fallback_reason") == "heuristic_only_mode"
    assert l1.parse_metadata.get("parser_available") is False
    assert l1.parse_metadata.get("parser_error") is None


def test_verify_parse_runtime_smoke() -> None:
    l1 = parse_question_layer1_heuristic("Công ty có nghĩa vụ cập nhật thông tin cổ đông đúng hạn không?")
    l2 = build_layer2(l1, user_facts=[])
    eng = NeSyEngine(nesy_nli_mock=True)
    rec = eng.verify_parse(l1, l2, question_text="Công ty có nghĩa vụ cập nhật thông tin cổ đông đúng hạn không?")
    assert rec.mode == "parse_verification"
    assert rec.final_decision in ("ACCEPT", "REJECT", "REPAIR")


def test_parse_real_llm_success_metadata(monkeypatch) -> None:
    monkeypatch.setenv("QUESTION_PARSER_MODE", "llm_required")
    monkeypatch.setenv("QUESTION_PARSER_ALLOW_FALLBACK", "false")
    monkeypatch.setenv("LEGAL_QA_LLM_API_KEY", "fake-key")
    monkeypatch.setenv("LEGAL_QA_LLM_BASE_URL", "https://api.groq.com/openai/v1")
    monkeypatch.setenv("LEGAL_QA_LLM_MODEL", "llama-3.1-8b-instant")

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
                "requested_mode": "llm_required",
                "actual_mode": "llm_real",
                "provider": "api.groq.com",
                "model": "llama-3.1-8b-instant",
                "parser_available": True,
                "parser_error": None,
                "parser_prompt_version": "v5_layer1_slot_prompt_1",
                "parser_latency_ms": 10.5,
                "parser_backend_mode": "llm_real",
                "fallback_used": False,
            },
        )
        return l1, dict(l1.parse_metadata)

    monkeypatch.setattr("question_side.question_parser.parse_layer1_llm", _fake_parse_layer1_llm)
    l1 = parse_question_layer1("Công ty có phải nộp hồ sơ không?")

    assert l1.parse_metadata.get("parser_backend") == "llm"
    assert l1.parse_metadata.get("parser_provider") == "api.groq.com"
    assert l1.parse_metadata.get("parser_prompt_version") == "v5_layer1_slot_prompt_1"
    assert l1.parse_metadata.get("parser_backend_mode") == "llm_real"
    assert l1.parse_metadata.get("requested_mode") == "llm_required"
    assert l1.parse_metadata.get("actual_mode") == "llm_real"
    assert l1.parse_metadata.get("parser_available") is True
    assert l1.parse_metadata.get("parser_error") is None


def test_parser_mode_llm_required_missing_key_parse_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("QUESTION_PARSER_MODE", "llm_required")
    monkeypatch.setenv("QUESTION_PARSER_ALLOW_FALLBACK", "false")
    monkeypatch.delenv("LEGAL_QA_LLM_API_KEY", raising=False)

    with pytest.raises(ParserUnavailableError) as ex:
        parse_question_layer1("Công ty có phải nộp hồ sơ không?")
    assert ex.value.parse_metadata.get("requested_mode") == "llm_required"
    assert ex.value.parse_metadata.get("actual_mode") == "parse_unavailable"
    assert ex.value.parse_metadata.get("fallback_used") is False
    assert ex.value.parse_metadata.get("parser_available") is False
    assert ex.value.parse_metadata.get("parser_error") == "missing_api_key"


def test_parser_mode_prefer_llm_missing_key_uses_heuristic_fallback(monkeypatch) -> None:
    monkeypatch.setenv("QUESTION_PARSER_MODE", "prefer_llm")
    monkeypatch.setenv("QUESTION_PARSER_ALLOW_FALLBACK", "true")
    monkeypatch.delenv("LEGAL_QA_LLM_API_KEY", raising=False)

    l1 = parse_question_layer1("Công ty có phải nộp hồ sơ không?")
    assert l1.parse_metadata.get("requested_mode") == "prefer_llm"
    assert l1.parse_metadata.get("actual_mode") == "heuristic_fallback"
    assert l1.parse_metadata.get("fallback_used") is True
    assert l1.parse_metadata.get("fallback_reason") == "missing_api_key"
    assert l1.parse_metadata.get("parser_backend") == "heuristic"
    assert l1.parse_metadata.get("provider") == "heuristic"
    assert l1.parse_metadata.get("model") == "heuristic_layer1_v2"
    assert l1.parse_metadata.get("parser_available") is False
    assert l1.parse_metadata.get("parser_error") == "missing_api_key"


def test_query_parser_v5_unified_interface(monkeypatch) -> None:
    monkeypatch.setenv("QUESTION_PARSER_MODE", "llm_required")
    monkeypatch.setenv("QUESTION_PARSER_ALLOW_FALLBACK", "false")
    monkeypatch.setenv("LEGAL_QA_LLM_API_KEY", "fake-key")
    monkeypatch.setenv("LEGAL_QA_LLM_BASE_URL", "https://api.groq.com/openai/v1")
    monkeypatch.setenv("LEGAL_QA_LLM_MODEL", "llama-3.1-8b-instant")

    def _fake_parse_layer1_llm(*args, **kwargs):
        l1 = Layer1Parse(
            utterance_type="direct_question",
            subject_text="Doanh nghiệp",
            action_text="nộp báo cáo định kỳ",
            question_focus="obligation",
            assertion_status="ambiguous",
            parse_metadata={
                "parser_backend": "llm",
                "parser_provider": "api.groq.com",
                "parser_model": "llama-3.1-8b-instant",
                "requested_mode": "llm_required",
                "actual_mode": "llm_real",
                "provider": "api.groq.com",
                "model": "llama-3.1-8b-instant",
                "parser_available": True,
                "parser_error": None,
                "parser_backend_mode": "llm_real",
                "fallback_used": False,
            },
        )
        return l1, dict(l1.parse_metadata)

    monkeypatch.setattr("question_side.question_parser.parse_layer1_llm", _fake_parse_layer1_llm)
    l1, l2, meta = parse_query_v5("Doanh nghiệp có phải nộp báo cáo định kỳ không?", user_facts=["u1"])
    assert isinstance(l1, Layer1Parse)
    assert isinstance(l2, Layer2Parse)
    assert meta.get("query_parser_version") == "v5"
    assert meta.get("layer2_built") is True
    assert meta.get("parser_backend_mode") in ("llm_real", "heuristic_fallback", "parse_unavailable")


def test_runtime_parse_flags_mojibake_input_non_blocking(monkeypatch) -> None:
    monkeypatch.setenv("QUESTION_PARSER_MODE", "heuristic_only")
    bad = "Trong th?i gian th? vi?c, ng??i lao ??ng c? ???c tr? l??ng kh?ng?"

    l1, l2, meta = _parse_query_for_runtime(bad, user_facts=[])

    assert l1.parse_metadata.get("input_encoding_suspect") is True
    assert isinstance(l1.parse_metadata.get("input_encoding_diag"), dict)
    assert meta.get("input_encoding_suspect") is True

    enc = (l2.diagnostics or {}).get("encoding_hygiene") or {}
    assert enc.get("input_encoding_suspect") is True
    assert enc.get("classification") == "invalid_input_encoding"
