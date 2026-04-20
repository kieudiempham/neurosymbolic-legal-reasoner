"""Process-wide QA orchestrator wiring (paths + singleton)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.qa_orchestrator import QAOrchestrator
from retrieval.evidence_retriever import configure_evidence_path
from retrieval.rulebase_loader import configure_rulebase_path
from verification.nli_verifier import NLIVerifier

_orchestrator: QAOrchestrator | None = None
# Registry-first singleton for ``get_rulebase_index`` / health (phase 2).
_global_rulebase_registry: Any = None


def get_global_rulebase_registry() -> Any:
    return _global_rulebase_registry


def set_global_rulebase_registry(reg: Any | None) -> None:
    global _global_rulebase_registry
    _global_rulebase_registry = reg


def configure_qa_orchestrator(
    *,
    rulebase_core_path: Path,
    evidence_chunks_path: Path,
    rule_retrieval_top_k: int = 8,
    nesy_nli_mock: bool = False,
    nli_verifier: NLIVerifier | None = None,
    nli_degraded: bool = False,
    nli_meta: dict | None = None,
    entailment_threshold: float = 0.70,
    contradiction_threshold: float = 0.70,
    max_repair_attempts_rule: int = 2,
    max_repair_attempts_backward: int = 1,
    max_repair_attempts_forward: int = 1,
    answer_reject_allow_fallback: bool = False,
    settings: Any | None = None,
    path_config: Any | None = None,
) -> QAOrchestrator:
    """Idempotent configuration: sets paths for loaders + stores orchestrator singleton.

    If ``path_config`` or ``settings`` is provided, builds :class:`QARuntimeBundle` via
    :class:`RulebaseRuntimeBootstrap` (multi-domain). Otherwise uses legacy single-file bundle.
    """
    global _orchestrator
    configure_rulebase_path(rulebase_core_path)
    configure_evidence_path(evidence_chunks_path)

    bundle = None
    if path_config is not None:
        from rulebase.rulebase_runtime_bootstrap import RulebaseRuntimeBootstrap

        bundle = RulebaseRuntimeBootstrap().build_runtime_bundle(path_config)
    elif settings is not None:
        from rulebase.rulebase_runtime_bootstrap import RulebaseRuntimeBootstrap, path_config_from_settings

        bundle = RulebaseRuntimeBootstrap().build_runtime_bundle(path_config_from_settings(settings))

    _orchestrator = QAOrchestrator(
        rulebase_core_path=rulebase_core_path,
        evidence_chunks_path=evidence_chunks_path,
        rule_retrieval_top_k=rule_retrieval_top_k,
        nesy_nli_mock=nesy_nli_mock,
        nli_verifier=nli_verifier,
        nli_degraded=nli_degraded,
        nli_meta=nli_meta,
        entailment_threshold=entailment_threshold,
        contradiction_threshold=contradiction_threshold,
        max_repair_attempts_rule=max_repair_attempts_rule,
        max_repair_attempts_backward=max_repair_attempts_backward,
        max_repair_attempts_forward=max_repair_attempts_forward,
        answer_reject_allow_fallback=answer_reject_allow_fallback,
        qa_runtime_bundle=bundle,
        settings=settings,
    )
    if bundle is not None:
        set_global_rulebase_registry(bundle.rulebase_registry)
    else:
        set_global_rulebase_registry(_orchestrator.runtime_bundle.rulebase_registry)
    return _orchestrator


def get_qa_orchestrator() -> QAOrchestrator:
    if _orchestrator is None:
        raise RuntimeError("configure_qa_orchestrator() must run at application startup")
    return _orchestrator
