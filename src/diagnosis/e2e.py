"""End-to-end QA on the 300 questions with the real GPT-4o parser, plus the pure GPT-4o baseline.

    PYTHONPATH=src NLI_BACKEND=ensemble_gpt NLI_TAU=0.5 NLI_RULE=pos_only .venv_diag/Scripts/python -m diagnosis.e2e

Methods (same domain KBs, oracle goal as in the paper):
  gpt4o      pure LLM: question only -> verdict + IRAC (no KB, no retrieval, no gold facts)
  symbolic   GPT-4o parser -> KB -> reasoner (no diagnosis)
  heuristic  + IF-THEN diagnosis and recovery
  ours       + cross-layer MBD diagnosis and recovery
No simulated user here: a clarification request is the answer "insufficient" (the user is not asked).
Writes experiments/e2e/qa_results.json and experiments/e2e/irac_answers.json (40 stratified questions,
IRAC text of every method, for diagnosis.irac_judge).
"""

from __future__ import annotations

import json
import random
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .ask import ANSWER_PROMPT, VERDICT, describe_rule, proof_rules
from .controller import Diagnoser, RunConfig
from .external_diag import DOMAINS, load_domains
from .llm_parser import LLMParser
from .nli import NLIModel
from .reasoner import backward_trace_required

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "e2e"
METHODS = {"symbolic": RunConfig(diagnosis=False), "heuristic": RunConfig(rule_check=True), "ours": RunConfig()}
SEED = 20261020

BASELINE_PROMPT = """Bạn là luật sư tư vấn pháp luật Việt Nam. Trả lời câu hỏi của người dùng theo pháp luật Việt Nam hiện hành (năm 2026), theo cấu trúc IRAC.

Quy ước kết luận:
- "CÓ" hoặc "KHÔNG" khi các dữ kiện câu hỏi nêu đủ để kết luận.
- "CHƯA ĐỦ DỮ KIỆN" khi thiếu một điều kiện pháp lý quyết định; khi đó nêu rõ cần bổ sung thông tin gì.
- Ngoại lệ mà câu hỏi hoàn toàn không nhắc tới thì coi như không áp dụng; ngoại lệ được nhắc tới một phần mà còn thiếu điều kiện quyết định thì kết luận "CHƯA ĐỦ DỮ KIỆN".

Câu hỏi: {question}

Chỉ trả về JSON: {{"verdict": "CÓ" | "KHÔNG" | "CHƯA ĐỦ DỮ KIỆN", "issue": "...", "rule": "...", "application": "...", "conclusion": "..."}}"""


def norm_verdict(v: str) -> str:
    v = (v or "").strip().upper()
    if v in ("TRUE", "CÓ", "CO"):
        return "true"
    if v in ("FALSE", "KHÔNG", "KHONG"):
        return "false"
    if v in ("INSUFFICIENT", "CLARIFICATION_REQUESTED") or "CHƯA ĐỦ" in v:
        return "insufficient"
    return "abstain" if v == "ABSTAIN" else "other"


def llm_many(parser: LLMParser, jobs: list[tuple[str, str]], model: str, workers: int = 12) -> None:
    """Fill parser.cache[key] for every (key, prompt) not cached yet, in parallel (JSON responses)."""
    todo = list(dict.fromkeys(k for k, _ in jobs if k not in parser.cache))
    prompts = dict(jobs)

    def call(k: str):
        for attempt in range(10):
            try:
                r = parser.client.chat.completions.create(
                    model=model, temperature=0.0, top_p=1.0, response_format={"type": "json_object"},
                    messages=[{"role": "user", "content": prompts[k]}])
                return k, json.loads(r.choices[0].message.content)
            except Exception as e:  # rate limit / transient
                if "insufficient_quota" in str(e):  # out of credits: retrying cannot help
                    raise RuntimeError("OpenAI credits exhausted; top up and re-run (finished calls are cached)") from e
                time.sleep(min(60, 3 * 2 ** attempt))
                last = e
        raise RuntimeError(f"LLM call failed: {k[:80]} ({last})")

    t0 = time.time()
    try:
        with ThreadPoolExecutor(workers) as pool:
            for n, (k, v) in enumerate(pool.map(call, todo), 1):
                parser.cache[k] = v
                if n % 50 == 0:
                    print(f"    {n}/{len(todo)} ({time.time() - t0:.0f}s)", flush=True)
                    parser.save()
    finally:  # keep what was already paid for, even if a later call fails (e.g. quota exhausted)
        parser.save()


