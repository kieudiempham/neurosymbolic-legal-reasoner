"""Rule-based domain routing + retrieval-oriented plan (phase 2 — no ML)."""

from __future__ import annotations

import re
from typing import Any

from schemas.domain_routing import DomainRoutingPlan
from schemas.question_parse import Layer1Parse, Layer2Parse
from rulebase.bridge_runtime import match_bridges_for_text
from rulebase.rulebase_registry import RulebaseRegistry

_DEFAULT_PRIMARY = "enterprise"

_TAX_PATTERNS = re.compile(
    r"(thuế|thue|vat|gtgt|tncn|khấu trừ|khai thuế|cơ quan thuế|thu nhập chịu thuế|"
    r"tax|invoice\s*vat)",
    re.I,
)
_LABOR_PATTERNS = re.compile(
    r"(lao động|lao dong|hợp đồng lao động|hợp đồng lao dong|bhxh|"
    r"tiền lương|tien luong|sa thải|sa thai|đình công|nghỉ việc|nghi viec|"
    r"employment|labor contract|trade union)",
    re.I,
)


class SimpleDomainSelector:
    """
    Chooses primary/secondary domains and flags for retrieval (cross-domain expansion, shared).
    When ``registry`` is passed, bridge matching can suggest extra routing evidence.
    """

    def select(
        self,
        parse_result: dict[str, Any] | Layer1Parse | None,
        *,
        registry: RulebaseRegistry | None = None,
    ) -> DomainRoutingPlan:
        if parse_result is None:
            return DomainRoutingPlan(
                primary_domains=[_DEFAULT_PRIMARY],
                secondary_domains=[],
                include_shared=True,
                allow_cross_domain_expansion=False,
                shared_only=False,
                routing_confidence=0.2,
                routing_reasons=["no_parse_result"],
                triggered_bridges=[],
            )
        layer1: Layer1Parse | None = None
        layer2: Layer2Parse | None = None
        q = ""
        if isinstance(parse_result, dict):
            layer1 = parse_result.get("layer1")
            layer2 = parse_result.get("layer2")
            q = str(parse_result.get("question") or parse_result.get("question_text") or "")
        else:
            layer1 = parse_result  # type: ignore[assignment]

        if layer1 and hasattr(layer1, "subject_text"):
            q = f"{q} {layer1.subject_text or ''} {layer1.action_text or ''} {layer1.modality_text or ''}"
        if layer2 and getattr(layer2, "query_rule_candidate", None):
            q += " " + str(layer2.query_rule_candidate or "")

        qlow = q.strip().lower()
        tax_hits = len(_TAX_PATTERNS.findall(qlow))
        labor_hits = len(_LABOR_PATTERNS.findall(qlow))

        md = (layer1.parse_metadata if layer1 else None) or {}
        intent = str(md.get("intent") or md.get("question_intent") or "").lower()
        if "tax" in intent or "thuế" in intent:
            tax_hits += 2
        if "labor" in intent or "lao động" in intent or "employment" in intent:
            labor_hits += 2

        reasons: list[str] = []
        primary = _DEFAULT_PRIMARY
        secondary: list[str] = []
        conf = 0.35
        allow_x = False
        bridges: list[str] = []

        if registry is not None:
            bridges = match_bridges_for_text(qlow, registry)
            if bridges:
                reasons.append(f"bridges:{','.join(bridges)}")
                if any("labor" in b for b in bridges):
                    labor_hits += 1
                if any("tax" in b for b in bridges):
                    tax_hits += 1

        if tax_hits > 0 and labor_hits > 0:
            if tax_hits >= labor_hits:
                primary = "tax"
                secondary = ["labor"]
                reasons.append("mixed_signals_tax_primary")
            else:
                primary = "labor"
                secondary = ["tax"]
                reasons.append("mixed_signals_labor_primary")
            conf = min(0.95, 0.55 + 0.1 * max(tax_hits, labor_hits))
            allow_x = True
        elif tax_hits > 0:
            primary = "tax"
            conf = min(0.95, 0.5 + 0.1 * tax_hits)
            reasons.append("keyword_tax")
        elif labor_hits > 0:
            primary = "labor"
            conf = min(0.95, 0.5 + 0.1 * labor_hits)
            reasons.append("keyword_labor")
            allow_x = bool(secondary)
        else:
            reasons.append("default_enterprise")

        return DomainRoutingPlan(
            primary_domains=[primary],
            secondary_domains=secondary,
            include_shared=True,
            allow_cross_domain_expansion=allow_x and bool(secondary),
            shared_only=False,
            routing_confidence=conf,
            routing_reasons=reasons,
            triggered_bridges=bridges,
        )
