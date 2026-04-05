"""Application configuration (paths, NeSy modes, env overrides)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_repo_root() -> Path:
    # backend/app/config.py -> parents[2] == repo root
    return Path(__file__).resolve().parents[2]


_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LEGAL_QA_",
        env_file=_REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Legal QA NeSy Research Demo"
    debug: bool = False

    repo_root: Path = Field(default_factory=_default_repo_root)

    rulebase_core_path: Path | None = None
    rulebase_mapping_path: Path | None = None
    evidence_chunks_path: Path | None = None

    # OpenAI-compatible HTTP API (default base URL/model suit Groq; names stay generic.)
    llm_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LLM_API_KEY", "LEGAL_QA_LLM_API_KEY"),
    )
    llm_base_url: str = Field(
        default="https://api.groq.com/openai/v1",
        validation_alias=AliasChoices("LLM_BASE_URL", "LEGAL_QA_LLM_BASE_URL"),
    )
    llm_model: str = Field(
        default="llama-3.1-8b-instant",
        validation_alias=AliasChoices("LLM_MODEL", "LEGAL_QA_LLM_MODEL"),
    )

    # Hugging Face NLI (mDeBERTa XNLI multilingual — premise/hypothesis)
    nli_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("NLI_ENABLED", "LEGAL_QA_NLI_ENABLED"),
    )
    nli_model_name: str = Field(
        default="MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7",
        validation_alias=AliasChoices("NLI_MODEL_NAME", "LEGAL_QA_NLI_MODEL_NAME"),
    )
    nli_device: str = Field(
        default="auto",
        validation_alias=AliasChoices("NLI_DEVICE", "LEGAL_QA_NLI_DEVICE"),
    )
    nli_batch_size: int = Field(
        default=8,
        validation_alias=AliasChoices("NLI_BATCH_SIZE", "LEGAL_QA_NLI_BATCH_SIZE"),
    )
    nli_max_length: int = Field(
        default=512,
        validation_alias=AliasChoices("NLI_MAX_LENGTH", "LEGAL_QA_NLI_MAX_LENGTH"),
    )
    nli_entailment_threshold: float = Field(
        default=0.70,
        validation_alias=AliasChoices("NLI_ENTAILMENT_THRESHOLD", "LEGAL_QA_NLI_ENTAILMENT_THRESHOLD"),
    )
    nli_contradiction_threshold: float = Field(
        default=0.70,
        validation_alias=AliasChoices("NLI_CONTRADICTION_THRESHOLD", "LEGAL_QA_NLI_CONTRADICTION_THRESHOLD"),
    )

    #: When False (default), all five NeSy modes may invoke NLI (unless degraded — see ``nli_policy``).
    #: Set True for fast tests / dev without an NLI backend.
    nesy_nli_mock: bool = False
    #: ``strict``: startup fails if NLI is required but unavailable. ``degraded``: symbolic-only with explicit trace.
    nli_policy: Literal["strict", "degraded"] = "degraded"
    #: If True, on answer REJECT still emit a short fallback answer (not default for research runs).
    answer_reject_allow_fallback: bool = False
    session_ttl_seconds: int = 3600 * 24
    rule_retrieval_top_k: int = 8

    def resolved_rulebase_core(self) -> Path:
        p = self.rulebase_core_path
        return p if p is not None else self.repo_root / "data" / "processed" / "rulebase" / "rulebase_reasoning_core.json"

    def resolved_rulebase_mapping(self) -> Path:
        p = self.rulebase_mapping_path
        return p if p is not None else self.repo_root / "data" / "processed" / "rulebase" / "rulebase_reasoning_core_mapping.json"

    def resolved_evidence_chunks(self) -> Path:
        p = self.evidence_chunks_path
        return p if p is not None else self.repo_root / "data" / "corpus" / "evidence_chunks.json"


VerificationModeLiteral = Literal[
    "parse_verification",
    "rule_verification",
    "backward_verification",
    "forward_verification",
    "answer_verification",
]

FusionDecisionLiteral = Literal["ACCEPT", "REJECT", "REPAIR"]


settings = Settings()
