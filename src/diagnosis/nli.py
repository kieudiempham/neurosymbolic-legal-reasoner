"""Targeted three-way NLI: original question (premise) vs. verbalised proposition (hypothesis)."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

# NLI_BACKEND selects the measurement model; each backend has its own score cache.
#   mdeberta: fine-tuned multilingual NLI classifier (computed locally or on GPU)
#   qwen:     open-weight LLM scoring the three labels (scores computed on GPU only, kaggle/nli_qwen_kaggle.py)
BACKENDS = {
    "mdeberta": ("MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7", "nli_cache.json"),
    "qwen": ("Qwen/Qwen2.5-7B-Instruct", "nli_cache_qwen2.5-7b.json"),
    "gpt4omini": ("gpt-4o-mini-2024-07-18 (prompt v4)", "nli_cache_gpt4omini.json"),
    "ensemble_gpt": ("mDeBERTa+gpt-4o-mini (mean)", None),
    # mean of the two label distributions (the classifier is strong on stated facts, the LLM on unstated ones)
    "ensemble": ("mDeBERTa+Qwen2.5-7B (mean)", None),
}
BACKEND = os.environ.get("NLI_BACKEND", "mdeberta")
MODEL_NAME, _cache_name = BACKENDS[BACKEND]
_DIAG = Path(__file__).resolve().parents[2] / "experiments" / "diag"
CACHE_FILE = _DIAG / (_cache_name or "nli_cache.json")
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
    if rule == "pos_only":  # the negative template is not used by this rule, so it is not queried
        pos = model.predict_many([(question, vocab[pred]["template_pos"])])[0]
        neg = None
    else:
        pos, neg = model.predict_many([(question, vocab[pred]["template_pos"]), (question, vocab[pred]["template_neg"])])
    pos_label = max(pos, key=pos.get)
    neg_label = max(neg, key=neg.get) if neg else None
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
        if BACKEND in ("ensemble", "ensemble_gpt"):
            a = json.loads((_DIAG / BACKENDS["mdeberta"][1]).read_text(encoding="utf-8"))
            other = "qwen" if BACKEND == "ensemble" else "gpt4omini"
            b = json.loads((_DIAG / BACKENDS[other][1]).read_text(encoding="utf-8"))
            self._cache = {k: {lab: (a[k][lab] + b[k][lab]) / 2 for lab in a[k]} for k in a.keys() & b.keys()}
        elif CACHE_FILE.exists():
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
        if todo and BACKEND in ("gpt4omini", "ensemble_gpt"):
            self._score_new_gpt(todo)  # rare new pairs (e.g. a fact only the real parser produces): score now
            todo = []
        if todo and BACKEND != "mdeberta":
            raise RuntimeError(f"{len(todo)} pairs missing from the {BACKEND} cache; score them on GPU "
                               "(python -m diagnosis.nli_gpu export, then kaggle/nli_qwen_kaggle.py)")
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

    def _score_new_gpt(self, keys: list[str]) -> None:
        """Score unseen pairs with GPT-4o-mini (prompt v4) and, for the ensemble, mDeBERTa on CPU; both
        persistent backend caches are extended so later runs reuse the scores."""
        import torch
        from dotenv import load_dotenv
        from openai import OpenAI
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        from .nli_openai import score_pair

        load_dotenv(_DIAG.parents[1] / ".env")
        client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.environ.get("LLM_BASE_URL") or None)
        gf, mf = _DIAG / BACKENDS["gpt4omini"][1], _DIAG / BACKENDS["mdeberta"][1]
        gc, mc = json.loads(gf.read_text(encoding="utf-8")), json.loads(mf.read_text(encoding="utf-8"))
        need_md = [k for k in keys if k not in mc]
        if need_md and BACKEND == "ensemble_gpt":
            name = BACKENDS["mdeberta"][0]
            tok = AutoTokenizer.from_pretrained(name)
            model = AutoModelForSequenceClassification.from_pretrained(name).eval()
            for k in need_md:
                prem, hyp = k.split("␞", 1)
                enc = tok([prem], [hyp], return_tensors="pt", truncation=True, max_length=256)
                with torch.inference_mode():
                    row = torch.softmax(model(**enc).logits, dim=-1)[0].tolist()
                mc[k] = {_LABEL[model.config.id2label[j].lower()]: v for j, v in enumerate(row)}
            mf.write_text(json.dumps(mc, ensure_ascii=False), encoding="utf-8")
        for k in keys:
            if k not in gc:
                gc[k] = score_pair(client, "gpt-4o-mini", *k.split("␞", 1), prompt="v4")
        gf.write_text(json.dumps(gc, ensure_ascii=False), encoding="utf-8")
        for k in keys:
            self._cache[k] = gc[k] if BACKEND == "gpt4omini" else {l: (mc[k][l] + gc[k][l]) / 2 for l in gc[k]}

    def predict(self, premise: str, hypothesis: str) -> tuple[str, dict[str, float]]:
        scores = self.predict_many([(premise, hypothesis)])[0]
        return max(scores, key=scores.get), scores

    def save(self) -> None:
        if BACKEND in ("ensemble", "ensemble_gpt"):
            return  # derived from the two backend caches, never written
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(self._cache, ensure_ascii=False), encoding="utf-8")
