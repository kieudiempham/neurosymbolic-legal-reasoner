"""Three-way NLI scores from an open-weight LLM (Qwen2.5-7B-Instruct) on a Kaggle T4 x2 notebook.
Paste the whole file into ONE notebook cell, set PART (and PROMPT) below, run.

PART = "dev"   : scores pairs_qwen_dev.jsonl with every candidate prompt in DEV_PROMPTS (prompt selection,
                 development split only) -> nli_scores_qwen_dev.jsonl
PART = 1..4    : scores pairs_qwen_part{PART}.jsonl with PROMPT -> nli_scores_qwen_part{PART}.jsonl
Then locally:  NLI_BACKEND=qwen python -m diagnosis.nli_gpu import <file>

The next-token probabilities of the option letters (A = entailed, B = not determined, C = contradicted)
are renormalised into label scores, so the acceptance test (threshold tau) works as with an NLI
classifier. One forward pass per pair, no sampling: deterministic. Resumable within a session.
Notebook settings: Accelerator = GPU T4 x2, Internet = On.
"""

PART = "dev"  # <<< "dev" first; then 1, 2, 3, 4 (one run per part, ~17 min each)
PROMPT = "v2"  # <<< prompt used for parts 1-4 (the one chosen on dev)

import glob
import json
import os
import sys
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = os.environ.get("QWEN_MODEL", "Qwen/Qwen2.5-7B-Instruct")
BATCH = int(os.environ.get("NLI_BATCH", 16))
SYSTEM = "Bạn là trợ lý kiểm tra suy luận ngôn ngữ (NLI). Chỉ trả lời bằng một chữ cái."
PROMPTS = {
    # v1: first run (too literal: "I" vs "the worker", "9 months" vs "at least 1 month" -> B)
    "v1": (
        "Đoạn văn (câu hỏi của người dùng):\n{premise}\n\n"
        "Mệnh đề:\n{hypothesis}\n\n"
        "Chỉ dựa vào nội dung đoạn văn, mệnh đề trên là:\n"
        "A. Đúng — đoạn văn nêu hoặc hàm ý rõ ràng điều này\n"
        "B. Không xác định — đoạn văn không nói đến hoặc không đủ thông tin để biết\n"
        "C. Sai — đoạn văn nêu điều ngược lại\n"
        "Trả lời A, B hoặc C."
    ),
    # v2: the asker is the party of the proposition; obvious inferences (numbers, periods, paraphrase) count
    "v2": (
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
    ),
    # v3: v2 + three generic worked examples (invented, not taken from the dataset)
    "v3": (
        "Ví dụ:\n"
        "- Đoạn văn: \"Tôi ký hợp đồng 6 tháng với công ty.\" Mệnh đề: \"Hợp đồng có thời hạn từ đủ 03 tháng trở lên.\" -> A\n"
        "- Đoạn văn: \"Tôi là người Việt Nam, làm kế toán.\" Mệnh đề: \"Người lao động là công dân nước ngoài.\" -> C\n"
        "- Đoạn văn: \"Tôi làm kế toán ở Hà Nội.\" Mệnh đề: \"Người lao động đã đóng bảo hiểm đủ 20 năm.\" -> B\n\n"
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
    ),
}
DEV_PROMPTS = ["v2", "v3"]
LABELS = [("A", "entail"), ("B", "neutral"), ("C", "contra")]

args = [a for a in sys.argv[1:] if a.endswith(".jsonl")]  # notebook kernels pass "-f kernel-....json"
name = "dev" if PART == "dev" else f"part{PART}"
src = args[0] if args else (glob.glob(f"/kaggle/input/**/pairs_qwen_{name}.jsonl", recursive=True) or [f"pairs_qwen_{name}.jsonl"])[0]
out = args[1] if len(args) > 1 else f"/kaggle/working/nli_scores_qwen_{name}.jsonl"
prompts = DEV_PROMPTS if PART == "dev" else [PROMPT]
print("model:", MODEL_NAME, "input:", src, "output:", out, "prompts:", prompts, "gpus:", torch.cuda.device_count())

pairs = [json.loads(x) for x in open(src, encoding="utf-8") if x.strip()]
done = set()
if os.path.exists(out):
    for x in open(out, encoding="utf-8"):
        if x.strip():
            r = json.loads(x)
            done.add((r["prompt"], r["premise"], r["hypothesis"]))
todo = list(dict.fromkeys((v, p["premise"], p["hypothesis"]) for v in prompts for p in pairs
                          if (v, p["premise"], p["hypothesis"]) not in done))
print(f"{len(pairs)} pairs x {len(prompts)} prompts, {len(done)} already scored, {len(todo)} to do")

tok = AutoTokenizer.from_pretrained(MODEL_NAME)
tok.padding_side = "left"
if tok.pad_token is None:
    tok.pad_token = tok.eos_token
cuda = torch.cuda.is_available()
if "model" not in globals():  # re-running the cell (next PART) reuses the model already on the GPUs
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, torch_dtype=torch.float16 if cuda else torch.float32,
        device_map="auto" if cuda else None,
        max_memory={i: "14GiB" for i in range(torch.cuda.device_count())} if cuda else None,
    ).eval()
label_ids = []
for letter, _ in LABELS:
    ids = tok.encode(letter, add_special_tokens=False)
    assert len(ids) == 1, (letter, ids)
    label_ids.append(ids[0])


def prompt(v: str, p: str, h: str) -> str:
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": PROMPTS[v].format(premise=p, hypothesis=h)}]
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


todo.sort(key=lambda vph: (vph[0], len(vph[1]) + len(vph[2])))
first_device = next(model.parameters()).device
t0 = time.time()
with open(out, "a", encoding="utf-8") as f:
    for i in range(0, len(todo), BATCH):
        chunk = todo[i : i + BATCH]
        enc = tok([prompt(v, p, h) for v, p, h in chunk], return_tensors="pt", padding=True).to(first_device)
        with torch.inference_mode():
            logits = model(**enc).logits[:, -1, :].float()
        probs = torch.softmax(logits[:, label_ids], dim=-1).tolist()
        for (v, p, h), row in zip(chunk, probs):
            f.write(json.dumps({"prompt": v, "premise": p, "hypothesis": h,
                                "scores": {lab: s for (_, lab), s in zip(LABELS, row)}}, ensure_ascii=False) + "\n")
        f.flush()
        n = min(i + BATCH, len(todo))
        if (i // BATCH) % 50 == 0 or n == len(todo):
            rate = n / (time.time() - t0)
            print(f"  {n}/{len(todo)}  {rate:.1f} pairs/s  eta {(len(todo) - n) / rate / 60:.1f} min", flush=True)
print("done in", round(time.time() - t0), "s ->", out)
try:  # download link for the result file (notebook only)
    from IPython.display import FileLink, display

    os.chdir(os.path.dirname(out))
    display(FileLink(os.path.basename(out)))
except Exception:
    pass
