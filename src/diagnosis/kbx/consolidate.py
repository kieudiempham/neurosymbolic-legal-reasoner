"""Consolidate the predicate vocabulary of the draft KB so rules share predicates and can chain.

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.kbx.consolidate

Steps:
  1. declare: undeclared predicates get template_pos/neg/ask/kind from the LLM (one rule quote as context);
  2. embed: template_pos of every predicate with a multilingual sentence encoder (CPU);
  3. cluster: average-linkage agglomerative clustering on cosine distance (candidate near-duplicates);
  4. confirm: the LLM splits each candidate cluster into groups of the SAME legal proposition (or its exact negation)
     and picks a canonical member name (curated names from data/diag/vocabulary.yaml win);
  5. rewrite rules with canonical literals and write the consolidated vocabulary.

Input:  data/diag/kb_full_draft/{rules.jsonl, vocabulary.yaml}
Output: data/diag/kb_full_draft/{rules_consolidated.jsonl, vocabulary_consolidated.yaml, consolidation_stats.json,
        consolidation_merges.jsonl}  (draft, NOT manually reviewed)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import yaml
from dotenv import load_dotenv
from openai import OpenAI

from .corpus import ROOT

KB = ROOT / "data" / "diag" / "kb_full_draft"
CURATED = ROOT / "data" / "diag" / "vocabulary.yaml"
CACHE = ROOT / "experiments" / "kbx" / "consolidate"
MODEL = "gpt-4o-mini"
EMBED_MODEL = "intfloat/multilingual-e5-base"
PRICE_IN, PRICE_OUT = 0.15 / 1e6, 0.60 / 1e6  # USD per token (gpt-4o-mini list price)
SIM = 0.955       # average-linkage cosine similarity threshold for candidate clusters (e5 similarities are compressed)
MAX_CLUSTER = 8   # larger candidate clusters are re-split with a stricter threshold (keeps <= 28 pairs per call)

DECLARE_PROMPT = """Bạn khai báo predicate cho cơ sở tri thức pháp luật Việt Nam (luật Horn).
Mỗi predicate dưới đây đang được dùng trong luật nhưng chưa có mô tả. Với mỗi predicate, dựa vào tên và trích dẫn văn bản,
viết một mệnh đề tiếng Việt ngắn, cụ thể (chủ thể + nội dung), đúng như nghĩa được dùng trong luật.

{items}

kind = "input" nếu là dữ kiện vụ việc người dùng có thể cho biết; "derived" nếu là kết luận/hệ quả pháp lý.
ask = câu hỏi người dùng (chỉ cho input, còn lại để rỗng).

Chỉ trả về JSON: {{"preds": [{{"pred": "...", "kind": "input|derived", "template_pos": "<câu khi đúng>",
                              "template_neg": "<câu khi sai>", "ask": "..."}}]}}"""

PAIR_PROMPT = """Bạn hợp nhất từ vựng predicate của một cơ sở tri thức pháp luật Việt Nam (luật Horn).
Các predicate dưới đây có câu mô tả gần giống nhau (theo embedding), nhưng phần lớn là KHÁC nhau.

{items}

Với MỖI cặp dưới đây, so sánh hai mệnh đề và gán nhãn:
- "same": hai mệnh đề là MỘT mệnh đề pháp lý (chỉ khác cách diễn đạt): thay tên này bằng tên kia trong MỌI luật không đổi nghĩa.
- "negation": mệnh đề này đúng KHI VÀ CHỈ KHI mệnh đề kia sai (phủ định chính xác, ví dụ "đã ký hợp đồng" / "chưa ký hợp đồng").
- "different": mọi trường hợp còn lại.
Trước khi gán nhãn, ghi rõ điểm khác nhau (nếu có) về: chủ thể / cơ quan; đối tượng (loại hồ sơ, giấy tờ, mẫu biểu, loại thuế,
loại bảo hiểm, ngành nghề...); con số, ngưỡng, thời hạn, tỷ lệ; điều/khoản tham chiếu; phương thức (được / phải / không được);
giai đoạn (đề nghị / đã được chấp thuận, nộp / cấp); phạm vi (một phần / toàn bộ, chung / trường hợp riêng).
Có BẤT KỲ điểm khác nào trong số đó thì nhãn là "different". "Gần nghĩa", "bao hàm", "liên quan", "cùng chủ đề",
"là hệ quả của" đều là "different". Nếu phân vân, chọn "different".

