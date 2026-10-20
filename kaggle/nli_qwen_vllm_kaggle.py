# Fast version of nli_qwen_kaggle.py using vLLM (tensor parallel over both T4s + prefix caching: each
# question is shared by ~66 propositions, so its prompt prefix is computed once).
# Same prompt, same label letters, same output format -> scores are interchangeable with nli_qwen_kaggle.py
# (up to fp16 numerics).
#
# Kaggle notebook, Accelerator = GPU T4 x2, Internet = On.
#   Cell 1:  !pip install -q vllm
#   Cell 2:  paste this whole file and run.
# Resumable: pairs already in /kaggle/working/nli_scores_qwen.jsonl or in any nli_scores_qwen*.jsonl under
# /kaggle/input (e.g. a partial file from an earlier session uploaded as a dataset) are skipped.

import glob
import json
import math
import os
import sys
import time

MODEL_NAME = os.environ.get("QWEN_MODEL", "Qwen/Qwen2.5-7B-Instruct")
CHUNK = int(os.environ.get("NLI_CHUNK", 2000))

SYSTEM = "Bạn là trợ lý kiểm tra suy luận ngôn ngữ (NLI). Chỉ trả lời bằng một chữ cái."
USER = (
    "Đoạn văn (câu hỏi của người dùng):\n{premise}\n\n"
    "Mệnh đề:\n{hypothesis}\n\n"
    "Chỉ dựa vào nội dung đoạn văn, mệnh đề trên là:\n"
    "A. Đúng — đoạn văn nêu hoặc hàm ý rõ ràng điều này\n"
    "B. Không xác định — đoạn văn không nói đến hoặc không đủ thông tin để biết\n"
    "C. Sai — đoạn văn nêu điều ngược lại\n"
    "Trả lời A, B hoặc C."
)
LABELS = [("A", "entail"), ("B", "neutral"), ("C", "contra")]

args = [a for a in sys.argv[1:] if a.endswith(".jsonl")]
src = args[0] if args else (glob.glob("/kaggle/input/**/pairs_qwen.jsonl", recursive=True) or ["pairs_qwen.jsonl"])[0]
out = args[1] if len(args) > 1 else "/kaggle/working/nli_scores_qwen.jsonl"

pairs = [json.loads(x) for x in open(src, encoding="utf-8") if x.strip()]
done = set()
for f in [out] + glob.glob("/kaggle/input/**/nli_scores_qwen*.jsonl", recursive=True):
    if os.path.exists(f):
        for x in open(f, encoding="utf-8"):
            if x.strip():
                r = json.loads(x)
                done.add((r["premise"], r["hypothesis"]))
todo = list(dict.fromkeys((p["premise"], p["hypothesis"]) for p in pairs if (p["premise"], p["hypothesis"]) not in done))
todo.sort()  # group by question so the shared prefix stays in the cache
print(f"model {MODEL_NAME}; {len(pairs)} pairs, {len(done)} already scored, {len(todo)} to do", flush=True)

import torch
from vllm import LLM, SamplingParams

llm = LLM(model=MODEL_NAME, dtype="half", tensor_parallel_size=max(1, torch.cuda.device_count()),
          enable_prefix_caching=True, max_model_len=2048, gpu_memory_utilization=0.90)
tok = llm.get_tokenizer()
letter_ids = [tok.encode(l, add_special_tokens=False)[0] for l, _ in LABELS]
params = SamplingParams(max_tokens=1, temperature=0.0, logprobs=20)


def prompt(p, h):
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": USER.format(premise=p, hypothesis=h)}]
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


t0 = time.time()
n_missing_letter = 0
with open(out, "a", encoding="utf-8") as f:
    for i in range(0, len(todo), CHUNK):
        chunk = todo[i : i + CHUNK]
        res = llm.generate([prompt(p, h) for p, h in chunk], params, use_tqdm=False)
        for (p, h), r in zip(chunk, res):
            lp = r.outputs[0].logprobs[0]  # token id -> Logprob, top-20 of the first answer token
            raw = []
            for tid in letter_ids:
                if tid in lp:
                    raw.append(lp[tid].logprob)
                else:
                    raw.append(-30.0)  # outside top-20: negligible probability
                    n_missing_letter += 1
            m = max(raw)
            e = [math.exp(x - m) for x in raw]
            s = sum(e)
            f.write(json.dumps({"premise": p, "hypothesis": h,
                                "scores": {lab: v / s for (_, lab), v in zip(LABELS, e)}}, ensure_ascii=False) + "\n")
        f.flush()
        n = min(i + CHUNK, len(todo))
        rate = n / (time.time() - t0)
        print(f"  {n}/{len(todo)}  {rate:.1f} pairs/s  eta {(len(todo) - n) / rate / 60:.1f} min", flush=True)
print("done in", round(time.time() - t0), "s ->", out, "| letters outside top-20:", n_missing_letter)
