"""Draft KB extraction with an LLM: article text -> Horn rules over a growing shared predicate vocabulary.

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.kbx.extract --doc 10_bao_hiem_xa_hoi   (pilot)
    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.kbx.extract                            (all 18)

Output (draft, NOT manually reviewed): data/diag/kb_full_draft/{rules.jsonl, vocabulary.yaml, relations.yaml, stats.json}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
from dotenv import load_dotenv
from openai import OpenAI

from .corpus import ROOT, Article, load_corpus

OUT = ROOT / "data" / "diag" / "kb_full_draft"
CACHE = ROOT / "experiments" / "kbx" / "cache"
SEED_VOCAB = ROOT / "data" / "diag" / "vocabulary.yaml"
MODEL = "gpt-4o-mini"
MAX_CHUNK = 7000
PRICE_IN, PRICE_OUT = 0.15 / 1e6, 0.60 / 1e6  # USD per token (gpt-4o-mini list price; verify on the pricing page)

PROMPT = """Bạn mã hóa văn bản pháp luật Việt Nam thành luật logic dạng Horn cho một hệ suy luận ký hiệu.

Văn bản: {doc} — {ref}{chapter}
Lĩnh vực: {domain}

[NỘI DUNG]
{text}

[VOCABULARY HIỆN CÓ — ưu tiên dùng lại đúng tên]
{vocab}

Yêu cầu:
1. Mỗi quy phạm có cấu trúc "nếu điều kiện thì hệ quả" -> một rule type "condition":
   premises = các điều kiện PHẢI ĐỒNG THỜI thỏa mãn (mỗi điều kiện là MỘT mệnh đề), conclusion = hệ quả pháp lý.
   Điều kiện thay thế nhau ("hoặc", "một trong các trường hợp", các điểm a, b, c liệt kê lựa chọn) -> TÁCH thành nhiều rule riêng.
   Điều kiện phủ định ("không", "chưa", "trừ") dùng value=false.
   Không bịa điều kiện không có trong văn bản.
2. Quy định tra cứu (hồ sơ gồm..., thời hạn..., cơ quan có thẩm quyền..., mức phí...) -> type "lookup":
   conclusion mô tả nội dung tra cứu, premises là phạm vi áp dụng (có thể rỗng).
3. Bỏ qua điều khoản chỉ nêu phạm vi điều chỉnh, giải thích từ ngữ thuần túy, hiệu lực thi hành, trách nhiệm thi hành.
4. Tên predicate: tiếng Anh snake_case, ngắn, KHÔNG chứa con số cụ thể của vụ việc (ngưỡng thì đưa vào tên, ví dụ term_at_least_12_months).
   Chỉ dùng lại predicate có sẵn khi nghĩa TRÙNG KHỚP hoàn toàn; nếu chỉ gần giống thì tạo predicate mới.
   Predicate mới phải khai báo trong new_predicates
   (kind = "input" nếu là dữ kiện người dùng cung cấp, "derived" nếu là kết luận pháp lý trung gian/cuối).
5. Nếu quy phạm là ngoại lệ của quy định khác ("trừ trường hợp", "không áp dụng đối với", "trường hợp ... thì thực hiện theo"),
   ghi exception_to = tham chiếu nguyên văn (ví dụ "khoản 1 Điều 2" hoặc "Điều 33 Luật này").
6. source ghi chính xác khoản/điểm thực sự chứa quy phạm đó: "Điều X khoản Y điểm z" (đếm đúng số khoản).

Chỉ trả về JSON:
{{"rules": [{{"type": "condition|lookup", "source": "...", "premises": [{{"pred": "...", "value": true}}],
              "conclusion": {{"pred": "...", "value": true}}, "exception_to": "", "quote": "<trích ngắn nguyên văn>"}}],
  "new_predicates": [{{"pred": "...", "kind": "input|derived", "template_pos": "<câu tiếng Việt khi đúng>",
                       "template_neg": "<câu khi sai>", "ask": "<câu hỏi người dùng, chỉ cho input>"}}]}}"""


class Vocab:
    """Thread-safe shared vocabulary, seeded with the curated BHXH vocabulary."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        seed = yaml.safe_load(SEED_VOCAB.read_text(encoding="utf-8"))["predicates"]
        self.preds: dict[str, dict] = {p: dict(v, domains=["labor"], origin="curated") for p, v in seed.items()}
        self.uses: Counter = Counter()

    def prompt_list(self, domain: str, text: str, limit: int = 220) -> str:
        with self.lock:
            items = list(self.preds.items())
        words = set(re.findall(r"\w+", text.lower()))

        def score(kv):
            p, v = kv
            overlap = len(words & set(re.findall(r"\w+", v.get("template_pos", "").lower())))
            return (domain in v.get("domains", []), overlap, self.uses[p])

        items.sort(key=score, reverse=True)
        return "\n".join(f"- {p} ({v.get('kind')}): {v.get('template_pos', '')}" for p, v in items[:limit])

    def add(self, entries: list[dict], domain: str) -> None:
        with self.lock:
            for e in entries:
                p = _norm_pred(e.get("pred", ""))
                if not p:
                    continue
                if p not in self.preds:
                    self.preds[p] = {k: e.get(k, "") for k in ("kind", "template_pos", "template_neg", "ask")}
                    self.preds[p].update(domains=[domain], origin="llm_draft")
                elif domain not in self.preds[p]["domains"]:
                    self.preds[p]["domains"].append(domain)

    def known(self, p: str) -> bool:
        with self.lock:
            return p in self.preds


