from __future__ import annotations

import pytest

from question_side.heuristic_layer1 import parse_question_layer1_heuristic
from question_side.question_normalizer import build_layer2
from utils.text import assert_clean_unicode_input, detect_mojibake


def test_utf8_vietnamese_input_parses_stably() -> None:
    q = "Trong thời gian thử việc, người lao động có được trả lương không, và tối thiểu là bao nhiêu?"
    assert_clean_unicode_input(q, where="utf8_test")
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])

    assert l1.question_focus in ("permission", "unknown")
    assert l2.goal.get("predicate") in ("permission", "unknown")


def test_ascii_no_diacritic_fallback_parses() -> None:
    q = "Trong thoi gian thu viec, nguoi lao dong co duoc tra luong khong, va toi thieu la bao nhieu?"
    assert_clean_unicode_input(q, where="ascii_fallback")
    l1 = parse_question_layer1_heuristic(q)
    l2 = build_layer2(l1, user_facts=[])

    assert l1.question_focus in ("permission", "unknown")
    assert l2.goal.get("predicate") in ("permission", "unknown")


def test_mojibake_input_is_flagged_not_silent_regression() -> None:
    bad = "Trong th?i gian th? vi?c, ng??i lao ??ng c? ???c tr? l??ng kh?ng, v? t?i thi?u l? bao nhi?u?"
    diag = detect_mojibake(bad)
    assert diag.get("is_mojibake") is True
    with pytest.raises(ValueError, match="mojibake|corrupted"):
        assert_clean_unicode_input(bad, where="mojibake_case")