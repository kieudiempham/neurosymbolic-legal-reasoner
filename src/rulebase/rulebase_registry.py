"""Registry for shared, domain, and statute-scoped rulebases (multi-rulebase phase 1)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from schemas.rule import RuleRecord
from schemas.rule_metadata import normalize_rule_record
from retrieval.rulebase_loader import RulebaseIndex
from rulebase.shared_rule_pack import get_shared_rules

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def _normalize_index_rules(
    index: RulebaseIndex,
    *,
    rulebase_id: str,
    layer: str,
    domain: str | None,
) -> RulebaseIndex:
    """Return a new index whose rules carry normalized metadata."""
    from schemas.rule_metadata import RuleLayer

    layer_t: RuleLayer
    if layer in ("shared", "domain", "statute"):
        layer_t = layer  # type: ignore[assignment]
    else:
        layer_t = "domain"
    dom = domain or "enterprise"
    out_rules: list[RuleRecord] = []
    for r in index.rules:
        out_rules.append(
            normalize_rule_record(
                r,
                rulebase_id=rulebase_id,
                layer=layer_t,
                domain=dom,
                warn_prefix="[registry] ",
            )
        )
    return RulebaseIndex(out_rules)


class RulebaseRegistry:
    """
    Holds references to multiple :class:`RulebaseIndex` instances.

    **Legacy adapter:** use :meth:`from_legacy_core` to register a single JSON file as one domain.
    """

    def __init__(self) -> None:
        self.shared: RulebaseIndex | None = None
        self.domain_rulebases: dict[str, RulebaseIndex] = {}
        self.statute_packs: dict[str, RulebaseIndex] = {}

    def register_shared(self, shared_rulebase: RulebaseIndex, *, rulebase_id: str = "shared_core") -> None:
        self.shared = _normalize_index_rules(shared_rulebase, rulebase_id=rulebase_id, layer="shared", domain="shared")

    def register_domain(self, domain: str, rulebase: RulebaseIndex, *, rulebase_id: str | None = None) -> None:
        rid = rulebase_id or f"{domain}_core"
        self.domain_rulebases[domain] = _normalize_index_rules(rulebase, rulebase_id=rid, layer="domain", domain=domain)

    def register_shared_from_pack(self) -> None:
        """Register shared rules from shared_rule_pack.py for Part C."""
        shared_rules = get_shared_rules()
        if shared_rules:
            shared_index = RulebaseIndex(shared_rules)
            self.register_shared(shared_index, rulebase_id="shared_pack_v1")
            logger.info("[registry] registered %d shared rules from pack", len(shared_rules))

    def get_shared(self) -> RulebaseIndex | None:
        return self.shared

    def get_domain_rulebase(self, domain: str) -> RulebaseIndex | None:
        return self.domain_rulebases.get(domain)

    def get_statute_pack(self, statute_id: str) -> RulebaseIndex | None:
        return self.statute_packs.get(statute_id)

    def list_domains(self) -> list[str]:
        return sorted(self.domain_rulebases.keys())

    def list_statutes(self) -> list[str]:
        return sorted(self.statute_packs.keys())

    def build_merged_index(
        self,
        primary_domains: list[str],
        *,
        include_shared: bool = True,
        statute_ids: list[str] | None = None,
    ) -> RulebaseIndex:
        """
        Merge rules from shared (optional), named domains, and statute packs into one :class:`RulebaseIndex`.

        Duplicate ``rule_id`` values across sources keep the first occurrence and log a warning.
        """
        merged: list[RuleRecord] = []
        seen: set[str] = set()

        def add_from(idx: RulebaseIndex, label: str) -> None:
            for r in idx.rules:
                if r.rule_id in seen:
                    logger.warning(
                        "[registry] duplicate rule_id %s when merging from %s — skipping duplicate",
                        r.rule_id,
                        label,
                    )
                    continue
                seen.add(r.rule_id)
                merged.append(r)

        if include_shared and self.shared:
            add_from(self.shared, "shared")
        for d in primary_domains:
            rb = self.domain_rulebases.get(d)
            if rb:
                add_from(rb, f"domain:{d}")
            else:
                logger.warning("[registry] unknown domain %r — no rules loaded for it", d)
        for sid in statute_ids or []:
            pk = self.statute_packs.get(sid)
            if pk:
                add_from(pk, f"statute:{sid}")

        return RulebaseIndex(merged)

    @classmethod
    def from_legacy_core(
        cls,
        path: str | None,
        *,
        domain: str = "enterprise",
        rulebase_id: str | None = None,
    ) -> RulebaseRegistry:
        """
        Adapter: load ``rulebase_reasoning_core``-style JSON from *path* and register as a single domain.

        Does not register *shared*; callers may add shared later.
        """
        from pathlib import Path

        from retrieval.rulebase_loader import load_rulebase

        reg = cls()
        if not path:
            return reg
        p = Path(path)
        if not p.exists():
            logger.error("[registry] legacy path missing: %s", p)
            return reg
        rid = rulebase_id or f"{domain}_core"
        idx = load_rulebase(p, legacy_domain=domain, legacy_rulebase_id=rid, normalize_metadata=False)
        reg.register_domain(domain, idx, rulebase_id=rid)
        return reg
