"""Layer-1 semantic slots via OpenAI-compatible JSON (structured, no free-form answer)."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field, field_validator

from schemas.question_parse import (
    AssertionStatus,
    Layer1Parse,
    QuestionFocus,
    UtteranceType,
)

logger = logging.getLogger(__name__)

_SYSTEM = """Bạn là bộ trích xuất slot cho câu hỏi pháp luật (tiếng Việt).
Chỉ trả về MỘT object JSON duy nhất, không markdown, không giải thích.
Các key bắt buộc (chuỗi có thể rỗng nếu không có):
utterance_type, subject_text, condition_text, action_text, modality_text, time_text, deadline_text, exception_text, question_focus, assertion_status

Giá trị cho utterance_type (chọn một):
direct_question | conditional_legal_question | hypothetical_question | ambiguous_question

question_focus (chọn một):
obligation | permission | prohibition | deadline | threshold | exception | procedure | legal_consequence | applicability | dossier | legal_effect | authority | unknown

assertion_status (chọn một):
asserted | hypothetical | ambiguous
"""


class _LLMJsonLayer1(BaseModel):
    utterance_type: str = ""
    subject_text: str = ""
    condition_text: str = ""
    action_text: str = ""
    modality_text: str = ""
    time_text: str = ""
    deadline_text: str = ""
    exception_text: str = ""
    question_focus: str = "unknown"
    assertion_status: str = "ambiguous"


_UTTERANCE: tuple[str, ...] = (
    "direct_question",
    "conditional_legal_question",
    "hypothetical_question",
    "ambiguous_question",
    "question",
    "command",
    "assertion",
    "unknown",
)
_FOCUS: tuple[str, ...] = (
    "obligation",
    "permission",
    "prohibition",
    "deadline",
    "threshold",
    "exception",
    "applicability",
    "dossier",
    "legal_effect",
    "authority",
    "procedure",
    "legal_consequence",
    "unknown",
)
_ASSERT: tuple[str, ...] = ("asserted", "hypothetical", "ambiguous", "factual", "unknown")


def _coerce_ut(s: str) -> UtteranceType:
    t = (s or "").strip().lower().replace(" ", "_")
    if t in _UTTERANCE:
        return t  # type: ignore[return-value]
    return "direct_question"


def _coerce_focus(s: str) -> QuestionFocus:
    t = (s or "").strip().lower().replace(" ", "_")
    if t in _FOCUS:
        return t  # type: ignore[return-value]
    return "unknown"


def _coerce_assert(s: str) -> AssertionStatus:
    t = (s or "").strip().lower()
    if t == "factual":
        return "asserted"
    if t in _ASSERT:
        return t  # type: ignore[return-value]
    return "ambiguous"


def _extract_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if "```" in text:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
        if m:
            text = m.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            raise
        data = json.loads(m.group(0))
    if not isinstance(data, dict):
        raise ValueError("layer1_llm_not_object")
    return data


def parse_layer1_llm(
    question: str,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> tuple[Layer1Parse, dict[str, Any]]:
    """
    Returns (Layer1Parse, trace dict with raw_llm_output, parser_backend, parser_model).
    Raises on hard failure (caller falls back to heuristic).
    """
    key = (api_key or os.environ.get("LEGAL_QA_LLM_API_KEY") or os.environ.get("LLM_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("layer1_llm_no_api_key")

    base = (base_url or os.environ.get("LEGAL_QA_LLM_BASE_URL") or os.environ.get("LLM_BASE_URL") or "").strip()
    if not base:
        base = "https://api.groq.com/openai/v1"
    mdl = (model or os.environ.get("LEGAL_QA_LLM_MODEL") or os.environ.get("LLM_MODEL") or "").strip()
    if not mdl:
        mdl = "llama-3.1-8b-instant"

    client = OpenAI(api_key=key, base_url=base.rstrip("/"), timeout=90.0)
    user = f"Câu hỏi:\n{question.strip()}"
    resp = client.chat.completions.create(
        model=mdl,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.0,
        max_tokens=512,
    )
    raw = (resp.choices[0].message.content or "").strip()
    data = _extract_json(raw)
    parsed = _LLMJsonLayer1.model_validate({k: data.get(k, "") for k in _LLMJsonLayer1.model_fields})

    l1 = Layer1Parse(
        utterance_type=_coerce_ut(parsed.utterance_type),
        subject_text=parsed.subject_text.strip(),
        condition_text=parsed.condition_text.strip(),
        action_text=parsed.action_text.strip(),
        modality_text=parsed.modality_text.strip(),
        time_text=parsed.time_text.strip(),
        deadline_text=parsed.deadline_text.strip() or parsed.time_text.strip(),
        exception_text=parsed.exception_text.strip(),
        question_focus=_coerce_focus(parsed.question_focus),
        assertion_status=_coerce_assert(parsed.assertion_status),
        raw_notes=["llm_layer1_json"],
        parse_metadata={
            "parser_backend": "llm",
            "parser_model": mdl,
            "fallback_used": False,
            "raw_llm_output": raw[:8000],
        },
    )
    trace = dict(l1.parse_metadata)
    return l1, trace


def repair_layer1_slots_llm(
    question: str,
    previous: Layer1Parse,
    *,
    hint: str,
    diagnostic_codes: list[str],
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> tuple[Layer1Parse, dict[str, Any]]:
    """Re-ask LLM to fix slots given verification errors."""
    key = (api_key or os.environ.get("LEGAL_QA_LLM_API_KEY") or os.environ.get("LLM_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("layer1_llm_no_api_key")

    base = (base_url or os.environ.get("LEGAL_QA_LLM_BASE_URL") or "").strip() or "https://api.groq.com/openai/v1"
    mdl = (model or os.environ.get("LEGAL_QA_LLM_MODEL") or "").strip() or "llama-3.1-8b-instant"
    client = OpenAI(api_key=key, base_url=base.rstrip("/"), timeout=90.0)

    prev_json = previous.model_dump(mode="json", exclude={"parse_metadata", "raw_notes"})
    repair_sys = _SYSTEM + (
        "\nBạn đang SỬA parse trước đó. Giữ đúng schema JSON. "
        "Chỉ sửa các trường cần thiết theo gợi ý lỗi. "
        f"Lỗi: {diagnostic_codes}. Gợi ý: {hint}."
    )
    user = f"Câu hỏi gốc:\n{question.strip()}\n\nParse trước (JSON):\n{json.dumps(prev_json, ensure_ascii=False)}"
    resp = client.chat.completions.create(
        model=mdl,
        messages=[
            {"role": "system", "content": repair_sys},
            {"role": "user", "content": user},
        ],
        temperature=0.0,
        max_tokens=512,
    )
    raw = (resp.choices[0].message.content or "").strip()
    data = _extract_json(raw)
    parsed = _LLMJsonLayer1.model_validate({k: data.get(k, "") for k in _LLMJsonLayer1.model_fields})

    l1 = Layer1Parse(
        utterance_type=_coerce_ut(parsed.utterance_type),
        subject_text=parsed.subject_text.strip(),
        condition_text=parsed.condition_text.strip(),
        action_text=parsed.action_text.strip(),
        modality_text=parsed.modality_text.strip(),
        time_text=parsed.time_text.strip(),
        deadline_text=parsed.deadline_text.strip() or parsed.time_text.strip(),
        exception_text=parsed.exception_text.strip(),
        question_focus=_coerce_focus(parsed.question_focus),
        assertion_status=_coerce_assert(parsed.assertion_status),
        raw_notes=list(previous.raw_notes) + ["llm_layer1_slot_repair"],
        parse_metadata={
            "parser_backend": "llm_repair",
            "parser_model": mdl,
            "fallback_used": False,
            "raw_llm_output": raw[:8000],
            "repair_hint": hint,
            "diagnostic_codes": diagnostic_codes,
        },
    )
    return l1, dict(l1.parse_metadata)
