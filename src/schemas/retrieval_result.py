"""Structured retrieval results for multi-rulebase runtime (phase 2)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from schemas.rule import RuleRecord


class MultiRuleRetrievalPlan(BaseModel):
    """Planner input for AdvancedDomainRetriever."""

    primary_domains: list[str] = Field(default_factory=list)
    secondary_domains: list[str] = Field(default_factory=list)
    include_shared: bool = True
    allow_cross_domain_expansion: bool = False
    top_k_per_scope: int = 12
    top_k_final: int = 20
    statute_ids: list[str] = Field(default_factory=list)


class ScopedCandidate(BaseModel):
    """One ranked candidate with explicit retrieval scope."""

    rule_id: str
    retrieval_scope: str
    domain: str
    layer: str
    rulebase_id: str
    score: float
    score_components: dict[str, Any] = Field(default_factory=dict)
    matched_features: list[str] = Field(default_factory=list)
    extra_diag: dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def from_ranked_tuple(
        cls,
        rule: RuleRecord,
        score: float,
        diag: dict[str, Any],
        *,
        retrieval_scope: str,
    ) -> ScopedCandidate:
        d = dict(diag)
        return cls(
            rule_id=rule.rule_id,
            retrieval_scope=retrieval_scope,
            domain=str(d.get("domain") or ""),
            layer=str(d.get("layer") or ""),
            rulebase_id=str(d.get("rulebase_id") or ""),
            score=float(score),
            score_components=dict(d.get("score_components") or {}),
            matched_features=list(d.get("matched_features") or []),
            extra_diag={k: v for k, v in d.items() if k not in ("score_components", "matched_features", "domain", "layer", "rulebase_id")},
        )


class RetrievalScopeBlock(BaseModel):
    scope_name: str
    candidate_count: int
    top_score: float = 0.0


class RetrievalResult(BaseModel):
    """Per-scope retrieval + combined ranking (phase 2)."""

    plan: MultiRuleRetrievalPlan
    by_scope: dict[str, list[ScopedCandidate]] = Field(default_factory=dict)
    combined_ranking: list[ScopedCandidate] = Field(default_factory=list)
    cross_domain_expansion_applied: bool = False
    expansion_domains_used: list[str] = Field(default_factory=list)
