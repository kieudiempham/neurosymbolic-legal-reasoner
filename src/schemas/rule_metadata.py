"""Normalized multi-rulebase metadata for rules (QA pipeline phase 1).

Legacy JSON may omit fields; :func:`normalize_rule_record` fills defaults and logs warnings.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.rule import RuleHead, RuleRecord

logger = logging.getLogger(__name__)

RuleLayer = Literal["shared", "domain", "statute"]


class CanonicalHead(BaseModel):
    predicate: str = "unknown"
    args: list[Any] = Field(default_factory=list)


class NormalizedRuleMeta(BaseModel):
    """Minimum schema for multi-rulebase provenance (v1)."""

    rule_id: str
    rulebase_id: str
    layer: RuleLayer = "domain"
    domain: str = "enterprise"
    source_doc: str = ""
    source_article: str = ""
    effective_from: str | None = None
    effective_to: str | None = None
    canonical_head: dict[str, Any] = Field(default_factory=dict)
    canonical_body: list[Any] = Field(default_factory=list)
    surface_text: str = ""
    verbalized_vi: str = ""

    def to_trace_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


MR_V1_KEY = "mr_v1"


def normalize_rule_record(
    rule: RuleRecord,
    *,
    rulebase_id: str,
    layer: RuleLayer,
    domain: str,
    warn_prefix: str = "",
) -> RuleRecord:
    """
    Return a copy of ``rule`` with ``metadata[MR_V1_KEY]`` set and top-level metadata keys mirrored
    for backward compatibility (``rulebase_id``, ``domain``, ``layer``).
    """
    md = dict(rule.metadata or {})
    prov = md.get("provenance") if isinstance(md.get("provenance"), dict) else {}

    source_doc = str(
        md.get("source_doc")
        or prov.get("source_ref_full")
        or prov.get("source_ref")
        or ""
    ).strip()
    if not source_doc and prov:
        logger.warning(
            "%srule %s: missing source_doc; left empty (check provenance)",
            warn_prefix,
            rule.rule_id,
        )

    source_article = str(md.get("source_article") or prov.get("article") or prov.get("clause") or "").strip()

    ch = md.get("canonical_head")
    if not isinstance(ch, dict):
        ch = CanonicalHead(
            predicate=rule.head.predicate,
            args=list(rule.head.args),
        ).model_dump(mode="json")
        logger.warning(
            "%srule %s: canonical_head inferred from RuleRecord.head",
            warn_prefix,
            rule.rule_id,
        )

    cb = md.get("canonical_body")
    if not isinstance(cb, list):
        cb = list(rule.body or [])
        if rule.body:
            logger.warning(
                "%srule %s: canonical_body inferred from RuleRecord.body",
                warn_prefix,
                rule.rule_id,
            )

    surface = str(md.get("surface_text") or rule.logic_form or "").strip()
    verbal = str(md.get("verbalized_vi") or md.get("verbalization_vi") or "").strip()

    norm = NormalizedRuleMeta(
        rule_id=rule.rule_id,
        rulebase_id=rulebase_id,
        layer=layer,
        domain=domain,
        source_doc=source_doc,
        source_article=source_article,
        effective_from=md.get("effective_from") if md.get("effective_from") is not None else None,
        effective_to=md.get("effective_to") if "effective_to" in md else None,
        canonical_head=ch,
        canonical_body=cb,
        surface_text=surface,
        verbalized_vi=verbal,
    )

    md[MR_V1_KEY] = norm.model_dump(mode="json")
    md["rulebase_id"] = rulebase_id
    md["domain"] = domain
    md["layer"] = layer

    return rule.model_copy(update={"metadata": md})


def get_normalized_meta(rule: RuleRecord) -> NormalizedRuleMeta | None:
    """Parse ``metadata[MR_V1_KEY]`` if present."""
    raw = (rule.metadata or {}).get(MR_V1_KEY)
    if not isinstance(raw, dict):
        return None
    try:
        return NormalizedRuleMeta.model_validate(raw)
    except Exception:
        return None


def collect_rulebase_ids_from_index(rules: list[RuleRecord]) -> list[str]:
    """Stable-unique rulebase_id values from normalized metadata (order preserved)."""
    seen: set[str] = set()
    out: list[str] = []
    for r in rules:
        m = get_normalized_meta(r)
        rid = m.rulebase_id if m else str((r.metadata or {}).get("rulebase_id") or "")
        if rid and rid not in seen:
            seen.add(rid)
            out.append(rid)
    return out


def meta_for_proof_and_trace(rule: RuleRecord) -> dict[str, Any]:
    """Unified provenance dict for proof steps and retrieval diagnostics."""
    n = get_normalized_meta(rule)
    if n:
        return {
            "rule_id": n.rule_id,
            "rulebase_id": n.rulebase_id,
            "domain": n.domain,
            "layer": n.layer,
            "source_doc": n.source_doc,
            "source_article": n.source_article,
        }
    md = rule.metadata or {}
    prov = md.get("provenance") if isinstance(md.get("provenance"), dict) else {}
    return {
        "rule_id": rule.rule_id,
        "rulebase_id": str(md.get("rulebase_id") or "unknown"),
        "domain": str(md.get("domain") or "enterprise"),
        "layer": str(md.get("layer") or "domain"),
        "source_doc": str(md.get("source_doc") or prov.get("source_ref_full") or prov.get("source_ref") or ""),
        "source_article": str(md.get("source_article") or prov.get("article") or ""),
    }
