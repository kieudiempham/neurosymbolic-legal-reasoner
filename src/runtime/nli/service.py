"""Singleton-friendly NLI service wrapping `HFNLIModel` (predict / batch_predict)."""

from __future__ import annotations

import logging
from typing import Any

from runtime.nli.hf_model import HFNLIModel
from runtime.nli.types import NLIRuntimeConfig

logger = logging.getLogger(__name__)

_instance: NLIService | None = None


class NLIService:
    """High-level API: delegates to `HFNLIModel`; use `get_nli_service()` after init."""

    def __init__(self, config: NLIRuntimeConfig) -> None:
        self._config = config
        self._model = HFNLIModel(config)

    @property
    def config(self) -> NLIRuntimeConfig:
        return self._config

    def predict(self, premise: str, hypothesis: str) -> dict[str, Any]:
        return self._model.predict(premise, hypothesis)

    def batch_predict(self, pairs: list[tuple[str, str]]) -> list[dict[str, Any]]:
        return self._model.batch_predict(pairs)


def init_nli_service(config: NLIRuntimeConfig) -> NLIService:
    """Create and register the process-wide NLI service (replaces previous instance)."""
    global _instance
    _instance = NLIService(config)
    logger.info("NLI service initialized model=%s", config.model_name)
    return _instance


def get_nli_service() -> NLIService:
    if _instance is None:
        raise RuntimeError("NLI service not initialized; call init_nli_service() first or enable NLI in backend.")
    return _instance


def reset_nli_service() -> None:
    """Clear singleton (tests / reload)."""
    global _instance
    _instance = None
