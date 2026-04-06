"""Domain routing plan for retrieval and reasoning (phase 2)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class DomainRoutingPlan(BaseModel):
    """Output of domain selector — drives retrieval plan and cross-domain policy."""

    primary_domains: list[str] = Field(default_factory=list)
    secondary_domains: list[str] = Field(default_factory=list)
    include_shared: bool = True
    allow_cross_domain_expansion: bool = False
    shared_only: bool = False
    routing_confidence: float = 0.0
    routing_reasons: list[str] = Field(default_factory=list)
    triggered_bridges: list[str] = Field(default_factory=list)

    def to_selector_dict(self) -> dict[str, Any]:
        """Backward-compatible dict for older code expecting phase-1 shape."""
        return self.model_dump(mode="json")


def routing_plan_from_dict(d: dict[str, Any] | None) -> DomainRoutingPlan:
    if d is None:
        return DomainRoutingPlan(primary_domains=["enterprise"])
    keys = DomainRoutingPlan.model_fields.keys()
    filtered = {k: v for k, v in d.items() if k in keys}
    return DomainRoutingPlan.model_validate({**{"primary_domains": d.get("primary_domains") or ["enterprise"]}, **filtered})
