"""NLI via any OpenAI-compatible HTTP API (e.g. Groq)."""

from __future__ import annotations

import json
import re
from typing import Any, cast

from openai import OpenAI

from schemas.verification import NLILabel, NLIResult
from verification.nli_verifier import NLIVerifier

_NLI_SYSTEM = (
    "You classify textual entailment. Output a single JSON object only, no markdown: "
    '{"label":"entailment"|"contradiction"|"neutral","score":number} '
    "where score is your confidence between 0 and 1."
)


class OpenAICompatibleNLIVerifier(NLIVerifier):
    """Chat-completions NLI (premise vs hypothesis) for NeSy verification."""

    def __init__(self, *, api_key: str, base_url: str, model: str, timeout: float = 60.0) -> None:
        self._model = model
        self._client = OpenAI(api_key=api_key, base_url=base_url.rstrip("/"), timeout=timeout)

    def verify(self, premise: str, hypothesis: str) -> NLIResult:
        user = f'Premise:\n{premise}\n\nHypothesis:\n{hypothesis}'
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _NLI_SYSTEM},
                {"role": "user", "content": user},
            ],
            temperature=0.0,
            max_tokens=120,
        )
        raw = (resp.choices[0].message.content or "").strip()
        return _parse_nli_response(raw)


def _parse_nli_response(raw: str) -> NLIResult:
    text = raw
    if "```" in text:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
        if m:
            text = m.group(1).strip()
    try:
        data: Any = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[^{}]*\}", text)
        if not m:
            return NLIResult(label="neutral", score=0.5)
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return NLIResult(label="neutral", score=0.5)

    if not isinstance(data, dict):
        return NLIResult(label="neutral", score=0.5)

    label_raw = data.get("label", "neutral")
    score_raw = data.get("score", 0.5)

    label_s = str(label_raw).lower().strip()
    if label_s not in ("entailment", "contradiction", "neutral"):
        label_s = "neutral"

    try:
        score = float(score_raw)
    except (TypeError, ValueError):
        score = 0.5
    score = max(0.0, min(1.0, score))

    scores_full: dict[str, float] | None = None
    if isinstance(data.get("scores"), dict):
        raw_s = data["scores"]
        scores_full = {}
        for k in ("entailment", "neutral", "contradiction"):
            if k in raw_s:
                try:
                    scores_full[k] = float(raw_s[k])
                except (TypeError, ValueError):
                    pass
        if not scores_full:
            scores_full = None

    return NLIResult(label=cast(NLILabel, label_s), score=score, scores=scores_full)
