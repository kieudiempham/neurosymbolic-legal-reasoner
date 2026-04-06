"""Domain-scoped rule retrieval (shared + primary domains) reusing hybrid BM25 + structured ranker."""

from __future__ import annotations

from typing import Any

from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleRecord
from schemas.rule_metadata import meta_for_proof_and_trace
from retrieval.rule_retriever import retrieve_rules
from retrieval.rulebase_loader import RulebaseIndex
from rulebase.rulebase_registry import RulebaseRegistry


def enrich_ranked_with_retrieval_meta(
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
) -> list[tuple[RuleRecord, float, dict[str, Any]]]:
    """Attach multi-rulebase fields to diagnostics (same shape as :meth:`DomainScopedRuleRetriever.retrieve`)."""
    out: list[tuple[RuleRecord, float, dict[str, Any]]] = []
    for rule, score, diag in ranked:
        m = meta_for_proof_and_trace(rule)
        enriched = dict(diag)
        enriched["rule_id"] = m["rule_id"]
        enriched["rulebase_id"] = m["rulebase_id"]
        enriched["domain"] = m["domain"]
        enriched["layer"] = m["layer"]
        enriched["source_doc"] = m["source_doc"]
        enriched["source_article"] = m["source_article"]
        enriched["score"] = float(score)
        out.append((rule, score, enriched))
    return out


class DomainScopedRuleRetriever:
    """
    Builds a merged :class:`RulebaseIndex` from the registry for the active domains, then
    delegates to :func:`retrieval.rule_retriever.retrieve_rules`.
    """

    def __init__(self, registry: RulebaseRegistry) -> None:
        self._registry = registry

    def retrieve(
        self,
        layer1: Layer1Parse,
        layer2: Layer2Parse,
        primary_domains: list[str],
        *,
        include_shared: bool = True,
        top_k: int = 20,
        statute_ids: list[str] | None = None,
        w_lexical: float = 0.35,
        w_structured: float = 0.65,
    ) -> tuple[list[tuple[RuleRecord, float, dict[str, Any]]], RulebaseIndex]:
        merged = self._registry.build_merged_index(
            primary_domains,
            include_shared=include_shared,
            statute_ids=statute_ids or [],
        )
        ranked = retrieve_rules(
            layer1=layer1,
            layer2=layer2,
            top_k=top_k,
            index=merged,
            w_lexical=w_lexical,
            w_structured=w_structured,
        )
        out: list[tuple[RuleRecord, float, dict[str, Any]]] = []
        for rule, score, diag in ranked:
            m = meta_for_proof_and_trace(rule)
            enriched = dict(diag)
            enriched["rule_id"] = m["rule_id"]
            enriched["rulebase_id"] = m["rulebase_id"]
            enriched["domain"] = m["domain"]
            enriched["layer"] = m["layer"]
            enriched["source_doc"] = m["source_doc"]
            enriched["source_article"] = m["source_article"]
            enriched["score"] = float(score)
            out.append((rule, score, enriched))
        return out, merged
