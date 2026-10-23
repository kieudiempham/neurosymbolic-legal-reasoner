"""Run the benchmark questions (300: bhxh 90, doanh_nghiep 70, thue 70, lien_nganh 40, lao_dong 30) through the
new pipeline. Every question is stored as a run in data/legalkb/runs.sqlite with the batch name, the item id and
its gold answer, so a batch can be resumed, summarised and every answer read again (python -m legalkb.trace <run>).

    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.batch --name kb_mini_v1                  # all 300, main KB
    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.batch --name smoke --sample --limit 5
    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.batch --name kb_mini_v1 --domain bhxh --split test
    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.batch --name kb_mini_v1 --summary          # no new runs

A batch is resumed by running the same command again: items that already have a run without error are skipped
(--retry-errors also re-runs the failed ones). Verdicts are compared with the gold answers: yes ~ true,
no ~ false, unknown ~ insufficient; the verdict of an item is that of its first case sub-question.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter, defaultdict

from diagnosis.dataset import load_items
from diagnosis.external_diag import DOMAINS

from .compile import ROOT
from .trace import connect_runs

GOLD = {"yes": "true", "no": "false", "unknown": "insufficient"}


def load_benchmark(domain: str | None = None, split: str | None = None) -> list[dict]:
    items = []
    for dom, (_, paths) in DOMAINS.items():
        if domain and dom != domain:
            continue
        for p in paths:
            sp = "test" if p.endswith("_test.jsonl") else "dev"
            if split and sp != split:
                continue
            items += [{**it, "split": sp} for it in load_items([str(ROOT / "data" / "dataset" / p)])]
    return items


def item_verdict(runs, run: int) -> str | None:
    row = runs.execute("SELECT verdict FROM run_questions WHERE run_id=? AND kind='case' ORDER BY q_no LIMIT 1",
                       (run,)).fetchone()
    return GOLD.get(row[0]) if row else None


def summary(runs, batch: str) -> str:
    rows = runs.execute(
        "SELECT r.run_id, r.item_id, r.gold, r.error FROM runs r JOIN (SELECT item_id, MAX(run_id) AS last FROM runs "
        "WHERE batch=? GROUP BY item_id) l ON l.last = r.run_id ORDER BY r.item_id", (batch,)).fetchall()
    if not rows:
        return f"batch {batch}: no runs"
    by_dom, by_gold, conf = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0]), Counter()
    errors = 0
    for run, item, gold, error in rows:
        if error:
            errors += 1
            continue
        pred = item_verdict(runs, run) or "no_case_question"
        ok = pred == gold
        dom = item.split("-")[0]
        for d, k in ((by_dom, dom), (by_gold, gold)):
            d[k][0] += ok
            d[k][1] += 1
        conf[(gold, pred)] += 1
    done = len(rows) - errors
    correct = sum(v[0] for v in by_dom.values())
    out = [f"batch {batch}: {len(rows)} items, {errors} errors, accuracy {correct}/{done}"
           + (f" = {100 * correct / done:.1f}%" if done else "")]
    out += [f"  {k:12s} {v[0]:3d}/{v[1]:3d}  {100 * v[0] / v[1]:5.1f}%" for k, v in sorted(by_dom.items())]
    out.append("  theo đáp án đúng:")
    out += [f"  {k:12s} {v[0]:3d}/{v[1]:3d}  {100 * v[0] / v[1]:5.1f}%" for k, v in sorted(by_gold.items())]
    out.append("  đáp án đúng -> hệ thống trả lời: " + ", ".join(f"{g}->{p}: {n}" for (g, p), n in sorted(conf.items())))
    return "\n".join(out)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="batch name (runs of the batch are grouped by it)")
    ap.add_argument("--sample", action="store_true", help="hand-encoded sample KB instead of the main KB")
    ap.add_argument("--domain", choices=list(DOMAINS))
    ap.add_argument("--split", choices=["dev", "test"])
    ap.add_argument("--limit", type=int)
    ap.add_argument("--retry-errors", action="store_true")
    ap.add_argument("--summary", action="store_true", help="only print the summary of the batch")
    args = ap.parse_args()
    runs = connect_runs()
    if not args.summary:
        from .ask import Asker

        items = load_benchmark(args.domain, args.split)[: args.limit]
        done = {i for (i,) in runs.execute(
            "SELECT item_id FROM runs WHERE batch=?" + ("" if not args.retry_errors else " AND error IS NULL"),
            (args.name,))}
        todo = [it for it in items if it["id"] not in done]
        print(f"batch {args.name}: {len(items)} items, {len(items) - len(todo)} already done, {len(todo)} to run")
        asker = Asker(args.sample)
        t0 = time.perf_counter()
        for k, it in enumerate(todo, 1):
            run, _ = asker.ask(it["question"], batch=args.name, item_id=it["id"], gold=it["expected"])
            err = runs.execute("SELECT error FROM runs WHERE run_id=?", (run,)).fetchone()[0]
            pred = None if err else item_verdict(runs, run)
            mark = "LỖI" if err else ("đúng" if pred == it["expected"] else "sai")
            print(f"[{k}/{len(todo)}] {it['id']}: {pred or '-'} (đúng: {it['expected']}) {mark}  run {run}  "
                  f"{time.perf_counter() - t0:.0f}s" + (f"  {err[:120]}" if err else ""), flush=True)
    print(summary(runs, args.name))


if __name__ == "__main__":
    main()
