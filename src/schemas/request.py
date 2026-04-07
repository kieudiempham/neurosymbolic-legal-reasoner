"""HTTP-style request bodies for the QA API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ClarifyFactAnswer(BaseModel):
    fact_key: str
    value: bool | str | float | None = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User legal question (Vietnamese or mixed).")
    session_id: str | None = None
    user_facts: list[str] = Field(default_factory=list, description="Optional pre-declared fact strings.")
    domain: str | None = Field(
        default=None,
        description="Target domain: 'enterprise', 'tax', 'labor'. If None, use domain router."
    )
    use_router: bool = Field(
        default=True,
        description="If True and domain not specified, use domain router to select domain."
    )


class ClarifyRequest(BaseModel):
    session_id: str
    answers: list[ClarifyFactAnswer] = Field(default_factory=list)
