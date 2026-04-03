"""Executable rule representation for symbolic reasoning."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Rule(BaseModel):
    """A logic rule with optional metadata for traceability."""

    rule_id: str
    head: str
    body: list[str] = Field(default_factory=list)
    predicates: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)
