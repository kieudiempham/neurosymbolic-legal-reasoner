"""Process-wide QA orchestrator wiring (paths + singleton)."""

from __future__ import annotations

from pathlib import Path

from runtime.qa_orchestrator import QAOrchestrator
from retrieval.evidence_retriever import configure_evidence_path
from retrieval.rulebase_loader import configure_rulebase_path
from verification.nli_verifier import NLIVerifier

_orchestrator: QAOrchestrator | None = None


def configure_qa_orchestrator(
    *,
    rulebase_core_path: Path,
    evidence_chunks_path: Path,
    rule_retrieval_top_k: int = 8,
    nesy_nli_mock: bool = True,
    nli_verifier: NLIVerifier | None = None,
    entailment_threshold: float = 0.70,
    contradiction_threshold: float = 0.70,
) -> QAOrchestrator:
    """Idempotent configuration: sets paths for loaders + stores orchestrator singleton."""
    global _orchestrator
    configure_rulebase_path(rulebase_core_path)
    configure_evidence_path(evidence_chunks_path)
    _orchestrator = QAOrchestrator(
        rulebase_core_path=rulebase_core_path,
        evidence_chunks_path=evidence_chunks_path,
        rule_retrieval_top_k=rule_retrieval_top_k,
        nesy_nli_mock=nesy_nli_mock,
        nli_verifier=nli_verifier,
        entailment_threshold=entailment_threshold,
        contradiction_threshold=contradiction_threshold,
    )
    return _orchestrator


def get_qa_orchestrator() -> QAOrchestrator:
    if _orchestrator is None:
        raise RuntimeError("configure_qa_orchestrator() must run at application startup")
    return _orchestrator
