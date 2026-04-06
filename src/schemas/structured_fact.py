"""Structured facts for domain-aware reasoning (Chặng A) — parallel to legacy string keys in known_facts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

FactOrigin = Literal["user", "bridge", "derived", "unknown"]


class StructuredFact(BaseModel):
    """Minimum schema for logic-layer matching (not a second source of truth for rule bodies)."""

    fact_id: str
    predicate: str
    args: list[Any] = Field(default_factory=list)
    fact_origin: FactOrigin = "unknown"
    fact_domain: str = ""
    serialized_key: str = ""
    bridge_rule_id: str = ""
    triggering_fact_ids: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
