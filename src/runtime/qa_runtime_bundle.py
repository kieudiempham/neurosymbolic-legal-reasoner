"""Container for multi-rulebase QA dependencies (phase 1).

The main pipeline still calls parse / gates / answer helpers directly; this bundle groups registry
and retrieval so orchestrators can depend on one object as the project grows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from retrieval.domain_scoped_retriever import DomainScopedRuleRetriever
from rulebase.rulebase_registry import RulebaseRegistry
from runtime.domain_selector import SimpleDomainSelector


@dataclass
class QARuntimeBundle:
    rulebase_registry: RulebaseRegistry
    domain_retriever: DomainScopedRuleRetriever
    domain_selector: SimpleDomainSelector
    parser: Any = None
    retriever: Any = None
    backward_reasoner: Any = None
    forward_reasoner: Any = None
    verifier: Any = None
    answer_generator: Any = None
    repair_loop: Any = None

    @classmethod
    def from_legacy_rulebase_path(
        cls,
        path: str | None,
        *,
        domain: str = "enterprise",
        rulebase_id: str | None = None,
    ) -> QARuntimeBundle:
        reg = RulebaseRegistry.from_legacy_core(path, domain=domain, rulebase_id=rulebase_id)
        return cls(
            rulebase_registry=reg,
            domain_retriever=DomainScopedRuleRetriever(reg),
            domain_selector=SimpleDomainSelector(),
        )
