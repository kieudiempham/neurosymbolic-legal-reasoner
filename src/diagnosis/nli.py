"""Targeted three-way NLI: original question (premise) vs. verbalised proposition (hypothesis)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
CACHE_FILE = Path(__file__).resolve().parents[2] / "experiments" / "diag" / "nli_cache.json"
_LABEL = {"entailment": "entail", "neutral": "neutral", "contradiction": "contra"}


def verbalize(vocab: dict, pred: str) -> str:
    """Deterministic template: always the positive reading, so entail => C true, contra => C false."""
    return vocab[pred]["template_pos"]


class NLIModel:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._cache: dict[str, dict] = {}
        if CACHE_FILE.exists():
            self._cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        self.calls = 0

    @lru_cache(maxsize=1)
    def _load(self):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        tok = AutoTokenizer.from_pretrained(self.model_name)
        model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        model.eval()
        torch.set_num_threads(max(1, torch.get_num_threads()))
        return tok, model

    def predict(self, premise: str, hypothesis: str) -> tuple[str, dict[str, float]]:
        self.calls += 1
        key = premise + "␞" + hypothesis
        if key not in self._cache:
            import torch

            tok, model = self._load()
            enc = tok(premise, hypothesis, return_tensors="pt", truncation=True, max_length=256)
            with torch.no_grad():
                probs = torch.softmax(model(**enc).logits[0], dim=-1).tolist()
            scores = {_LABEL[model.config.id2label[i].lower()]: p for i, p in enumerate(probs)}
            self._cache[key] = scores
        scores = self._cache[key]
        return max(scores, key=scores.get), scores

    def save(self) -> None:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(self._cache, ensure_ascii=False), encoding="utf-8")