Các cặp:
{pairs}

Chỉ trả về JSON: {{"pairs": [{{"pair": <số thứ tự>, "khac_biet": "<điểm khác nhau cụ thể, rỗng nếu không có>",
                              "label": "same|negation|different"}}]}}"""

CANON_PROMPT = """Các predicate sau đã được xác nhận là cùng một mệnh đề pháp lý (một số có thể là dạng phủ định của nhau).
Chọn MỘT tên làm tên chuẩn (canonical) cho cả nhóm: ưu tiên dạng khẳng định (không bắt đầu bằng not_/no_/non_),
tên tiếng Anh rõ nghĩa, đủ cụ thể, tổng quát và được dùng nhiều.

{items}

Chỉ trả về JSON: {{"canonical": "<một tên trong danh sách>", "reason": "<ngắn>"}}"""

VERIFY_PROMPT = """Bạn kiểm tra trùng lặp trong từ vựng predicate của một cơ sở tri thức pháp luật Việt Nam.
Mỗi predicate có tên (tiếng Anh), câu mô tả khi đúng / khi sai, và trích dẫn văn bản luật nơi nó được dùng.
Câu mô tả có thể viết sơ sài: hãy dựa vào CẢ tên lẫn trích dẫn. Nếu tên hoặc trích dẫn cho thấy hai predicate nói về
đối tượng, trường hợp, điểm/khoản, con số, chủ thể hay giai đoạn khác nhau thì chúng KHÁC nhau dù câu mô tả giống hệt.

Với mỗi cặp, chọn đúng một nhãn:
- "same": cùng một mệnh đề pháp lý, thay tên này bằng tên kia trong mọi luật không làm đổi nghĩa;
- "negation": P1 đúng khi và chỉ khi P2 sai (phủ định chính xác);
- "different": còn lại (kể cả gần nghĩa, bao hàm, cùng chủ đề, một bên rộng hơn bên kia). Phân vân thì chọn "different".

{pairs}

