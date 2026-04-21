"""Shared canonical semantic family normalization for reasoning pipeline."""

from __future__ import annotations

import re
from typing import Any

CANONICAL_FAMILIES: tuple[str, ...] = (
    "obligation",
    "permission",
    "prohibition",
    "deadline",
    "threshold",
    "applicability",
    "legal_effect",
    "procedure",
    "dossier",
    "authority_action",
    "exception",
)

_CANONICAL_SET = set(CANONICAL_FAMILIES)

FAMILY_ALIASES: dict[str, str] = {
    # Core canonical identities.
    "obligation": "obligation",
    "permission": "permission",
    "prohibition": "prohibition",
    "deadline": "deadline",
    "threshold": "threshold",
    "applicability": "applicability",
    "legal_effect": "legal_effect",
    "procedure": "procedure",
    "dossier": "dossier",
    "authority_action": "authority_action",
    "exception": "exception",
    # Legacy and trigger-style aliases.
    "must": "obligation",
    "obligation_trigger": "obligation",
    "prohibition_trigger": "prohibition",
    "legal_effect_trigger": "legal_effect",
    "legal_consequence": "legal_effect",
    "legal_consequence_or_legal_effect": "legal_effect",
    "applicability_condition": "applicability",
    "condition_based": "applicability",
    "eligibility": "applicability",
    "applies_if": "applicability",
    "regulatory_deadline": "deadline",
    "regulatory_deadline_requirement": "deadline",
    "procedure_step": "procedure",
    "authority": "authority_action",
    "sanction": "legal_effect",
}


def _normalize_token(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    token = re.sub(r"[^a-z0-9_]+", "_", text)
    token = re.sub(r"_+", "_", token).strip("_")
    return token


def normalize_family(value: Any) -> str:
    """Normalize arbitrary family labels into the reasoning-level canonical set."""
    token = _normalize_token(value)
    if not token:
        return ""
    mapped = FAMILY_ALIASES.get(token, token)
    return mapped if mapped in _CANONICAL_SET else ""


def normalize_predicate_family(value: Any) -> str:
    """Alias-friendly helper used at predicate/goal/rule matching sites."""
    return normalize_family(value)


def is_canonical_family(value: Any) -> bool:
    return normalize_family(value) in _CANONICAL_SET
