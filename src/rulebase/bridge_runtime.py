"""Shared bridge rules — lightweight runtime (phase 2).

Bridges can come from:
- rules in the shared :class:`RulebaseIndex` with ``metadata["bridge"]`` dict
- built-in defaults for common routing hints
"""

from __future__ import annotations

import logging
import re
from typing import Any

from schemas.rule import RuleRecord
from rulebase.rulebase_registry import RulebaseRegistry

logger = logging.getLogger(__name__)

# Built-in semantic/routing bridges (no external file required)
_DEFAULT_BRIDGES: list[dict[str, Any]] = [
    {
        "bridge_id": "builtin_employee_to_labor",
        "trigger_patterns": [r"người\s+lao\s+động", r"employee", r"employer", r"người\s+sử\s+dụng\s+lao\s+động"],
        "suggest_domains": ["labor"],
        "kind": "routing",
    },
    {
        "bridge_id": "builtin_tax_keywords",
        "trigger_patterns": [r"thuế|thue|vat|gtgt|tncn"],
        "suggest_domains": ["tax"],
        "kind": "routing",
    },
]


def _load_metadata_bridges(shared_index: Any | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if shared_index is None:
        return out
    for r in getattr(shared_index, "rules", []) or []:
        md = r.metadata or {}
        br = md.get("bridge")
        if isinstance(br, dict) and br.get("bridge_id"):
            out.append(
                {
                    "bridge_id": str(br.get("bridge_id")),
                    "trigger_patterns": list(br.get("trigger_patterns") or []),
                    "suggest_domains": list(br.get("suggest_domains") or []),
                    "kind": str(br.get("kind") or "routing"),
                    "source_rule_id": r.rule_id,
                }
            )
    return out


def match_bridges_for_text(
    text: str,
    registry: RulebaseRegistry,
) -> list[str]:
    """Return triggered bridge ids from shared rules + builtins."""
    t = (text or "").lower()
    triggered: list[str] = []
    shared = registry.get_shared()
    for b in _load_metadata_bridges(shared) + _DEFAULT_BRIDGES:
        bid = str(b.get("bridge_id") or "")
        for pat in b.get("trigger_patterns") or []:
            try:
                if re.search(pat, t, re.I):
                    if bid and bid not in triggered:
                        triggered.append(bid)
                        logger.debug("[bridge] matched %s via pattern %s", bid, pat[:48])
                    break
            except re.error:
                continue
    return triggered
