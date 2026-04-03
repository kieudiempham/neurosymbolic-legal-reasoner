"""Rule objects loaded from rulebase_reasoning_core.json (QA pipeline)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RuleHead(BaseModel):
    predicate: str
    args: list[Any] = Field(default_factory=list)


class RuleRecord(BaseModel):
    rule_id: str
    logic_form: str
    head: RuleHead
    body: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    selected_for_reasoning: bool | None = None
    auxiliary_clauses: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def source_ref(self) -> str | None:
        prov = self.metadata.get("provenance") or {}
        return prov.get("source_ref")

    @property
    def source_ref_full(self) -> str | None:
        prov = self.metadata.get("provenance") or {}
        return prov.get("source_ref_full")
