"""Reasoning context: active domains and rulebases for multi-rulebase QA (phase 1)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReasoningContext:
    primary_domains: list[str] = field(default_factory=list)
    secondary_domains: list[str] = field(default_factory=list)
    active_rulebases: list[str] = field(default_factory=list)
    include_shared: bool = True
    question_time: str | None = None
    statute_ids: list[str] = field(default_factory=list)

    def to_trace_dict(self) -> dict:
        return {
            "primary_domains": list(self.primary_domains),
            "secondary_domains": list(self.secondary_domains),
            "active_rulebases": list(self.active_rulebases),
            "include_shared": self.include_shared,
            "question_time": self.question_time,
            "statute_ids": list(self.statute_ids),
        }