def _norm_pred(p: str) -> str:
    p = re.sub(r"[^a-z0-9_]", "_", str(p).strip().lower())
    return re.sub(r"_+", "_", p).strip("_")


def chunks(art: Article) -> list[str]:
    if len(art.text) <= MAX_CHUNK:
        return [art.text]
    parts = re.split(r"(?m)(?=^\s*\d+\.\s)", art.text)
    out, cur = [], ""
    for part in parts:
        if len(cur) + len(part) > MAX_CHUNK and cur:
            out.append(cur)
            cur = ""
        cur += part
        while len(cur) > MAX_CHUNK:
            out.append(cur[:MAX_CHUNK])
            cur = cur[MAX_CHUNK:]
    if cur.strip():
        out.append(cur)
    return out


class Extractor:
    def __init__(self, model: str = MODEL):
        load_dotenv(ROOT / ".env")
        self.client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.environ.get("LLM_BASE_URL") or None)
        self.model = model
        self.vocab = Vocab()
        self.usage = Counter()
        self.lock = threading.Lock()
        CACHE.mkdir(parents=True, exist_ok=True)

    def call(self, art: Article, k: int, text: str) -> dict:
        key = hashlib.sha1(f"v2|{self.model}|{art.doc_id}|{art.number}|{k}|{text}".encode()).hexdigest()
        f = CACHE / f"{key}.json"
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))
        prompt = PROMPT.format(doc=art.doc_id, ref=f"Điều {art.number}. {art.title}",
                               chapter=f" (Chương {art.chapter})" if art.chapter else "", domain=art.domain,
                               text=text, vocab=self.vocab.prompt_list(art.domain, text))
        for attempt in range(12):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model, temperature=0.0, response_format={"type": "json_object"},
                    messages=[{"role": "user", "content": prompt}])
                out = json.loads(resp.choices[0].message.content)
                with self.lock:
                    self.usage["in"] += resp.usage.prompt_tokens
                    self.usage["out"] += resp.usage.completion_tokens
                    self.usage["calls"] += 1
                f.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
                return out
            except json.JSONDecodeError:
                time.sleep(1)
            except Exception as e:
                wait = min(60, 3 * 2 ** attempt)
                print(f"   retry {attempt} in {wait}s: {type(e).__name__}", flush=True)
                time.sleep(wait)
        raise RuntimeError(f"extraction failed: {art.ref}")

    def article(self, art: Article) -> list[dict]:
        rules = []
        for k, text in enumerate(chunks(art)):
            out = self.call(art, k, text)
            self.vocab.add(out.get("new_predicates") or [], art.domain)
            for j, r in enumerate(out.get("rules") or []):
                rules.append(self._normalize(r, art, k, j))
        return [r for r in rules if r]

    def _normalize(self, r: dict, art: Article, k: int, j: int) -> dict | None:
        concl = r.get("conclusion") or {}
        c = _norm_pred(concl.get("pred", ""))
        if not c:
            return None
        prem = [{"pred": _norm_pred(p.get("pred", "")), "value": bool(p.get("value", True))}
                for p in (r.get("premises") or []) if _norm_pred(p.get("pred", ""))]
        unknown = [p["pred"] for p in prem if not self.vocab.known(p["pred"])] + ([] if self.vocab.known(c) else [c])
        src = str(r.get("source") or f"Điều {art.number}")
        return {
            "id": f"{art.domain[:3].upper()}-{art.doc_id[:2]}-D{art.number}-{k}{j:02d}",
            "type": r.get("type", "condition") if r.get("type") in ("condition", "lookup") else "condition",
            "premises": [p["pred"] if p["value"] else f"~{p['pred']}" for p in prem],
            "conclusion": c if concl.get("value", True) else f"~{c}",
            "source": f"{art.doc_id}, {src}",
            "doc_id": art.doc_id, "article": art.number, "domain": art.domain,
            "exception_to": str(r.get("exception_to") or ""),
            "quote": str(r.get("quote") or "")[:400],
            "undeclared_predicates": unknown,
            "review_status": "draft",
        }