def select_irac(items: dict, split: dict, n_per_domain: int = 8) -> list[str]:
    rng = random.Random(SEED)
    chosen = []
    for dom in DOMAINS:
        its = [it for it in items.values() if it["domain"] == dom]
        test = [it for it in its if split[it["id"]] == "test"] or its
        by = defaultdict(list)
        for it in sorted(test, key=lambda x: x["id"]):
            by[it["expected"]].append(it["id"])
        for v in by.values():
            rng.shuffle(v)
        quota = {"true": 3, "false": 3, "insufficient": 2}
        pick = [i for lab, q in quota.items() for i in by[lab][:q]]
        rest = [i for lab in by for i in by[lab] if i not in pick]
        pick += rest[: n_per_domain - len(pick)]
        chosen += pick[:n_per_domain]
    return chosen


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    kbs, items, split = load_domains()
    parsers = {dom: LLMParser(kbs[dom]) for dom in DOMAINS}
    shared = parsers["bhxh"].cache
    for p in parsers.values():
        p.cache = shared
    any_p = parsers["bhxh"]
    irac_ids = set(select_irac(items, split))
    if "--irac-all" in sys.argv:  # IRAC for every question (written to irac_answers_all.json)
        irac_ids = set(items)
    # --test-only: the held-out test questions plus the IRAC sample (social insurance has no test split)
    order = sorted(i for i in items if "--test-only" not in sys.argv or split[i] == "test" or i in irac_ids)
    print(f"{len(order)} questions", flush=True)

    # 1. parse every question with its domain KB vocabulary (GPT-4o, cached)
    import hashlib

    from .llm_parser import PARSE_PROMPT

    jobs = []
    for iid in order:
        p = parsers[items[iid]["domain"]]
        tag = hashlib.sha1(p.pred_list.encode("utf-8")).hexdigest()[:10]
        q = items[iid]["question"]
        jobs.append((f"parse|{p.model}|{tag}|{q}", PARSE_PROMPT.format(predicates=p.pred_list, question=q)))
    print(f"parsing {len(order)} questions", flush=True)
    llm_many(any_p, jobs, any_p.model)

    # 2. pure GPT-4o baseline
    print("GPT-4o baseline", flush=True)
    bjobs = [(f"baseline|gpt-4o|{items[i]['question']}", BASELINE_PROMPT.format(question=items[i]["question"])) for i in order]
    llm_many(any_p, bjobs, "gpt-4o")

    # 3. symbolic / heuristic / ours
    nli = NLIModel()
    rows, ver_jobs, irac_meta = [], [], {}
    tp = fp = fn = 0
    for iid in order:
        it = items[iid]
        dom, kb, p = it["domain"], kbs[it["domain"]], parsers[it["domain"]]
        parsed = p.parse(it["question"])
        gold = {f["pred"]: bool(f["value"]) for f in it["facts"]}
        tp += sum(1 for c, f in parsed.items() if gold.get(c) == f.value)
        fp += sum(1 for c, f in parsed.items() if gold.get(c) != f.value)
        fn += sum(1 for c in gold if c not in parsed or parsed[c].value != gold[c])
        goal = it["goal"]["pred"]
        b = any_p.cache[f"baseline|gpt-4o|{it['question']}"]
        row = {"id": iid, "domain": dom, "split": split[iid], "expected": it["expected"],
               "parsed": {c: f.value for c, f in parsed.items()},
               "gpt4o": norm_verdict(b.get("verdict", ""))}
        for name, cfg in METHODS.items():
            res = Diagnoser(kb, nli, cfg).run(it["question"], goal, dict(parsed), lambda c: None)
            row[name] = norm_verdict(res.answer)
            row[f"{name}_diagnosis"] = res.first_diagnosis
            if iid in irac_ids:
                st = res.final_state
                rules = proof_rules(kb, st)
                facts = "\n".join(
                    f"- {kb.vocab[c]['template_pos' if f.value else 'template_neg']}"
                    for c, f in st.facts.items() if f.origin != "derived" and kb.vocab[c].get("kind") == "input"
                    and f.origin != "default") or "- (không có)"
                extra = ""
                if res.answer in ("insufficient", "clarification_requested"):
                    extra = "Thông tin còn thiếu cần người dùng bổ sung:\n" + "\n".join(
                        f"- {kb.vocab[c]['ask']}" for c in backward_trace_required(kb, st))
                key = f"answer|{p.model}|{it['question']}|{res.answer}|{'|'.join(rules)}|{facts}"
                ver_jobs.append((key, ANSWER_PROMPT.format(
                    question=it["question"], goal=kb.vocab[goal]["template_pos"], verdict=VERDICT[res.answer],
                    facts=facts, rules="\n".join(describe_rule(kb, r, st) for r in rules) or "- (không có)", extra=extra)))
                irac_meta[(iid, name)] = key
        rows.append(row)
    nli.save()

    # 4. IRAC verbalisation of the proof for the 40 selected questions (same prompt for the 3 KB-based methods)
    print(f"verbalising {len(ver_jobs)} IRAC answers", flush=True)
    llm_many(any_p, ver_jobs, any_p.model)

    # summaries
    names = ["gpt4o", *METHODS]
    summ = {}
    for subset, sel in (("all", rows), ("dev", [r for r in rows if r["split"] == "dev"]),
                        ("test", [r for r in rows if r["split"] == "test"])):
        summ[subset] = {m: round(sum(r[m] == r["expected"] for r in sel) / max(1, len(sel)), 4) for m in names}
        summ[subset]["n"] = len(sel)
    summ["by_domain_test_or_all"] = {}
    for dom in DOMAINS:
        sel = [r for r in rows if r["domain"] == dom and (r["split"] == "test" or dom == "bhxh")]
        summ["by_domain_test_or_all"][dom] = {m: round(sum(r[m] == r["expected"] for r in sel) / max(1, len(sel)), 4)
                                              for m in names} | {"n": len(sel)}
    summ["by_gold_label_all"] = {lab: {m: round(sum(r[m] == lab for r in rows if r["expected"] == lab)
                                                / max(1, sum(r["expected"] == lab for r in rows)), 4) for m in names}
                                 for lab in ("true", "false", "insufficient")}
    summ["verdict_distribution"] = {m: dict(Counter(r[m] for r in rows)) for m in names}
    summ["parser"] = {"precision": round(tp / max(1, tp + fp), 4), "recall": round(tp / max(1, tp + fn), 4)}
    if "--irac-all" not in sys.argv:
      (OUT / "qa_results.json").write_text(json.dumps({"summary": summ, "rows": rows}, ensure_ascii=False, indent=1),
                                         encoding="utf-8")

    irac = []
    for iid in sorted(irac_ids):
        it = items[iid]
        b = any_p.cache[f"baseline|gpt-4o|{it['question']}"]
        ans = {"gpt4o": {k: b.get(k, "") for k in ("issue", "rule", "application", "conclusion")}}
        for name in METHODS:
            v = any_p.cache[irac_meta[(iid, name)]]
            ans[name] = {k: v.get(k, "") for k in ("issue", "rule", "application", "conclusion")}
        irac.append({"id": iid, "domain": it["domain"], "split": split[iid], "question": it["question"],
                     "gold_expected": it["expected"], "gold_missing": it.get("missing_facts") or [],
                     "gold_legal_basis": it.get("legal_basis") or [], "answers": ans})
    name = "irac_answers_all.json" if "--irac-all" in sys.argv else "irac_answers.json"
    (OUT / name).write_text(json.dumps(irac, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summ, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
