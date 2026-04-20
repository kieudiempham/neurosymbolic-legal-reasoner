from __future__ import annotations

from question_side.parse_clarify_apply import normalize_clarification_answers
from reasoning.clarification_manager import build_clarification_prompts_from_requirements
from schemas.reasoning import RequirementItem


def _build_prompts(keys: list[str], requirement_kind: str = "constraint") -> list[dict]:
    reqs = [
        RequirementItem(
            key=k,
            description="",
            predicate=None,
            args=[],
            requirement_kind=requirement_kind,
        )
        for k in keys
    ]
    return build_clarification_prompts_from_requirements(keys, reqs)


def test_placeholder_condition_not_exposed_to_user() -> None:
    prompts = _build_prompts(["condition()"], requirement_kind="positive")
    assert prompts
    p = prompts[0]
    assert p["fact_key"] == "legal_ground"
    assert p["source_fact_key"] == "condition()"
    assert "condition()" not in p["question_text"]
    assert p["expected_type"] == "short_text"


def test_placeholder_deadline_constraint_is_concrete_target() -> None:
    prompts = _build_prompts(["constraint:deadline:X"])
    p = prompts[0]
    assert p["fact_key"] == "deadline_anchor_event"
    assert p["source_fact_key"] == "constraint:deadline:X"
    assert "constraint:" not in p["question_text"]
    assert p["expected_type"] == "short_text"


def test_placeholder_threshold_constraint_is_concrete_target() -> None:
    prompts = _build_prompts(["constraint:threshold::::"])
    p = prompts[0]
    assert p["fact_key"] == "threshold_value"
    assert p["source_fact_key"] == "constraint:threshold::::"
    assert "constraint:" not in p["question_text"]
    assert p["expected_type"] == "number"


def test_normalize_answers_maps_public_key_back_to_internal_source() -> None:
    prompts = [
        {
            "fact_key": "deadline_anchor_event",
            "source_fact_key": "constraint:deadline:X",
            "expected_type": "short_text",
        }
    ]
    answers = [{"fact_key": "deadline_anchor_event", "value": "ngày chấm dứt hợp đồng"}]
    normalized = normalize_clarification_answers(answers, prompts)
    assert normalized == [
        {"fact_key": "constraint:deadline:X", "value": "ngày chấm dứt hợp đồng"}
    ]


def test_normalize_rejects_wrong_type_for_number() -> None:
    prompts = [
        {
            "fact_key": "threshold_value",
            "source_fact_key": "constraint:threshold::::",
            "expected_type": "number",
        }
    ]
    answers = [{"fact_key": "threshold_value", "value": "co"}]
    normalized = normalize_clarification_answers(answers, prompts)
    assert normalized == []


def test_normalize_rejects_wrong_type_for_date_and_duration() -> None:
    prompts = [
        {
            "fact_key": "deadline_date",
            "source_fact_key": "constraint:deadline:fixed",
            "expected_type": "date",
        },
        {
            "fact_key": "duration_limit",
            "source_fact_key": "constraint:threshold:duration_limit",
            "expected_type": "duration",
        },
    ]
    answers = [
        {"fact_key": "deadline_date", "value": "có"},
        {"fact_key": "duration_limit", "value": "ngày mai"},
    ]
    normalized = normalize_clarification_answers(answers, prompts)
    assert normalized == []


def test_normalize_choice_strict_to_options() -> None:
    prompts = [
        {
            "fact_key": "salary_minimum_basis",
            "source_fact_key": "constraint:threshold:salary",
            "expected_type": "choice",
            "options": ["luong_toi_thieu_vung", "luong_hop_dong"],
        }
    ]
    answers = [{"fact_key": "salary_minimum_basis", "value": "muc_luong_thoa_thuan"}]
    normalized = normalize_clarification_answers(answers, prompts)
    assert normalized == []
