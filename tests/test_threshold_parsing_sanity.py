from __future__ import annotations

from question_side.heuristic_layer1 import parse_question_layer1_heuristic
from question_side.question_normalizer import build_layer2
from utils.text import assert_clean_unicode_input


def _parse(question: str) -> tuple[str, dict[str, object], list[str], float]:
    assert_clean_unicode_input(question, where="threshold_sanity")
    l1 = parse_question_layer1_heuristic(question)
    l2 = build_layer2(l1, user_facts=[])
    cands = list(l1.parse_metadata.get("archetype_candidates", []))
    conf = float(l1.parse_metadata.get("archetype_confidence", 0.0))
    return l1.question_focus, l2.goal, cands, conf


def test_threshold_duration_limit_is_stable() -> None:
    q = "Thời gian thử việc tối đa đối với nhân viên chuyên môn kỹ thuật là bao lâu?"
    focus, goal, _cands, _conf = _parse(q)

    assert focus == "threshold"
    assert goal.get("predicate") == "threshold"
    assert str(goal.get("args", [""])[0]).startswith("duration_limit")
    assert goal.get("predicate") not in {"deadline", "obligation", "legal_effect"}


def test_threshold_capital_minimum_should_be_canonical_metric() -> None:
    q = "Vốn điều lệ tối thiểu để kinh doanh ngành X là bao nhiêu?"
    focus, goal, _cands, _conf = _parse(q)

    assert focus == "threshold"
    assert goal.get("predicate") == "threshold"
    assert goal.get("args", [""])[0] == "von_dieu_le"
    assert goal.get("predicate") not in {"deadline", "obligation", "legal_effect"}


def test_threshold_labor_count_should_not_drift_to_obligation() -> None:
    q = "Doanh nghiệp sử dụng từ bao nhiêu lao động thì phải thực hiện nghĩa vụ X?"
    focus, goal, _cands, _conf = _parse(q)

    assert focus == "threshold"
    assert goal.get("predicate") == "threshold"
    assert goal.get("args", [""])[0] == "so_lao_dong"
    assert goal.get("predicate") not in {"deadline", "obligation", "legal_effect"}


def test_threshold_revenue_floor_should_not_drift_to_obligation() -> None:
    q = "Doanh thu từ mức nào thì phải kê khai theo phương pháp Y?"
    focus, goal, _cands, _conf = _parse(q)

    assert focus == "threshold"
    assert goal.get("predicate") == "threshold"
    assert goal.get("args", [""])[0] == "doanh_thu"
    assert goal.get("predicate") not in {"deadline", "obligation", "legal_effect"}


def test_threshold_percentage_ownership_should_resolve_to_threshold() -> None:
    q = "Tỷ lệ sở hữu bao nhiêu phần trăm thì được quyền Z?"
    focus, goal, _cands, _conf = _parse(q)

    assert focus == "threshold"
    assert goal.get("predicate") == "threshold"
    assert goal.get("args", [""])[0] == "ty_le_so_huu"
    assert goal.get("predicate") not in {"deadline", "obligation", "legal_effect"}


def test_threshold_min_salary_percentage_should_resolve_to_threshold() -> None:
    q = "Người lao động trong thời gian thử việc được trả ít nhất bao nhiêu phần trăm mức lương của công việc đó?"
    focus, goal, _cands, _conf = _parse(q)

    assert focus == "threshold"
    assert goal.get("predicate") == "threshold"
    assert goal.get("args", [""])[0] == "ty_le_luong_thu_viec"
    assert goal.get("predicate") not in {"deadline", "obligation", "legal_effect"}
