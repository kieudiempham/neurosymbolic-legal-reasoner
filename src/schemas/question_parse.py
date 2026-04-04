"""Layer 1 and Layer 2 question parse schemas (QA pipeline) — v5-oriented dual layer."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# Legacy + v5 utterance kinds (keep "question" for backward compatibility)
UtteranceType = Literal[
    "question",
    "command",
    "assertion",
    "unknown",
    "direct_question",
    "conditional_legal_question",
    "hypothetical_question",
    "ambiguous_question",
]

QuestionFocus = Literal[
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
]

# Legacy "factual" kept; v5 prefers "asserted"
AssertionStatus = Literal["factual", "hypothetical", "unknown", "asserted", "ambiguous"]


class Layer1Parse(BaseModel):
    """Surface / linguistic parse — semantic slots (Layer 1)."""

    utterance_type: UtteranceType = "direct_question"
    subject_text: str = ""
    condition_text: str = ""
    action_text: str = ""
    modality_text: str = ""
    time_text: str = ""
    deadline_text: str = ""
    exception_text: str = ""
    question_focus: QuestionFocus = "unknown"
    assertion_status: AssertionStatus = "unknown"
    raw_notes: list[str] = Field(default_factory=list)
    """Parser metadata: parser_backend, parser_model, fallback_used, raw_llm_output, etc."""
    parse_metadata: dict[str, Any] = Field(default_factory=dict)


class Layer2Parse(BaseModel):
    """Normalized logical sketch — Layer 2; verified by NeSy."""

    subject_normalized: str = "company_x"
    subject_type_guess: str = "unknown"
    condition_atoms: list[str] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)
    goal: dict[str, Any] = Field(
        default_factory=lambda: {"predicate": "unknown", "args": []},
        description="Structured goal, e.g. obligation(subject, action, object)",
    )
    query_rule_candidate: str = ""
    diagnostics: dict[str, Any] = Field(default_factory=dict)
