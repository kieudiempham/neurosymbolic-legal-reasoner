"""LLM semantic parser into the shared predicate vocabulary, plus targeted re-parsing of one proposition."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .kb import KB
from .reasoner import Fact

ROOT = Path(__file__).resolve().parents[2]
CACHE_FILE = ROOT / "experiments" / "diag" / "parser_cache.json"

PARSE_PROMPT = """Bạn là bộ phân tích ngữ nghĩa (semantic parser) cho hệ thống hỏi đáp pháp luật bảo hiểm xã hội.
Nhiệm vụ: đọc câu hỏi của người dùng và trích xuất các dữ kiện của vụ việc theo đúng danh sách predicate dưới đây.

Mỗi predicate là một mệnh đề về người hỏi. value = true nghĩa là câu "khi đúng" xảy ra; value = false nghĩa là câu "khi sai" xảy ra.
{predicates}

Quy tắc:
- Chỉ trích dữ kiện được câu hỏi nêu ra hoặc suy ra trực tiếp từ câu chữ. Không đoán, không dùng giá trị mặc định.
- Không đưa vào predicate mà câu hỏi không đề cập.
- span là đoạn nguyên văn ngắn trong câu hỏi làm căn cứ.

Câu hỏi: {question}

Chỉ trả về JSON: {{"facts": [{{"pred": "<tên predicate>", "value": true|false, "span": "<đoạn nguyên văn>"}}]}}"""

REPARSE_PROMPT = """Câu hỏi của người dùng: {question}

Hãy xác định duy nhất mệnh đề sau dựa trên câu hỏi:
- Nếu câu hỏi cho biết điều này ĐÚNG: "{pos}"
- Nếu câu hỏi cho biết điều này SAI: "{neg}"
- Nếu câu hỏi không nói tới: trả về "unknown".

Chỉ trả về JSON: {{"value": "true" | "false" | "unknown", "span": "<đoạn nguyên văn hoặc rỗng>"}}"""


class LLMParser:
    def __init__(self, kb: KB, model: str | None = None):
        load_dotenv(ROOT / ".env")
        self.kb = kb
        self.client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.environ.get("LLM_BASE_URL") or None)
        self.model = model or os.environ.get("LLM_MODEL", "gpt-4o")
        self.cache = json.loads(CACHE_FILE.read_text(encoding="utf-8")) if CACHE_FILE.exists() else {}
        self.calls = 0
        self.pred_list = "\n".join(
            f"- {p}: khi đúng = \"{v['template_pos']}\"; khi sai = \"{v['template_neg']}\""
            for p, v in kb.vocab.items()
            if v.get("kind") == "input"
        )

    def _chat(self, key: str, prompt: str) -> dict:
        if key not in self.cache:
            for attempt in range(15):
                try:
                    resp = self.client.chat.completions.create(
                        model=self.model, temperature=0.0, top_p=1.0,
                        response_format={"type": "json_object"},
                        messages=[{"role": "user", "content": prompt}],
                    )
                    self.cache[key] = json.loads(resp.choices[0].message.content)
                    self.calls += 1
                    break
                except Exception as e:  # rate limits: back off and retry, never fall back to an empty parse
                    wait = min(60, 5 * 2 ** attempt)
                    print(f"retry {attempt} in {wait}s: {type(e).__name__}", flush=True)
                    time.sleep(wait)
            else:
                raise RuntimeError(f"LLM call failed after retries: {key[:80]}")
            self.save()
        return self.cache[key]

    def parse(self, question: str) -> dict[str, Fact]:
        out = self._chat(f"parse|{self.model}|{question}", PARSE_PROMPT.format(predicates=self.pred_list, question=question))
        facts: dict[str, Fact] = {}
        for f in out.get("facts", []):
            p = f.get("pred")
            if p in self.kb.vocab and self.kb.vocab[p].get("kind") == "input" and isinstance(f.get("value"), bool):
                facts[p] = Fact(p, f["value"], "parser", str(f.get("span") or ""))
        return facts

    def reparse(self, question: str, pred: str) -> bool | None:
        v = self.kb.vocab[pred]
        out = self._chat(f"reparse|{self.model}|{pred}|{question}",
                         REPARSE_PROMPT.format(question=question, pos=v["template_pos"], neg=v["template_neg"]))
        val = str(out.get("value", "unknown")).lower()
        return {"true": True, "false": False}.get(val)

    def save(self) -> None:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(self.cache, ensure_ascii=False), encoding="utf-8")
