"""Application configuration (paths, NeSy modes, env overrides)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_repo_root() -> Path:
    # backend/app/config.py -> parents[2] == repo root
    return Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LEGAL_QA_", env_file=".env", extra="ignore")

    app_name: str = "Legal QA NeSy Research Demo"
    debug: bool = False

    repo_root: Path = Field(default_factory=_default_repo_root)

    rulebase_core_path: Path | None = None
    rulebase_mapping_path: Path | None = None
    evidence_chunks_path: Path | None = None

    nesy_nli_mock: bool = True
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
    "backward_verification",
    "forward_verification",
    "answer_verification",
]

FusionDecisionLiteral = Literal["ACCEPT", "REJECT", "REPAIR"]


settings = Settings()
