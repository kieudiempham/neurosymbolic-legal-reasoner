"""Targeted three-way NLI: original question (premise) vs. verbalised proposition (hypothesis)."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
CACHE_FILE = Path(__file__).resolve().parents[2] / "experiments" / "diag" / "nli_cache.json"
_LABEL = {"entailment": "entail", "neutral": "neutral", "contradiction": "contra"}


ACCEPT_THRESHOLD = float(os.environ.get("NLI_TAU", 0.70))
# "pos_neg": the negative-template prediction must agree with the positive one (default);
# "pos_only": only the confidence of the positive-template prediction is tested
ACCEPT_RULE = os.environ.get("NLI_RULE", "pos_neg")


def verbalize(vocab: dict, pred: str) -> str:
    """Deterministic template: always the positive reading, so entail => C true, contra => C false."""
    return vocab[pred]["template_pos"]


def verify(model: "NLIModel", question: str, vocab: dict, pred: str, tau: float | None = None,
           rule: str | None = None) -> dict:
    """Acceptance test that turns a provisional NLI prediction into an observation (or rejects it).

    The proposition is queried twice, with its positive and its negative template. A label is accepted
    only if the positive-template prediction is confident (p >= tau) and the negative-template prediction
    does not contradict it (entail on the positive reading must not also be entail on the negative one,
    and vice versa; neutral must be neutral on both). Otherwise the result is unverified (label None).
    """
    tau = ACCEPT_THRESHOLD if tau is None else tau
    rule = ACCEPT_RULE if rule is None else rule
    pos, neg = model.predict_many([(question, vocab[pred]["template_pos"]), (question, vocab[pred]["template_neg"])])
    pos_label, neg_label = max(pos, key=pos.get), max(neg, key=neg.get)
    expected_neg = {"entail": "contra", "contra": "entail", "neutral": "neutral"}[pos_label]
    confident = pos[pos_label] >= tau
    consistent = rule == "pos_only" or neg_label == expected_neg or (pos_label != "neutral" and neg_label == "neutral")
    return {
        "raw": pos_label,
        "label": pos_label if (confident and consistent) else None,
        "pos_scores": pos,
        "neg_label": neg_label,
        "reject_reason": "" if confident and consistent else ("low_confidence" if not confident else "template_disagreement"),
    }


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
        torch.set_num_threads(int(os.environ.get("NLI_THREADS", os.cpu_count() or 4)))
        return tok, model

    def predict_many(self, pairs: list[tuple[str, str]], batch_size: int = 16) -> list[dict[str, float]]:
        """Scores for many (premise, hypothesis) pairs; uncached pairs are run in padded batches."""
        keys = [p + "␞" + h for p, h in pairs]
        todo = list(dict.fromkeys(k for k in keys if k not in self._cache))
        if todo:
            import torch

            tok, model = self._load()
            for i in range(0, len(todo), batch_size):
                chunk = todo[i : i + batch_size]
                prem, hyp = zip(*(k.split("␞", 1) for k in chunk))
                enc = tok(list(prem), list(hyp), return_tensors="pt", truncation=True, max_length=256, padding=True)
                with torch.inference_mode():
                    probs = torch.softmax(model(**enc).logits, dim=-1).tolist()
                for k, row in zip(chunk, probs):
                    self._cache[k] = {_LABEL[model.config.id2label[j].lower()]: p for j, p in enumerate(row)}
        self.calls += len(pairs)
        return [self._cache[k] for k in keys]

    def predict(self, premise: str, hypothesis: str) -> tuple[str, dict[str, float]]:
        scores = self.predict_many([(premise, hypothesis)])[0]
        return max(scores, key=scores.get), scores

    def save(self) -> None:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(self._cache, ensure_ascii=False), encoding="utf-8")
