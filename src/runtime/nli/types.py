"""Typed config for Hugging Face NLI runtime (decoupled from FastAPI settings)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NLIRuntimeConfig:
    """Parameters for loading and running an XNLI-style transformer."""

    model_name: str = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
    device: str = "auto"
    batch_size: int = 8
    max_length: int = 512
