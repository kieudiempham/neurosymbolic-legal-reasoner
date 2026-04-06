"""Single bootstrap path for registry + bundle (phase 2 — registry-first)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from retrieval.rulebase_loader import load_rulebase
from rulebase.rulebase_registry import RulebaseRegistry
from retrieval.domain_scoped_retriever import DomainScopedRuleRetriever
from retrieval.advanced_domain_retriever import AdvancedDomainRetriever
from runtime.domain_selector import SimpleDomainSelector
from runtime.qa_runtime_bundle import QARuntimeBundle

logger = logging.getLogger(__name__)


@dataclass
class RulebasePathConfig:
    """Resolved paths for multi-domain load."""

    repo_root: Path
    enterprise: Path | None = None
    labor: Path | None = None
    tax: Path | None = None
    shared: Path | None = None
    #: Single-file fallback (phase-1 style) — used as enterprise if enterprise path missing
    legacy_core: Path | None = None


class RulebaseRuntimeBootstrap:
    """Build :class:`RulebaseRegistry` and :class:`QARuntimeBundle` from path config (single source of truth)."""

    def build_registry(self, cfg: RulebasePathConfig) -> RulebaseRegistry:
        reg = RulebaseRegistry()
        ent_path = cfg.enterprise or cfg.legacy_core
        if ent_path and ent_path.exists():
            idx = load_rulebase(
                ent_path,
                legacy_domain="enterprise",
                legacy_rulebase_id="enterprise_core",
                normalize_metadata=False,
            )
            reg.register_domain("enterprise", idx, rulebase_id="enterprise_core")
        else:
            logger.warning("[bootstrap] no enterprise/legacy rulebase path resolved — registry empty")

        if cfg.shared and cfg.shared.exists():
            idx_s = load_rulebase(cfg.shared, legacy_domain="shared", legacy_rulebase_id="shared_core", normalize_metadata=False)
            reg.register_shared(idx_s, rulebase_id="shared_core")
        else:
            logger.debug("[bootstrap] no shared rulebase file — optional")

        if cfg.labor and cfg.labor.exists():
            idx_l = load_rulebase(cfg.labor, legacy_domain="labor", legacy_rulebase_id="labor_core", normalize_metadata=False)
            reg.register_domain("labor", idx_l, rulebase_id="labor_core")
        else:
            logger.debug("[bootstrap] labor rulebase not configured or missing file")

        if cfg.tax and cfg.tax.exists():
            idx_t = load_rulebase(cfg.tax, legacy_domain="tax", legacy_rulebase_id="tax_core", normalize_metadata=False)
            reg.register_domain("tax", idx_t, rulebase_id="tax_core")
        else:
            logger.debug("[bootstrap] tax rulebase not configured or missing file")

        return reg

    def build_runtime_bundle(self, cfg: RulebasePathConfig) -> QARuntimeBundle:
        reg = self.build_registry(cfg)
        return QARuntimeBundle(
            rulebase_registry=reg,
            domain_retriever=DomainScopedRuleRetriever(reg),
            domain_selector=SimpleDomainSelector(),
            retriever_advanced=AdvancedDomainRetriever(reg),
        )


def path_config_from_settings(settings: Any) -> RulebasePathConfig:
    """Duck-typed adapter for ``backend.app.config.Settings`` or tests."""
    repo = getattr(settings, "repo_root", None) or Path(".")
    return RulebasePathConfig(
        repo_root=Path(repo),
        enterprise=_opt_resolved(settings, "resolved_rulebase_enterprise"),
        labor=_opt_resolved(settings, "resolved_rulebase_labor"),
        tax=_opt_resolved(settings, "resolved_rulebase_tax"),
        shared=_opt_resolved(settings, "resolved_rulebase_shared"),
        legacy_core=_opt_resolved(settings, "resolved_rulebase_core"),
    )


def _opt_resolved(settings: Any, method: str) -> Path | None:
    fn = getattr(settings, method, None)
    if callable(fn):
        try:
            p = fn()
            return Path(p) if p is not None else None
        except Exception:
            return None
    return None
