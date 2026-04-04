"""Build `NLIVerifier` from settings: HF NLI (preferred when enabled) or OpenAI-compatible API."""

from __future__ import annotations

import logging

from app.config import Settings
from verification.nli_verifier import NLIVerifier
from verification.openai_compatible_nli import OpenAICompatibleNLIVerifier

logger = logging.getLogger(__name__)


def build_nli_verifier(settings: Settings) -> NLIVerifier | None:
    """
    Priority:
    1. Hugging Face NLI when `nli_enabled` (downloads/loads `nli_model_name`).
    2. OpenAI-compatible HTTP API when `LLM_API_KEY` is set.
    3. `None` (orchestrator uses `MockNLIVerifier` inside `NeSyEngine`).
    """
    if settings.nli_enabled:
        try:
            from runtime.nli.service import init_nli_service, reset_nli_service
            from runtime.nli.types import NLIRuntimeConfig
            from verification.hf_nli_verifier import HuggingFaceNLIVerifier

            reset_nli_service()
            cfg = NLIRuntimeConfig(
                model_name=settings.nli_model_name,
                device=settings.nli_device,
                batch_size=settings.nli_batch_size,
                max_length=settings.nli_max_length,
            )
            svc = init_nli_service(cfg)
            logger.info("Using HuggingFaceNLIVerifier model=%s", settings.nli_model_name)
            return HuggingFaceNLIVerifier(svc)
        except Exception as e:
            logger.warning("NLI HF could not be initialized (%s); trying LLM API or mock.", e)

    key = (settings.llm_api_key or "").strip()
    if key:
        logger.info("Using OpenAI-compatible NLI verifier (HTTP)")
        return OpenAICompatibleNLIVerifier(
            api_key=key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
        )
    return None
