"""Per-scope retrieval then controlled merge — phase 2 (not single merged-pool facade)."""

from __future__ import annotations

import logging
from typing import Any

from schemas.domain_routing import DomainRoutingPlan
from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.retrieval_result import MultiRuleRetrievalPlan, RetrievalResult, ScopedCandidate
from schemas.rule import RuleRecord
from retrieval.domain_scoped_retriever import enrich_ranked_with_retrieval_meta
from retrieval.rule_retriever import retrieve_rules
from retrieval.rulebase_loader import RulebaseIndex
from rulebase.rulebase_registry import RulebaseRegistry

logger = logging.getLogger(__name__)


def _dedupe_best_score(
    items: list[tuple[RuleRecord, float, dict[str, Any]]],
) -> list[tuple[RuleRecord, float, dict[str, Any]]]:
    best: dict[str, tuple[RuleRecord, float, dict[str, Any]]] = {}
    for r, s, d in items:
        cur = best.get(r.rule_id)
        if cur is None or s > cur[1]:
            best[r.rule_id] = (r, s, d)
    return sorted(best.values(), key=lambda x: -x[1])


class AdvancedDomainRetriever:
    """
    Runs ``retrieve_rules`` **per scope** (shared / each domain index), tags scope, merges with dedupe.
    """

    def __init__(self, registry: RulebaseRegistry) -> None:
        self._registry = registry

    def build_plan_from_routing(self, routing: DomainRoutingPlan, top_k_final: int = 20) -> MultiRuleRetrievalPlan:
        return MultiRuleRetrievalPlan(
            primary_domains=list(routing.primary_domains),
            secondary_domains=list(routing.secondary_domains),
            include_shared=routing.include_shared,
            allow_cross_domain_expansion=routing.allow_cross_domain_expansion,
            top_k_per_scope=max(8, min(20, top_k_final)),
            top_k_final=top_k_final,
        )

    def retrieve(
        self,
        layer1: Layer1Parse,
        layer2: Layer2Parse,
        routing: DomainRoutingPlan,
        *,
        top_k_final: int = 20,
    ) -> tuple[RetrievalResult, list[tuple[RuleRecord, float, dict[str, Any]]], RulebaseIndex]:
        plan = self.build_plan_from_routing(routing, top_k_final=top_k_final)
        by_scope: dict[str, list[ScopedCandidate]] = {}
        pooled: list[tuple[RuleRecord, float, dict[str, Any], str]] = []
        expansion_done = False
        expansion_used: list[str] = []

        def run_scope(scope_name: str, index: RulebaseIndex | None) -> None:
            if index is None or not index.rules:
                by_scope[scope_name] = []
                return
            ranked = retrieve_rules(
                layer1=layer1,
                layer2=layer2,
                top_k=plan.top_k_per_scope,
                index=index,
            )
            ranked = enrich_ranked_with_retrieval_meta(ranked)
            sc_list: list[ScopedCandidate] = []
            for r, s, d in ranked:
                d2 = dict(d)
                d2["retrieval_scope"] = scope_name
                pooled.append((r, s, d2, scope_name))
                sc_list.append(ScopedCandidate.from_ranked_tuple(r, s, d2, retrieval_scope=scope_name))
            by_scope[scope_name] = sc_list

        if plan.include_shared and self._registry.get_shared():
            run_scope("shared", self._registry.get_shared())

        for dom in plan.primary_domains:
            idx = self._registry.get_domain_rulebase(dom)
            if idx is None:
                logger.warning("[retrieve] primary domain %r not loaded — skipping scope", dom)
                by_scope.setdefault(dom, [])
                continue
            run_scope(dom, idx)

        if plan.allow_cross_domain_expansion and plan.secondary_domains:
            expansion_done = True
            for dom in plan.secondary_domains:
                idx = self._registry.get_domain_rulebase(dom)
                if idx is None:
                    logger.warning("[retrieve] secondary domain %r not loaded — skipping expansion", dom)
                    continue
                run_scope(f"secondary:{dom}", idx)
                if dom not in expansion_used:
                    expansion_used.append(dom)

        merged_flat: list[tuple[RuleRecord, float, dict[str, Any]]] = [(r, s, d) for r, s, d, _ in pooled]
        merged_flat = _dedupe_best_score(merged_flat)
        merged_flat = merged_flat[: plan.top_k_final]

        combined_sc = [ScopedCandidate.from_ranked_tuple(r, s, d, retrieval_scope=str(d.get("retrieval_scope") or "")) for r, s, d in merged_flat]

        result = RetrievalResult(
            plan=plan,
            by_scope=by_scope,
            combined_ranking=combined_sc,
            cross_domain_expansion_applied=expansion_done,
            expansion_domains_used=expansion_used,
        )

        full_index = self._registry.build_merged_index(
            self._registry.list_domains(),
            include_shared=bool(self._registry.get_shared()),
            statute_ids=[],
        )
        return result, merged_flat, full_index
