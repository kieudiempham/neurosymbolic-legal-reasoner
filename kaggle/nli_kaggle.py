"""NLI scoring on a Kaggle GPU notebook (T4 x2) — paste this whole file into ONE notebook cell and run.

Input : pairs.jsonl  ({"premise", "hypothesis"} per line), uploaded as a Kaggle Dataset
        (auto-detected anywhere under /kaggle/input).
Output: /kaggle/working/nli_scores.jsonl  ({"premise", "hypothesis", "scores": {entail, neutral, contra}})
        -> download it, then locally:  python -m diagnosis.nli_gpu import nli_scores.jsonl

Same model, tokenizer settings (max_length=256, truncation) and label mapping as src/diagnosis/nli.py,
fp32 by default so scores match the CPU run. Resumable: pairs already in the output file are skipped.
Notebook settings: Accelerator = GPU T4 x2, Internet = On (to download the model from Hugging Face).
"""

import glob
import json
import os
import sys
import time

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
LABEL = {"entailment": "entail", "neutral": "neutral", "contradiction": "contra"}
BATCH = int(os.environ.get("NLI_BATCH", 128))
FP16 = os.environ.get("NLI_FP16", "0") == "1"

args = [a for a in sys.argv[1:] if a.endswith(".jsonl")]  # notebook kernels pass "-f kernel-....json"
src = args[0] if args else (glob.glob("/kaggle/input/**/pairs.jsonl", recursive=True) or ["pairs.jsonl"])[0]
out = args[1] if len(args) > 1 else "/kaggle/working/nli_scores.jsonl"
print("input:", src, "output:", out, "gpus:", torch.cuda.device_count(), "fp16:", FP16)

pairs = [json.loads(x) for x in open(src, encoding="utf-8") if x.strip()]
done = set()
if os.path.exists(out):
    for x in open(out, encoding="utf-8"):
        if x.strip():
            r = json.loads(x)
            done.add((r["premise"], r["hypothesis"]))
todo = list(dict.fromkeys((p["premise"], p["hypothesis"]) for p in pairs if (p["premise"], p["hypothesis"]) not in done))
print(f"{len(pairs)} pairs, {len(done)} already scored, {len(todo)} to do")

tok = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME).eval()
id2label = [LABEL[model.config.id2label[j].lower()] for j in range(model.config.num_labels)]
dev = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(dev)
if FP16 and dev == "cuda":
    model = model.half()
if torch.cuda.device_count() > 1:
    model = torch.nn.DataParallel(model)

# sort by length so each batch pads little (results do not depend on batch composition)
todo.sort(key=lambda ph: len(ph[0]) + len(ph[1]))
t0 = time.time()
with open(out, "a", encoding="utf-8") as f:
    for i in range(0, len(todo), BATCH):
        chunk = todo[i : i + BATCH]
        prem, hyp = zip(*chunk)
        enc = tok(list(prem), list(hyp), return_tensors="pt", truncation=True, max_length=256, padding=True)
        enc = {k: v.to(dev) for k, v in enc.items()}
        with torch.inference_mode():
            probs = torch.softmax(model(**enc).logits.float(), dim=-1).tolist()
        for (p, h), row in zip(chunk, probs):
            f.write(json.dumps({"premise": p, "hypothesis": h,
                                "scores": {id2label[j]: v for j, v in enumerate(row)}}, ensure_ascii=False) + "\n")
        f.flush()
        n = min(i + BATCH, len(todo))
        if (i // BATCH) % 20 == 0 or n == len(todo):
            rate = n / (time.time() - t0)
            print(f"  {n}/{len(todo)}  {rate:.0f} pairs/s  eta {(len(todo) - n) / rate / 60:.1f} min", flush=True)
print("done in", round(time.time() - t0), "s ->", out)
