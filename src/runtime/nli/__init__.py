"""Hugging Face NLI runtime (mDeBERTa XNLI-style) for NeSy verification."""

from runtime.nli.helpers import (
    check_contradiction,
    check_entailment,
    is_semantically_consistent,
    score_pair,
    support_score,
    verify_claim_against_evidence,
)
from runtime.nli.hf_model import HFNLIModel, resolve_torch_device
from runtime.nli.service import NLIService, get_nli_service, init_nli_service, reset_nli_service
from runtime.nli.types import NLIRuntimeConfig

__all__ = [
    "NLIRuntimeConfig",
    "HFNLIModel",
    "NLIService",
    "init_nli_service",
    "get_nli_service",
    "reset_nli_service",
    "resolve_torch_device",
    "check_entailment",
    "check_contradiction",
    "score_pair",
    "verify_claim_against_evidence",
    "support_score",
    "is_semantically_consistent",
]
