"""Layer 1 and Layer 2 question parse schemas (QA pipeline)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

UtteranceType = Literal["question", "command", "assertion", "unknown"]
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
    "unknown",
]
AssertionStatus = Literal["factual", "hypothetical", "unknown"]


class Layer1Parse(BaseModel):
    """Surface / linguistic parse (research demo)."""

    utterance_type: UtteranceType = "question"
    subject_text: str = ""
    condition_text: str = ""
    action_text: str = ""
    modality_text: str = ""
    time_text: str = ""
    exception_text: str = ""
    question_focus: QuestionFocus = "unknown"
    assertion_status: AssertionStatus = "unknown"
    raw_notes: list[str] = Field(default_factory=list)


class Layer2Parse(BaseModel):
    """Normalized logical sketch — not ground truth; verified by NeSy."""

    subject_normalized: str = "company_x"
    condition_atoms: list[str] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)
    goal: dict[str, Any] = Field(
        default_factory=lambda: {"predicate": "unknown", "args": []},
        description="Structured goal, e.g. obligation(subject, action, object)",
    )
    query_rule_candidate: str = ""
    diagnostics: dict[str, Any] = Field(default_factory=dict)
