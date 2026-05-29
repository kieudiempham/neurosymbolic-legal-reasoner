"""
Baseline runner — GPT-4.1 via OpenAI API.

Two modes:
  direct   ChatGPT (no context) → evaluation/results/baseline_gpt41_direct.jsonl
  rag      ChatGPT + RAG (oracle evidence_text as context)
           → evaluation/results/baseline_gpt41_rag.jsonl

Output per line is fully compatible with compute_eval_tables.py.

Config (paper-reportable):
  model       : gpt-4.1
  temperature : 0.2
  top_p       : 1.0
  max_tokens  : 700

Usage:
    export OPENAI_API_KEY=sk-...
    python evaluation/scripts/run_baseline_gpt41.py --mode direct
    python evaluation/scripts/run_baseline_gpt41.py --mode rag
    python evaluation/scripts/run_baseline_gpt41.py --mode direct --limit 10
    python evaluation/scripts/run_baseline_gpt41.py --mode direct --resume
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CASES_FILE = ROOT / "evaluation" / "qa_290_exp_cases_gold_mode.jsonl"
OUT_DIR    = ROOT / "evaluation" / "results"

# ---------------------------------------------------------------------------
# Paper config — do NOT change without updating paper text
# ---------------------------------------------------------------------------
MODEL       = "gpt-4.1"
TEMPERATURE = 0.2
TOP_P       = 1.0
MAX_TOKENS  = 700

PROMPT_DIRECT = """\
Bạn là trợ lý pháp lý tại Việt Nam.

Hãy trả lời câu hỏi sau bằng tiếng Việt, theo cách rõ ràng và dễ hiểu cho người không chuyên.

Yêu cầu:
- Trả lời trực tiếp câu hỏi
- Có thể viện dẫn quy định pháp luật nếu biết
- Không cần trình bày theo format đặc biệt
- Nếu thiếu thông tin, có thể đưa ra giả định hợp lý

Câu hỏi:
{question}"""

PROMPT_RAG = """\
Bạn là trợ lý pháp lý tại Việt Nam.

Dưới đây là một số đoạn văn bản pháp luật liên quan:

{retrieved_context}

Hãy trả lời câu hỏi dựa trên thông tin trên.

Yêu cầu:
- Ưu tiên sử dụng thông tin trong context
- Có thể viện dẫn điều luật nếu có
- Nếu context không đủ, có thể suy luận thêm

Câu hỏi:
{question}"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Matches patterns like: Điều 30, khoản 2 Điều 5, Điều 31 khoản 2, etc.
_CITATION_RE = re.compile(
    r"(?:khoản\s+\d+\s+)?Điều\s+\d+(?:\s+khoản\s+\d+)?(?:\s+[—–-]\s+[\w/]+)?",
    re.IGNORECASE | re.UNICODE,
)

# Phrases that suggest the system is asking for missing information
_MISSING_FACT_PHRASES = [
    "cần biết thêm", "cần xác định", "cần làm rõ", "phụ thuộc vào",
    "tùy thuộc", "nếu bạn có", "nếu anh/chị", "thiếu thông tin",
    "chưa đủ thông tin", "cần bổ sung",
]


def extract_citations(text: str) -> list[str]:
    found = _CITATION_RE.findall(text)
    seen: set[str] = set()
    out: list[str] = []
    for c in found:
        c = c.strip()
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def extract_missing_facts(text: str) -> list[str]:
    """Heuristic: if the text signals missing info, return generic marker."""
    lower = text.lower()
    if any(phrase in lower for phrase in _MISSING_FACT_PHRASES):
        return ["[unstructured_clarification_in_text]"]
    return []


def infer_pred_mode(final_answer: str, missing_facts: list[str]) -> str:
    if final_answer and missing_facts:
        return "A+B"
    if missing_facts:
        return "B"
    return "A"


