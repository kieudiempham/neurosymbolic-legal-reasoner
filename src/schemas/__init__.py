"""Shared data schemas (Pydantic) aligned with paper terminology."""

from schemas.legal_frame_schema import LegalFrame
from schemas.proof import ProofObject as Proof, ProofStep
from schemas.question_parse import Layer1Parse as Layer1SemanticSlots
from schemas.question_parse import Layer2Parse as Layer2LogicObjects
from schemas.rule import RuleRecord as Rule
from schemas.verification import VerificationResult

__all__ = [
    "Layer1SemanticSlots",
    "Layer2LogicObjects",
    "LegalFrame",
    "Rule",
    "Proof",
    "ProofStep",
    "VerificationResult",
]
