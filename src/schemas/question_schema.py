"""Question-side representations: layer-1 semantic slots and layer-2 logical objects."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SemanticSlot(BaseModel):
    """A single semantic slot (layer 1), e.g. role, issue, time span."""

    name: str
    value: str | None = None
    span: tuple[int, int] | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class Layer1SemanticSlots(BaseModel):
    """Layer 1: shallow semantic slots extracted from the user question."""

    question_id: str
    raw_text: str
    slots: list[SemanticSlot] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class LogicObject(BaseModel):
    """A normalized logical object (layer 2), e.g. obligation, fact query."""

    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)


class Layer2LogicObjects(BaseModel):
    """Layer 2: structured logical objects feeding retrieval and reasoning."""

    question_id: str
    objects: list[LogicObject] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
