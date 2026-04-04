"""Live LLM Layer-1 tests — skipped unless API key present."""

from __future__ import annotations

import os

import pytest

from question_side.llm_layer1_parser import parse_layer1_llm


@pytest.mark.llm_live
def test_live_parse_layer1_smoke() -> None:
    if not (os.environ.get("LEGAL_QA_LLM_API_KEY") or os.environ.get("LLM_API_KEY")):
        pytest.skip("no LLM API key")
    l1, meta = parse_layer1_llm("Công ty có bắt buộc lưu hồ sơ đăng ký thay đổi trong 10 năm không?")
    assert l1.subject_text or l1.action_text
    assert meta.get("parser_backend") == "llm"
