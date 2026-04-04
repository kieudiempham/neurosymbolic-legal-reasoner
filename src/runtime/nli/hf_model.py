"""Low-level Hugging Face NLI: tokenizer + sequence classification + softmax."""

from __future__ import annotations

import logging
import time
from typing import Any

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from runtime.nli.types import NLIRuntimeConfig

logger = logging.getLogger(__name__)

# Canonical keys in downstream dicts / fusion
_LABEL_KEYS = ("entailment", "neutral", "contradiction")

# When config uses opaque labels (LABEL_0…), many MNLI checkpoints use this index order.
_FALLBACK_MNLI_ORDER = ("contradiction", "neutral", "entailment")


def resolve_torch_device(spec: str) -> torch.device:
    if spec == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(spec)


def _normalize_config_label(raw: str) -> str:
    s = raw.strip().lower()
    if "entail" in s:
        return "entailment"
    if "contradict" in s:
        return "contradiction"
    return "neutral"


class HFNLIModel:
    """
    Loads `AutoTokenizer` + `AutoModelForSequenceClassification`, runs softmax inference.
    Vietnamese (and other) text is handled by the multilingual model; no extra normalize step required.
    """

    def __init__(self, config: NLIRuntimeConfig) -> None:
        self._cfg = config
        self._device = resolve_torch_device(config.device)
        t0 = time.perf_counter()
        logger.info(
            "NLI loading model=%s device=%s batch_size=%d max_length=%d",
            config.model_name,
            self._device,
            config.batch_size,
            config.max_length,
        )
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(config.model_name, use_fast=True)
            self._model = AutoModelForSequenceClassification.from_pretrained(config.model_name)
        except Exception as e:
            logger.warning("NLI failed to load model %s: %s", config.model_name, e)
            raise
        self._model.to(self._device)
        self._model.eval()
        self._id2label = dict(self._model.config.id2label) if self._model.config.id2label else {}
        if not self._id2label:
            raise RuntimeError("Model config missing id2label; cannot map logits to NLI classes.")
        dt = time.perf_counter() - t0
        logger.info("NLI model ready in %.2fs id2label=%s", dt, self._id2label)

    @property
    def device(self) -> torch.device:
        return self._device

    @property
    def model_name(self) -> str:
        return self._cfg.model_name

    def _probs_to_scores(self, probs: list[float]) -> dict[str, float]:
        out: dict[str, float] = {k: 0.0 for k in _LABEL_KEYS}
        for i, p in enumerate(probs):
            raw = self._id2label.get(i, str(i))
            key = _normalize_config_label(str(raw))
            if key in out:
                out[key] = float(p)
        if sum(out.values()) < 1e-6 and len(probs) == len(_FALLBACK_MNLI_ORDER):
            logger.warning(
                "NLI id2label not recognized as entail/neutral/contradict; using positional MNLI fallback %s",
                self._id2label,
            )
            for i, name in enumerate(_FALLBACK_MNLI_ORDER):
                out[name] = float(probs[i])
        return out

    def predict(self, premise: str, hypothesis: str) -> dict[str, Any]:
        """Single pair; returns label, scores, echo strings."""
        return self.batch_predict([(premise, hypothesis)])[0]

    def batch_predict(self, pairs: list[tuple[str, str]]) -> list[dict[str, Any]]:
        if not pairs:
            return []
        results: list[dict[str, Any]] = []
        bs = max(1, self._cfg.batch_size)
        for start in range(0, len(pairs), bs):
            chunk = pairs[start : start + bs]
            premises = [p for p, _ in chunk]
            hypotheses = [h for _, h in chunk]
            batch_out = self._forward_batch(premises, hypotheses)
            results.extend(batch_out)
        return results

    def _forward_batch(self, premises: list[str], hypotheses: list[str]) -> list[dict[str, Any]]:
        empty_warn = False
        for i, (p, h) in enumerate(zip(premises, hypotheses)):
            if not (p or "").strip() or not (h or "").strip():
                empty_warn = True
        if empty_warn:
            logger.warning("NLI batch contains empty premise or hypothesis; using neutral fallback for those.")

        enc = self._tokenizer(
            premises,
            hypotheses,
            padding=True,
            truncation=True,
            max_length=self._cfg.max_length,
            return_tensors="pt",
        )
        enc = {k: v.to(self._device) for k, v in enc.items()}

        t0 = time.perf_counter()
        with torch.no_grad():
            logits = self._model(**enc).logits
            probs = torch.softmax(logits, dim=-1).detach().cpu().tolist()
        dt = time.perf_counter() - t0
        if len(premises) > 1 or dt > 0.5:
            logger.debug("NLI forward batch_size=%d time=%.3fs", len(premises), dt)

        out: list[dict[str, Any]] = []
        for i, (premise, hypothesis) in enumerate(zip(premises, hypotheses)):
            if not (premise or "").strip() or not (hypothesis or "").strip():
                scores = {"entailment": 0.0, "neutral": 1.0, "contradiction": 0.0}
                label = "neutral"
                score = 1.0
            else:
                row = probs[i]
                scores = self._probs_to_scores(row)
                label = max(scores, key=scores.get)  # type: ignore[arg-type]
                score = float(scores[label])
            out.append(
                {
                    "label": label,
                    "scores": scores,
                    "premise": premise,
                    "hypothesis": hypothesis,
                }
            )
        return out