Chỉ trả về JSON: {{"pairs": [{{"pair": <số thứ tự>, "ly_do": "<ngắn>", "label": "same|negation|different"}}]}}"""


def _strip(lit: str) -> tuple[str, bool]:
    return (lit[1:], False) if lit.startswith("~") else (lit, True)


def _lit(pred: str, pos: bool) -> str:
    return pred if pos else f"~{pred}"


class LLM:
    def __init__(self, model: str = MODEL):
        load_dotenv(ROOT / ".env")
        self.client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.environ.get("LLM_BASE_URL") or None)
        self.model = model
        self.usage = Counter()
        self.lock = threading.Lock()
        CACHE.mkdir(parents=True, exist_ok=True)

    def chat(self, tag: str, prompt: str) -> dict:
        key = hashlib.sha1(f"{tag}|{self.model}|{prompt}".encode()).hexdigest()
        f = CACHE / f"{tag}_{key}.json"
        if f.exists():  # cached calls still count toward the reported cost of building the KB
            rec = json.loads(f.read_text(encoding="utf-8"))
            with self.lock:
                self.usage["cached"] += 1
                self.usage["in"] += rec["tokens_in"]
                self.usage["out"] += rec["tokens_out"]
            return rec["response"]
        for attempt in range(12):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model, temperature=0.0, top_p=1.0, response_format={"type": "json_object"},
                    messages=[{"role": "user", "content": prompt}])
                out = json.loads(resp.choices[0].message.content)
                with self.lock:
                    self.usage["in"] += resp.usage.prompt_tokens
                    self.usage["out"] += resp.usage.completion_tokens
                    self.usage["calls"] += 1
                f.write_text(json.dumps({"response": out, "tokens_in": resp.usage.prompt_tokens,
                                         "tokens_out": resp.usage.completion_tokens}, ensure_ascii=False),
                             encoding="utf-8")
                return out
            except json.JSONDecodeError:
                time.sleep(1)
            except Exception as e:  # rate limits: back off and retry
                wait = min(60, 3 * 2 ** attempt)
                print(f"   retry {attempt} in {wait}s: {type(e).__name__}", flush=True)
                time.sleep(wait)
        raise RuntimeError(f"LLM call failed: {tag}")

    def cost(self) -> float:
        return self.usage["in"] * PRICE_IN + self.usage["out"] * PRICE_OUT


# ---------------------------------------------------------------- metrics

def kb_metrics(rules: list[dict], vocab: dict) -> dict:
    uses, doms = Counter(), defaultdict(set)
    for r in rules:
        for p in {_strip(x)[0] for x in r["premises"] + [r["conclusion"]]}:
            uses[p] += 1
            doms[p].add(r["domain"])
    concl = {r["conclusion"] for r in rules}
    derivable = sum(any(p in concl for p in r["premises"]) for r in rules)
    return {
        "rules": len(rules),
        "predicates_used": len(uses),
        "predicates_declared": len(vocab),
        "predicates_used_by_2plus_rules": sum(c >= 2 for c in uses.values()),
        "reuse_rate": round(sum(c >= 2 for c in uses.values()) / max(1, len(uses)), 4),
        "mean_rules_per_predicate": round(sum(uses.values()) / max(1, len(uses)), 3),
        "cross_domain_shared_predicates": sum(len(d) > 1 for d in doms.values()),
        "rules_with_premise_derivable_by_another_rule": derivable,
        "rules_with_premise_derivable_pct": round(derivable / max(1, len(rules)), 4),
        "rules_with_undeclared_predicates": sum(
            any(_strip(x)[0] not in vocab for x in r["premises"] + [r["conclusion"]]) for r in rules),
        "undeclared_predicates": sum(p not in vocab for p in uses),
    }


# ---------------------------------------------------------------- steps

def declare(llm: LLM, rules: list[dict], vocab: dict, workers: int) -> dict:
    """LLM templates for predicates used in rules but missing from the vocabulary."""
    ctx: dict[str, dict] = {}
    for r in rules:
        for role, lits in (("điều kiện", r["premises"]), ("kết luận", [r["conclusion"]])):
            for x in lits:
                p, pos = _strip(x)
                if p not in vocab and p not in ctx:
                    ctx[p] = {"role": role, "neg": not pos, "domain": r["domain"], "quote": r["quote"][:200],
                              "source": r["source"]}
    preds = sorted(ctx)
    batches = [preds[i:i + 30] for i in range(0, len(preds), 30)]
    print(f"declare: {len(preds)} undeclared predicates, {len(batches)} calls", flush=True)

    def work(batch):
        items = "\n".join(
            f"- {p} (dùng làm {ctx[p]['role']}{', dạng phủ định' if ctx[p]['neg'] else ''}; lĩnh vực {ctx[p]['domain']}; "
            f"{ctx[p]['source']}): \"{ctx[p]['quote']}\"" for p in batch)
        out = llm.chat("declare", DECLARE_PROMPT.format(items=items))
        return {e.get("pred"): e for e in out.get("preds") or [] if isinstance(e, dict)}

    declared = {}
    with ThreadPoolExecutor(workers) as pool:
        for batch, got in zip(batches, pool.map(work, batches)):
            for p in batch:
                e = got.get(p) or {}
                if e.get("template_pos"):
                    declared[p] = {"kind": e.get("kind") if e.get("kind") in ("input", "derived") else "derived",
                                   "template_pos": str(e["template_pos"]), "template_neg": str(e.get("template_neg") or ""),
                                   "ask": str(e.get("ask") or ""), "domains": [ctx[p]["domain"]],
                                   "origin": "llm_declared"}
    return declared


def embed(texts: list[str]) -> np.ndarray:
    """Normalised e5 embeddings, cached per text."""
    f = CACHE / "embeddings.npz"
    cache = dict(np.load(f, allow_pickle=False)) if f.exists() else {}
    keys = [hashlib.sha1(f"{EMBED_MODEL}|{t}".encode()).hexdigest() for t in texts]
    todo = sorted({k: t for k, t in zip(keys, texts) if k not in cache}.items())
    if todo:
        from sentence_transformers import SentenceTransformer

        print(f"embed: {len(todo)} new texts with {EMBED_MODEL} (CPU)", flush=True)
        m = SentenceTransformer(EMBED_MODEL, device="cpu")
        vecs = m.encode([f"query: {t}" for _, t in todo], batch_size=64, normalize_embeddings=True,
                        show_progress_bar=False)
        cache.update({k: v.astype(np.float32) for (k, _), v in zip(todo, vecs)})
        np.savez(f, **cache)
    return np.stack([cache[k] for k in keys])


def cluster(E: np.ndarray, sim: float = SIM) -> list[list[int]]:
    """Average-linkage clusters of size >= 2; oversized ones are re-split with a stricter threshold."""
    from sklearn.cluster import AgglomerativeClustering

    def run(idx: list[int], s: float) -> list[list[int]]:
        if len(idx) < 2:
            return []
        labels = AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average",
                                         distance_threshold=1 - s).fit_predict(E[idx])
        groups = defaultdict(list)
        for i, lab in zip(idx, labels):
            groups[lab].append(i)
        out = []
        for g in groups.values():
            if len(g) > MAX_CLUSTER and s < 0.995:
                out += run(g, s + 0.005)
            elif len(g) >= 2:
                out.append(g)
        return out

    return run(list(range(len(E))), sim)


def _desc(p: str, vocab: dict, uses: Counter, quotes: dict, curated: set) -> str:
    v = vocab[p]
    return (f"{p}{' [curated]' if p in curated else ''} ({v.get('kind')}, {'/'.join(v.get('domains', []))}, "
            f"dùng trong {uses[p]} luật): khi đúng = \"{v.get('template_pos', '')}\"; "
            f"khi sai = \"{v.get('template_neg', '')}\"; ví dụ: \"{quotes.get(p, '')[:140]}\"")


def confirm(llm: LLM, clusters: list[list[str]], vocab: dict, uses: Counter, quotes: dict, examples: dict,
            curated: set, workers: int) -> tuple[list[dict], Counter]:
    """Merge groups confirmed in three LLM passes.

    A. every pair of a candidate cluster is labelled same / negation / different (differences listed first);
    B. each same/negation pair is re-judged by a second, pair-only prompt that also sees two rule quotes per
       predicate (templates are sometimes too generic); the pair is kept only if both labels agree;
    C. groups are cliques of pairs that passed both checks with consistent polarity; the LLM picks the
       canonical name, except that a curated name always wins and a group holds at most one curated predicate.
    """
    n_pairs = Counter()

    def pairs_of(names):
        return [(a, b) for i, a in enumerate(names) for b in names[i + 1:]]

    def stage_a(names: list[str]) -> list[tuple[str, str, bool]]:
        pairs = pairs_of(names)
        items = "\n".join(f"- {_desc(p, vocab, uses, quotes, curated)}" for p in names)
        plist = "\n".join(f"{k}. {a} | {b}" for k, (a, b) in enumerate(pairs, 1))
        out = llm.chat("pair", PAIR_PROMPT.format(items=items, pairs=plist))
        got = []
        for e in out.get("pairs") or []:
            k = e.get("pair") if isinstance(e, dict) else None
            if isinstance(k, int) and 1 <= k <= len(pairs) and e.get("label") in ("same", "negation"):
                got.append((*pairs[k - 1], e["label"] == "negation"))
        return got

    def stage_b(batch: list[tuple[str, str, bool]]) -> list[bool]:
        def show(tag, p):
            v = vocab[p]
            ex = "; ".join(f"\"{q[:160]}\" ({src})" for q, src in examples.get(p, [])[:2])
            return (f"   {tag} = {p}: khi đúng \"{v.get('template_pos', '')}\"; khi sai \"{v.get('template_neg', '')}\""
                    f"\n        trích dẫn: {ex}")
        plist = "\n".join(f"{k}.\n{show('P1', a)}\n{show('P2', b)}" for k, (a, b, _) in enumerate(batch, 1))
        out = llm.chat("verify2", VERIFY_PROMPT.format(pairs=plist))
        lab = {e.get("pair"): e.get("label") for e in out.get("pairs") or [] if isinstance(e, dict)}
        return [lab.get(k) == ("negation" if neg else "same") for k, (_, _, neg) in enumerate(batch, 1)]

    print(f"confirm A: {len(clusters)} clusters, {sum(len(pairs_of(c)) for c in clusters)} pairs", flush=True)
    with ThreadPoolExecutor(workers) as pool:
        cand = [e for es in pool.map(stage_a, clusters) for e in es]
    batches = [cand[i:i + 8] for i in range(0, len(cand), 8)]
    print(f"confirm B: {len(cand)} candidate pairs ({sum(e[2] for e in cand)} negation), {len(batches)} calls", flush=True)
    with ThreadPoolExecutor(workers) as pool:
        verdicts = [v for vs in pool.map(stage_b, batches) for v in vs]
    with open(CACHE / "pair_decisions.jsonl", "w", encoding="utf-8") as fh:  # audit trail for spot checks
        for (a, b, neg), ok in zip(cand, verdicts):
            fh.write(json.dumps({"a": a, "b": b, "negation": neg, "verified": ok,
                                 "a_pos": vocab[a].get("template_pos"), "b_pos": vocab[b].get("template_pos")},
                                ensure_ascii=False) + "\n")
    edges = {frozenset((a, b)): neg for (a, b, neg), ok in zip(cand, verdicts) if ok}
    n_pairs.update(candidate_pairs=sum(len(pairs_of(c)) for c in clusters), stage_a_accepted=len(cand),
                   stage_a_negation=sum(e[2] for e in cand), stage_b_accepted=len(edges),
                   stage_b_negation=sum(edges.values()))

    groups = []
    for names in clusters:
        order = sorted(names, key=lambda p: (p not in curated, -uses[p], p))
        assigned = set()
        for seed in order:
            if seed in assigned:
                continue
            sign = {seed: False}  # True = member is the negation of the seed
            for x in order:
                if x in assigned or x in sign or (x in curated and any(m in curated for m in sign)):
                    continue
                rel = [edges.get(frozenset((m, x))) for m in sign]
                if None in rel:
                    continue
                s = {sign[m] != r for m, r in zip(sign, rel)}
                if len(s) == 1:
                    sign[x] = s.pop()
            if len(sign) >= 2:
                assigned.update(sign)
                groups.append(sign)

    def choose(sign: dict) -> dict:
        cur = [p for p in sign if p in curated]
        if cur:
            canon, reason = cur[0], "curated"
        else:
            items = "\n".join(f"- {_desc(p, vocab, uses, quotes, curated)}" for p in sign)
            out = llm.chat("canon", CANON_PROMPT.format(items=items))
            canon, reason = out.get("canonical"), str(out.get("reason") or "")
            if canon not in sign:
                canon, reason = max(sign, key=lambda p: (not sign[p], uses[p], -len(p))), "fallback: most used"
        flip = sign[canon]
        return {"canonical": canon, "members": [{"pred": p, "neg": n != flip} for p, n in sign.items() if p != canon],
                "reason": reason}

    print(f"confirm C: {len(groups)} groups", flush=True)
    with ThreadPoolExecutor(workers) as pool:
        return list(pool.map(choose, groups)), n_pairs


def rewrite(rules: list[dict], mapping: dict[str, tuple[str, bool]]) -> tuple[list[dict], Counter]:
    """Canonical literals; drop rules that became trivial (conclusion among premises) or contradictory."""
    def m(lit):
        p, pos = _strip(lit)
        c, neg = mapping.get(p, (p, False))
        return _lit(c, pos != neg)

    out, dropped, seen = [], Counter(), {}
    for r in rules:
        prem = list(dict.fromkeys(m(x) for x in r["premises"]))
        concl = m(r["conclusion"])
        if concl in prem:
            dropped["trivial_conclusion_in_premises"] += 1
            continue
        if any(_lit(_strip(x)[0], not _strip(x)[1]) in prem for x in prem):
            dropped["contradictory_premises"] += 1
            continue
        key = (r["doc_id"], r["type"], frozenset(prem), concl)
        if key in seen:  # same rule twice in one document after renaming
            seen[key].setdefault("duplicate_ids", []).append(r["id"])
            dropped["duplicate_in_same_document"] += 1
            continue
        nr = dict(r, premises=prem, conclusion=concl)
        nr.pop("undeclared_predicates", None)
        renamed = sorted({_strip(x)[0] for x in r["premises"] + [r["conclusion"]] if _strip(x)[0] in mapping})
        if renamed:
            nr["renamed_predicates"] = renamed
        nr["review_status"] = "draft"
        seen[key] = nr
        out.append(nr)
    return out, dropped


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--sim", type=float, default=SIM)
    args = ap.parse_args()
    t0 = time.time()

    rules = [json.loads(line) for line in open(KB / "rules.jsonl", encoding="utf-8")]
    vocab = yaml.safe_load((KB / "vocabulary.yaml").read_text(encoding="utf-8"))["predicates"]
    curated = set(yaml.safe_load(CURATED.read_text(encoding="utf-8"))["predicates"])
    before = kb_metrics(rules, vocab)
    dedup_rules, dedup_dropped = rewrite(rules, {})  # baseline: what deduplication alone does, without merging
    dedup_only = kb_metrics(dedup_rules, vocab)
    llm = LLM()

    # 1. declare undeclared predicates
    declared = declare(llm, rules, vocab, args.workers)
    full = dict(vocab, **declared)

    # 2-3. embed and cluster all predicates used in rules (plus curated ones)
    uses, quotes, examples = Counter(), {}, defaultdict(list)
    for r in rules:
        for p in {_strip(x)[0] for x in r["premises"] + [r["conclusion"]]}:
            uses[p] += 1
            quotes.setdefault(p, r["quote"])
            if r["quote"] not in (q for q, _ in examples[p]):
                examples[p].append((r["quote"], r["source"]))
    names = sorted(p for p in full if uses[p] or p in curated)
    E = embed([full[p].get("template_pos") or p.replace("_", " ") for p in names])
    clusters = [[names[i] for i in c] for c in cluster(E, args.sim)]
    print(f"cluster: {len(clusters)} clusters covering {sum(map(len, clusters))} predicates "
          f"(sizes {Counter(min(len(c), 10) for c in clusters).most_common()})", flush=True)

    # 4. confirm merges
    groups, pair_stats = confirm(llm, clusters, full, uses, quotes, examples, curated,
                                  args.workers)
    mapping = {m["pred"]: (g["canonical"], m["neg"]) for g in groups for m in g["members"]}

    # 5. rewrite rules and build the consolidated vocabulary
    new_rules, dropped = rewrite(rules, mapping)
    concluded = {_strip(r["conclusion"])[0] for r in new_rules}
    used_after = {_strip(x)[0] for r in new_rules for x in r["premises"] + [r["conclusion"]]}
    doms = defaultdict(set)
    for r in new_rules:
        for x in r["premises"] + [r["conclusion"]]:
            doms[_strip(x)[0]].add(r["domain"])
    by_canon = defaultdict(list)
    for g in groups:
        by_canon[g["canonical"]] += g["members"]
    new_vocab, undeclared_dropped = {}, []
    for p in sorted(used_after | (curated & set(full))):
        if p not in full:
            undeclared_dropped.append(p)
            continue
        e = {k: v for k, v in full[p].items() if k != "domains"}
        e["domains"] = sorted(doms[p] | set(full[p].get("domains", [])))
        merged = by_canon.get(p, [])
        if merged:
            e["merged_from"] = [_lit(m["pred"], not m["neg"]) for m in merged]
            kinds = {full[m["pred"]].get("kind") for m in merged} | {full[p].get("kind")}
            if len(kinds - {"lookup"}) > 1:
                e["kind"] = "derived" if p in concluded else "input"
            if not e.get("ask"):
                e["ask"] = next((full[m["pred"]].get("ask") for m in merged
                                 if not m["neg"] and full[m["pred"]].get("ask")), "")
        e["review_status"] = "draft"
        new_vocab[p] = e
    if undeclared_dropped:  # predicates the LLM could not declare: drop the rules that use them
        bad = set(undeclared_dropped)
        n = len(new_rules)
        new_rules = [r for r in new_rules if not ({_strip(x)[0] for x in r["premises"] + [r["conclusion"]]} & bad)]
        dropped["uses_undeclarable_predicate"] = n - len(new_rules)

    after = kb_metrics(new_rules, new_vocab)
    with open(KB / "rules_consolidated.jsonl", "w", encoding="utf-8") as fh:
        for r in new_rules:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (KB / "vocabulary_consolidated.yaml").write_text(
        "# Consolidated predicate vocabulary (draft, LLM-merged, NOT manually reviewed). See consolidation_stats.json.\n"
        + yaml.safe_dump({"predicates": new_vocab}, allow_unicode=True, sort_keys=True, width=120), encoding="utf-8")
    with open(KB / "consolidation_merges.jsonl", "w", encoding="utf-8") as fh:
        for g in groups:
            fh.write(json.dumps({k: g[k] for k in ("canonical", "members", "reason")}, ensure_ascii=False) + "\n")
    stats = {
        "model": llm.model, "embedding_model": EMBED_MODEL, "cluster_similarity_threshold": args.sim,
        "max_cluster_size": MAX_CLUSTER,
        "before": before, "before_dedup_only": dedup_only, "after": after,
        "rules_dropped_by_dedup_only": dict(dedup_dropped),
        "undeclared_declared_by_llm": len(declared),
        "undeclared_dropped": len(undeclared_dropped),
        "candidate_clusters": len(clusters),
        "predicates_in_candidate_clusters": sum(map(len, clusters)),
        "pair_checks": dict(pair_stats),
        "merge_groups": len(groups),
        "predicates_merged_away": len(mapping),
        "negation_merges": sum(neg for _, neg in mapping.values()),
        "rules_renamed": sum("renamed_predicates" in r for r in new_rules),
        "rules_dropped": dict(dropped),
        "api_calls": llm.usage["calls"] + llm.usage["cached"],
        "tokens_in": llm.usage["in"], "tokens_out": llm.usage["out"],
        "estimated_cost_usd": round(llm.cost(), 4),
        "seconds": round(time.time() - t0),
        "review_status": "draft (LLM-merged, not manually verified)",
    }
    (KB / "consolidation_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