_REF = re.compile(r"(?:(?:điểm\s+([a-zđ])\s+)?khoản\s+(\d+)\s+)?Điều\s+(\d+[a-zđ]?)", re.I)


def resolve_exceptions(rules: list[dict]) -> list[list[str]]:
    """Map 'exception_to' references to rule ids of the same document (same article/clause, same conclusion predicate)."""
    by_art = defaultdict(list)
    for r in rules:
        by_art[(r["doc_id"], r["article"].split("#")[0])].append(r)
    pairs = []
    for r in rules:
        ref = r["exception_to"]
        if not ref:
            continue
        m = _REF.search(ref)
        art = m.group(3) if m else r["article"].split("#")[0]
        clause = m.group(2) if m else None
        conc = r["conclusion"].lstrip("~")
        for t in by_art.get((r["doc_id"], art), []):
            if t["id"] == r["id"] or t["conclusion"].lstrip("~") != conc:
                continue
            if clause and f"khoản {clause}" not in t["source"]:
                continue
            pairs.append([r["id"], t["id"]])
    return pairs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", default="", help="substring of doc_id to restrict (pilot)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args()

    arts = [a for a in load_corpus() if args.doc in a.doc_id]
    ex = Extractor(args.model)
    print(f"{len(arts)} articles, model {ex.model}", flush=True)
    t0 = time.time()
    results: dict[int, list[dict]] = {}
    done = 0

    def work(ia):
        nonlocal done
        i, a = ia
        results[i] = ex.article(a)
        with ex.lock:
            done += 1
            if done % 20 == 0:
                cost = ex.usage["in"] * PRICE_IN + ex.usage["out"] * PRICE_OUT
                print(f"  {done}/{len(arts)} ({time.time() - t0:.0f}s, ~${cost:.3f})", flush=True)

    with ThreadPoolExecutor(args.workers) as pool:
        list(pool.map(work, enumerate(arts)))
    rules = [r for i in sorted(results) for r in results[i]]
    pairs = resolve_exceptions(rules)

    OUT.mkdir(parents=True, exist_ok=True)
    suffix = f"_{args.doc}" if args.doc else ""
    with open(OUT / f"rules{suffix}.jsonl", "w", encoding="utf-8") as fh:
        for r in rules:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (OUT / f"vocabulary{suffix}.yaml").write_text(
        yaml.safe_dump({"predicates": ex.vocab.preds}, allow_unicode=True, sort_keys=True), encoding="utf-8")
    (OUT / f"relations{suffix}.yaml").write_text(
        yaml.safe_dump({"exception_of": pairs, "priority_over": [],
                        "note": "auto-resolved from exception_to references; draft, not reviewed"},
                       allow_unicode=True), encoding="utf-8")
    cost = ex.usage["in"] * PRICE_IN + ex.usage["out"] * PRICE_OUT
    cond = [r for r in rules if r["type"] == "condition"]
    stats = {
        "model": ex.model, "articles": len(arts), "rules": len(rules), "condition_rules": len(cond),
        "lookup_rules": len(rules) - len(cond),
        "condition_rules_multi_premise": sum(len(r["premises"]) >= 2 for r in cond),
        "rules_with_undeclared_predicates": sum(bool(r["undeclared_predicates"]) for r in rules),
        "predicates_total": len(ex.vocab.preds),
        "predicates_new": sum(v.get("origin") == "llm_draft" for v in ex.vocab.preds.values()),
        "exception_references": sum(bool(r["exception_to"]) for r in rules),
        "exception_of_resolved": len(pairs),
        "by_domain": dict(Counter(r["domain"] for r in rules)),
        "by_doc": dict(Counter(r["doc_id"] for r in rules)),
        "api_calls": ex.usage["calls"], "tokens_in": ex.usage["in"], "tokens_out": ex.usage["out"],
        "estimated_cost_usd": round(cost, 3), "seconds": round(time.time() - t0),
        "review_status": "draft (LLM-extracted, not manually verified)",
    }
    (OUT / f"stats{suffix}.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
