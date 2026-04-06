"""Reasoning context: active domains, rulebases, and policy snapshot (phase 2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.cross_domain_policy import CrossDomainPolicy


@dataclass
class ReasoningContext:
    primary_domains: list[str] = field(default_factory=list)
    secondary_domains: list[str] = field(default_factory=list)
    active_rulebases: list[str] = field(default_factory=list)
    include_shared: bool = True
    question_time: str | None = None
    statute_ids: list[str] = field(default_factory=list)
    cross_domain_policy: CrossDomainPolicy | None = None
    triggered_bridges: list[str] = field(default_factory=list)

    def to_trace_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "primary_domains": list(self.primary_domains),
            "secondary_domains": list(self.secondary_domains),
            "active_rulebases": list(self.active_rulebases),
            "include_shared": self.include_shared,
            "question_time": self.question_time,
            "statute_ids": list(self.statute_ids),
            "triggered_bridges": list(self.triggered_bridges),
        }
        if self.cross_domain_policy:
            out["cross_domain_policy"] = self.cross_domain_policy.to_trace_dict()
        return out
