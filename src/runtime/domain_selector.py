"""Rule-based domain routing (phase 1 — no ML)."""

from __future__ import annotations

import re
from typing import Any

from schemas.question_parse import Layer1Parse, Layer2Parse

_DEFAULT_PRIMARY = "enterprise"

# Vietnamese / ASCII keywords (lightweight)
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
    Chooses primary domain(s) from parse output and question text.

    Defaults to ``enterprise``. If both tax and labor signals are strong, primary stays the
    stronger hit; the other domain is listed under ``secondary_domains``.
    """

    def select(self, parse_result: dict[str, Any] | Layer1Parse | None) -> dict[str, Any]:
        if parse_result is None:
            return {
                "primary_domains": [_DEFAULT_PRIMARY],
                "secondary_domains": [],
                "shared_only": False,
                "routing_confidence": 0.2,
                "routing_reasons": ["no_parse_result"],
            }
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

        q = q.strip().lower()
        tax_hits = len(_TAX_PATTERNS.findall(q))
        labor_hits = len(_LABOR_PATTERNS.findall(q))

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
        elif tax_hits > 0:
            primary = "tax"
            conf = min(0.95, 0.5 + 0.1 * tax_hits)
            reasons.append("keyword_tax")
        elif labor_hits > 0:
            primary = "labor"
            conf = min(0.95, 0.5 + 0.1 * labor_hits)
            reasons.append("keyword_labor")
        else:
            reasons.append("default_enterprise")

        return {
            "primary_domains": [primary],
            "secondary_domains": secondary,
            "shared_only": False,
            "routing_confidence": conf,
            "routing_reasons": reasons,
        }
