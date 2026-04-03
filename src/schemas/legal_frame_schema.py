"""Legal frame: structured normative content extracted from law text."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LegalFrame(BaseModel):
    """A frame capturing actors, actions, conditions, and deontic mode (per paper)."""

    frame_id: str
    source_doc_id: str
    span: tuple[int, int] | None = None
    actors: list[str] = Field(default_factory=list)
    action: str | None = None
    conditions: list[str] = Field(default_factory=list)
    deontic: str | None = None  # e.g. obligation, permission, prohibition
    raw_text: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
