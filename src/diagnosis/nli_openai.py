"""Three-way NLI scores from an OpenAI chat model, same prompt (v2) and output format as kaggle/nli_qwen_kaggle.py.

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.nli_openai experiments/nli_gpu/pairs_qwen_dev.jsonl \
        experiments/nli_gpu/nli_scores_gpt4omini_dev.jsonl [--model gpt-4o-mini]

One completion token at temperature 0 with top-5 logprobs; the probabilities of the option letters A/B/C
are renormalised into {entail, neutral, contra}. Resumable (pairs already in the output are skipped).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = "Bạn là trợ lý kiểm tra suy luận ngôn ngữ (NLI). Chỉ trả lời bằng một chữ cái."
USER_V2 = (
    "Đoạn văn là câu hỏi của một người dùng. Người hỏi (\"tôi\", \"công ty tôi\", \"doanh nghiệp của tôi\"...) "
    "chính là người lao động, người sử dụng lao động, doanh nghiệp hoặc người nộp thuế được nói tới trong mệnh đề.\n\n"
    "Đoạn văn:\n{premise}\n\n"
    "Mệnh đề:\n{hypothesis}\n\n"
    "Dựa vào đoạn văn, kể cả các suy luận hiển nhiên (so sánh số tiền, thời hạn, tỷ lệ; từ đồng nghĩa; "
    "cách diễn đạt khác cùng nghĩa), mệnh đề trên là:\n"
    "A. Đúng — đoạn văn nêu hoặc suy ra trực tiếp được điều này\n"
    "B. Không xác định — đoạn văn không đề cập đến điều này\n"
    "C. Sai — đoạn văn nêu hoặc suy ra trực tiếp được điều ngược lại\n"
    "Trả lời A, B hoặc C."
)
# v4: v2 + open-world convention made explicit (nothing is inferred from what the question does not say)
USER_V4 = (
    "Đoạn văn là câu hỏi của một người dùng. Người hỏi (\"tôi\", \"công ty tôi\", \"doanh nghiệp của tôi\"...) "
    "chính là người lao động, người sử dụng lao động, doanh nghiệp hoặc người nộp thuế được nói tới trong mệnh đề.\n\n"
    "Đoạn văn:\n{premise}\n\n"
    "Mệnh đề:\n{hypothesis}\n\n"
    "Quy ước: chỉ xét điều đoạn văn THỰC SỰ nêu. Được dùng suy luận hiển nhiên từ điều đã nêu (so sánh số tiền, "
    "thời hạn, tỷ lệ; từ đồng nghĩa; cách diễn đạt khác cùng nghĩa). KHÔNG suy diễn từ việc đoạn văn không nhắc tới "
    "một điều gì: nếu đoạn văn không đề cập đến nội dung của mệnh đề thì chọn B.\n"
    "A. Đúng — đoạn văn nêu, hoặc suy ra hiển nhiên từ điều đã nêu\n"
    "B. Không xác định — đoạn văn không đề cập đến nội dung này\n"
    "C. Sai — đoạn văn nêu, hoặc suy ra hiển nhiên từ điều đã nêu, điều ngược lại\n"
    "Trả lời A, B hoặc C."
)
PROMPTS = {"v2": USER_V2, "v4": USER_V4}
LABELS = [("A", "entail"), ("B", "neutral"), ("C", "contra")]


def score_pair(client: OpenAI, model: str, p: str, h: str, prompt: str = "v2") -> dict:
    for attempt in range(8):
        try:
            r = client.chat.completions.create(
                model=model, temperature=0, max_tokens=1, logprobs=True, top_logprobs=5, seed=0,
                messages=[{"role": "system", "content": SYSTEM},
                          {"role": "user", "content": PROMPTS[prompt].format(premise=p, hypothesis=h)}])
            top: dict[str, float] = {}
            for t in r.choices[0].logprobs.content[0].top_logprobs:  # "B" and " B" both map to B: keep the larger
                k = t.token.strip()
                top[k] = max(top.get(k, -1e9), t.logprob)
            raw = [top.get(letter, -30.0) for letter, _ in LABELS]
            m = max(raw)
            e = [math.exp(x - m) for x in raw]
            return {lab: v / sum(e) for (_, lab), v in zip(LABELS, e)}
        except Exception as ex:  # rate limit / transient: back off, never return an empty score
            if attempt == 7:
                raise
            time.sleep(min(60, 2 ** attempt))
            last = ex  # noqa: F841


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs")
    ap.add_argument("out")
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--prompt", default="v2", choices=["v2", "v4"])
    args = ap.parse_args()
    load_dotenv(ROOT / ".env")
    client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.environ.get("LLM_BASE_URL") or None)
    pairs = [json.loads(x) for x in Path(args.pairs).read_text(encoding="utf-8").splitlines() if x.strip()]
    done = set()
    if Path(args.out).exists():
        for x in Path(args.out).read_text(encoding="utf-8").splitlines():
            if x.strip():
                r = json.loads(x)
                done.add((r["premise"], r["hypothesis"]))
    todo = list(dict.fromkeys((p["premise"], p["hypothesis"]) for p in pairs if (p["premise"], p["hypothesis"]) not in done))
    print(f"{args.model}: {len(pairs)} pairs, {len(done)} done, {len(todo)} to do", flush=True)
    lock, n, t0 = threading.Lock(), [0], time.time()
    with open(args.out, "a", encoding="utf-8") as f, ThreadPoolExecutor(args.workers) as pool:
        def job(ph):
            s = score_pair(client, args.model, *ph, prompt=args.prompt)
            with lock:
                f.write(json.dumps({"prompt": args.prompt, "model": args.model, "premise": ph[0], "hypothesis": ph[1],
                                    "scores": s}, ensure_ascii=False) + "\n")
                f.flush()
                n[0] += 1
                if n[0] % 500 == 0 or n[0] == len(todo):
                    rate = n[0] / (time.time() - t0)
                    print(f"  {n[0]}/{len(todo)}  {rate:.1f}/s", flush=True)
        list(pool.map(job, todo))
    print("done ->", args.out)


if __name__ == "__main__":
    main()