def build_output_record(case: dict, raw_answer: str, latency_ms: int, model: str) -> dict:
    citations = extract_citations(raw_answer)
    missing   = extract_missing_facts(raw_answer)
    return {
        "id":       case["id"],
        "model":    model,
        "question": case["question"],
        "domain":   case.get("domain"),
        "question_group": case.get("question_group"),

        # gold labels (needed by compute_eval_tables.py)
        "gold_answer_mode":         case.get("gold_answer_mode"),
        "gold_missing_facts":       case.get("gold_missing_facts") or [],
        "gold_response_requirements": case.get("gold_response_requirements") or {},

        # system output fields (aligned with run_batch_eval.py format)
        "final_answer":     raw_answer,
        "final_status":     "success" if raw_answer else "error",
        "pred_mode":        infer_pred_mode(raw_answer, missing),
        "predicted_domains": [],       # GPT does not expose domain routing
        "selected_rule_id": None,      # no symbolic rule in baseline
        "proof_present":    False,     # no formal proof in baseline
        "legal_citations":  citations,
        "missing_facts":    missing,
        "verification": {              # no verification layer in baseline
            "parse":   "N/A",
            "rule":    "N/A",
            "forward": "N/A",
            "answer":  "N/A",
        },
        "latency_ms": latency_ms,
    }


# ---------------------------------------------------------------------------
# OpenAI call
# ---------------------------------------------------------------------------

def call_openai(client: Any, prompt: str) -> tuple[str, int]:
    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    latency_ms = round((time.perf_counter() - t0) * 1000)
    return resp.choices[0].message.content or "", latency_ms


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_done_ids(path: Path) -> set[str]:
    done: set[str] = set()
    if not path.exists():
        return done
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                done.add(json.loads(line)["id"])
            except Exception:
                pass
    return done


def run(args: argparse.Namespace) -> int:
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai package not installed. Run: pip install openai", file=sys.stderr)
        return 1

    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: set OPENAI_API_KEY env var or pass --api-key", file=sys.stderr)
        return 1

    client = OpenAI(api_key=api_key)
    mode   = args.mode  # "direct" | "rag"
    model_label = f"gpt41_{mode}"

    out_path = OUT_DIR / f"baseline_gpt41_{mode}.jsonl"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    done_ids: set[str] = set()
    if args.resume:
        done_ids = load_done_ids(out_path)
        print(f"[resume] {len(done_ids)} cases already done.")

    cases: list[dict] = []
    with CASES_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))

    if args.limit:
        cases = cases[: args.limit]

    total   = len(cases)
    success = errors = skipped = 0

    write_mode = "a" if args.resume else "w"
    with out_path.open(write_mode, encoding="utf-8") as out_f:
        for i, case in enumerate(cases, 1):
            cid = case["id"]
            if cid in done_ids:
                skipped += 1
                continue

            # Build prompt
            if mode == "direct":
                prompt = PROMPT_DIRECT.format(question=case["question"])
            else:
                context = (case.get("evidence_text") or "").strip()
                if case.get("legal_source"):
                    context = f"[{case['legal_source']}]\n{context}"
                prompt = PROMPT_RAG.format(
                    retrieved_context=context or "(không có context)",
                    question=case["question"],
                )

            try:
                raw_answer, latency_ms = call_openai(client, prompt)
            except Exception as exc:
                print(f"  [{i}/{total}] ERROR {cid}: {exc}", file=sys.stderr)
                out_f.write(json.dumps({
                    "id": cid,
                    "model": model_label,
                    "domain": case.get("domain"),
                    "question_group": case.get("question_group"),
                    "gold_answer_mode": case.get("gold_answer_mode"),
                    "gold_missing_facts": case.get("gold_missing_facts") or [],
                    "gold_response_requirements": case.get("gold_response_requirements") or {},
                    "final_status": "error",
                    "error": str(exc),
                }, ensure_ascii=False) + "\n")
                out_f.flush()
                errors += 1
                time.sleep(2)
                continue

            record = build_output_record(case, raw_answer, latency_ms, model_label)
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            out_f.flush()
            success += 1
            print(f"  [{i}/{total}] {cid} | {latency_ms}ms | citations={len(record['legal_citations'])}")

            # gentle rate-limit: ~3 req/s max
            time.sleep(0.35)

    print(f"\nDone. success={success}, errors={errors}, skipped={skipped}")
    print(f"Output: {out_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Baseline runner — GPT-4.1")
    parser.add_argument("--mode",    choices=["direct", "rag"], required=True,
                        help="direct = no context | rag = oracle evidence_text as context")
    parser.add_argument("--limit",   type=int, default=0,  help="Run only first N cases")
    parser.add_argument("--resume",  action="store_true",  help="Skip already-done ids")
    parser.add_argument("--api-key", default="",           help="OpenAI API key (or set OPENAI_API_KEY)")
    return run(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
