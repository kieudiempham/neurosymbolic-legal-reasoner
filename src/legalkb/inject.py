"""Fault-injection benchmark of step 4 on the new pipeline (sample KB, Luật BHXH questions of the benchmark).

Base cases: the BHXH questions are parsed and reasoned; a question whose verdict matches its gold answer (true /
false) is a clean base. From each clean base:
  control      unchanged (expected action: answer)
  misinterp    a fact a proof uses gets the wrong value or the wrong polarity (expected: confirm)
  omission     a fact a proof uses is removed (expected: confirm)
  unsupported  a fact the question does not state is added (expected: confirm; "benign" when no proof uses it)
  misencoded   a rule a proof uses is perturbed in a copy of the KB: conclusion negated, or threshold halved
               (expected: warn)
  omitted      a norm a proof uses is removed from the step 2 candidates (expected: warn)
Questions whose gold answer is "insufficient" are the natural missing-information cases (expected: ask).
Each instance is stored as a run (batch inject_v1) with its MBD trace, and its measured components are kept in
experiments/legalkb/inject_results.jsonl so the acceptance threshold can be recalibrated without new calls.

    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.inject run            # resumable
    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.inject eval [--tau 0.5 --rule pos_neg]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

from .compile import ROOT, write_and_check
from .db import connect

OUT = ROOT / "experiments" / "legalkb"
BASE_FILE, RESULTS = OUT / "inject_base.json", OUT / "inject_results.jsonl"
BATCH = "inject_v1"
EXPECTED = {None: "answer", "missing": "ask", "misinterp": "confirm", "omission": "confirm",
            "unsupported": "confirm", "misencoded": "warn", "omitted": "warn"}
ADDABLE = ["dang_huong_luong_huu_hoac_tro_cap_hang_thang(toi)", "lam_viec_khong_tron_thoi_gian(toi)"]


def akey(atom: str) -> tuple:
    """Component identity independent of its form: attr(hd1, thoi_han, 12) and attr(hd1,thoi_han)>=1 match."""
    s = atom.replace(" ", "")
    m = re.match(r"attr\(([^,]+),([^,()]+)", s)
    if m:
        return ("attr", m.group(1), m.group(2))
    m = re.match(r"([a-z_0-9]+)\((.*)\)$", s)
    return (m.group(1), m.group(2)) if m else (s,)


def split_of(item_id: str) -> str:
    return "dev" if int(re.sub(r"\D", "", item_id) or 0) % 2 else "test"


def build_base(sample_db: Path, sample_pl: Path) -> list[dict]:
    from .batch import load_benchmark
    from .parse import Parser
    from .questions import answer
    from .reason import Reasoner
    from .sample_kb import PARAMETERS

    if BASE_FILE.exists():
        return json.loads(BASE_FILE.read_text(encoding="utf-8"))
    con, r = connect(sample_db), Reasoner(sample_pl)
    parser, base = Parser(con), []
    for it in load_benchmark("bhxh"):
        facts, ff, qs, _ = parser.parse(it["question"])
        q = next((x for x in qs if x.type not in ("who", "conditions", "exceptions", "definition", "validity")), None)
        if q is None:
            continue
        part = answer(q, PARAMETERS + facts, r, con, ff)
        base.append({"id": it["id"], "question": it["question"], "gold": it["expected"], "facts": facts,
                     "false_facts": ff, "q": q.__dict__, "verdict": {"yes": "true", "no": "false",
                                                                     "unknown": "insufficient"}[part["verdict"]],
                     "proof_facts": sorted({n["goal"] for a in part["answers"] + part["contrary"]
                                            if a["status"] == "certain" for n in _leaves(a["proof"])
                                            if n.get("kind") == "fact" and not n["goal"].startswith("attr(tham_so")}),
                     "proof_norms": sorted({n["norm"] for a in part["answers"] + part["contrary"]
                                            if a["status"] == "certain" for n in _leaves(a["proof"])
                                            if n.get("kind") == "rule" and n.get("norm") not in (None, "derived")})})
        print(it["id"], it["expected"], base[-1]["verdict"], flush=True)
    r.close()
    OUT.mkdir(parents=True, exist_ok=True)
    BASE_FILE.write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")
    return base


def _leaves(n):
    yield n
    for c in n.get("children", []):
        yield from _leaves(c)


def _same(a: str, b: str) -> bool:
    return a.replace(" ", "") == b.replace(" ", "")


def instances(base: list[dict]) -> list[dict]:
    out = []
    for b in base:
        common = {"base": b["id"], "split": split_of(b["id"]), "question": b["question"], "q": b["q"]}
        if b["gold"] == "insufficient":
            out.append({**common, "id": f"{b['id']}/missing", "mode": "missing", "key": None,
                        "facts": b["facts"], "false_facts": b["false_facts"]})
            continue
        if b["verdict"] != b["gold"]:
            continue
        out.append({**common, "id": f"{b['id']}/control", "mode": None, "key": None, "facts": b["facts"],
                    "false_facts": b["false_facts"]})
        used = [f for f in b["facts"] if any(_same(f, g) for g in b["proof_facts"]) and not f.startswith("instance_of")]
        for k, f in enumerate(used):
            rest = [x for x in b["facts"] if x != f]
            out.append({**common, "id": f"{b['id']}/omission{k}", "mode": "omission", "key": akey(f),
                        "facts": rest, "false_facts": b["false_facts"]})
            m = re.fullmatch(r"attr\((\s*[^,]+),(\s*[^,]+),\s*(.+)\)", f)
            if m and re.fullmatch(r"-?\d+(\.\d+)?", m.group(3).strip()):
                wrong = f"attr({m.group(1).strip()}, {m.group(2).strip()}, 0)"
                ff = b["false_facts"]
            elif m:
                wrong = f"attr({m.group(1).strip()}, {m.group(2).strip()}, xac_dinh_thoi_han)" \
                    if "khong_xac_dinh" in m.group(3) else f"attr({m.group(1).strip()}, {m.group(2).strip()}, khac)"
                ff = b["false_facts"]
            else:  # a relation / status read with the wrong polarity
                wrong, ff = None, b["false_facts"] + [f]
            out.append({**common, "id": f"{b['id']}/misinterp{k}", "mode": "misinterp", "key": akey(f),
                        "facts": rest + ([wrong] if wrong else []), "false_facts": ff})
        for k, f in enumerate(b["false_facts"]):  # a fact the question denies, read as true
            out.append({**common, "id": f"{b['id']}/misinterp_neg{k}", "mode": "misinterp", "key": akey(f),
                        "facts": b["facts"] + [f], "false_facts": [x for x in b["false_facts"] if x != f]})
        for k, f in enumerate(ADDABLE):
            if not any(akey(f) == akey(x) for x in b["facts"] + b["false_facts"]):
                out.append({**common, "id": f"{b['id']}/unsupported{k}", "mode": "unsupported", "key": akey(f),
                            "facts": b["facts"] + [f], "false_facts": b["false_facts"]})
        for k, n in enumerate(b["proof_norms"]):
            out.append({**common, "id": f"{b['id']}/omitted{k}", "mode": "omitted", "key": (n,), "drop": [n],
                        "facts": b["facts"], "false_facts": b["false_facts"]})
            for how in ("negate", "threshold"):
                out.append({**common, "id": f"{b['id']}/misencoded{k}_{how}", "mode": "misencoded", "key": (n,),
                            "variant": [n, how], "facts": b["facts"], "false_facts": b["false_facts"]})
    return out


def variant(sample_db: Path, norm: str, how: str) -> tuple[Path, Path] | None:
    """A copy of the sample KB with one rule perturbed; None when the perturbation does not apply."""
    tag = re.sub(r"\W", "_", f"{norm}_{how}")
    db = sample_db.with_name(f"variant_{tag}.sqlite")
    pl = db.with_suffix(".pl")
    if not db.exists():
        shutil.copy(sample_db, db)
        con = connect(db)
        if how == "negate":
            n = con.execute("UPDATE norms SET conclusion_negated = 1 - COALESCE(conclusion_negated, 0) "
                            "WHERE norm_id=? AND conclusion_pred IS NOT NULL", (norm,)).rowcount
        else:
            n = con.execute("UPDATE norm_conditions SET value_num = value_num / 2 WHERE norm_id=? AND "
                            "kind='compare' AND value_num IS NOT NULL", (norm,)).rowcount
        con.commit()
        if not n:
            con.close()
            db.unlink()
            return None
        write_and_check(con, pl)
        con.close()
    return db, pl


def run() -> None:
    from .extract import Extractor
    from .questions import Question, answer
    from .reason import Reasoner
    from .sample_kb import PARAMETERS, SAMPLE_DB, SAMPLE_PL, build
    from .trace import connect_runs, save_run
    from .verify import verify

    build()
    base = build_base(SAMPLE_DB, SAMPLE_PL)
    insts = instances(base)
    done = {json.loads(x)["id"] for x in RESULTS.read_text(encoding="utf-8").splitlines()} if RESULTS.exists() else set()
    print(f"{len(base)} base questions, {len(insts)} instances, {len(done)} done", flush=True)
    client, runs = Extractor("gpt-4.1-mini").client, connect_runs()
    kbs = {"": (connect(SAMPLE_DB), SAMPLE_PL)}
    reasoners = {"": Reasoner(SAMPLE_PL)}
    with RESULTS.open("a", encoding="utf-8") as out:
        for k, inst in enumerate(insts, 1):
            if inst["id"] in done:
                continue
            key = ""
            if inst.get("variant"):
                v = variant(SAMPLE_DB, *inst["variant"])
                if v is None:
                    continue
                key = str(v[1])
                if key not in kbs:
                    kbs[key] = (connect(v[0]), v[1])
                    reasoners[key] = Reasoner(v[1])
            con, pl = kbs[key]
            q = Question(**inst["q"])
            part = answer(q, PARAMETERS + inst["facts"], reasoners[key], con, inst["false_facts"],
                          drop=set(inst.get("drop", [])))
            part.update(question=inst["question"], facts=inst["facts"], false_facts=inst["false_facts"],
                        parsed=inst["q"], seconds=0)
            mbd = verify(inst["question"], inst["facts"], [part], con, client)
            run_id = save_run(runs, time="inject", question=inst["question"], kb_program=str(pl), kb_database="",
                              parser_model="(injected)", parser_output=None, facts=inst["facts"],
                              false_facts=inst["false_facts"], parameters=PARAMETERS, parse_seconds=0,
                              parts=[part], batch=BATCH, item_id=inst["id"],
                              gold=json.dumps({"mode": inst["mode"], "key": inst["key"]}), mbd=mbd)
            rec = {k2: inst[k2] for k2 in ("id", "base", "split", "mode", "key")}
            rec.update(run=run_id, verdict=part["verdict"], action=mbd["action"], diagnoses=mbd["diagnoses"],
                       components=mbd["components"], competing=mbd.get("competing", []))
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            print(f"[{k}/{len(insts)}] {inst['id']}: {mbd['action']} (want {EXPECTED[inst['mode']]}) "
                  f"{mbd['diagnoses'][:2]}", flush=True)
    for r in reasoners.values():
        r.close()


def faults_of(diagnoses: list[list[str]], comps: list[dict]) -> set[tuple]:
    """Fault atoms of the minimal diagnoses as (mode, component key)."""
    item = {c["id"]: c["item"] for c in comps}
    out = set()
    for d in diagnoses:
        for f in d:
            mode, cid = f.split("(", 1)
            for c in cid[:-1].replace(" ", "").split(","):
                it = item.get(c, c)
                out.add((mode, (it,) if mode in ("misencoded", "omitted", "kbconflict") else akey(it)))
    return out


def heuristic(comps: list[dict]) -> tuple[set[tuple], str]:
    """Baseline: every component whose accepted label disagrees with normal behaviour is blamed on its own,
    without the consistency model (the paper's rule_check counterpart)."""
    faults = set()
    for c in comps:
        lab = c.get("label")
        if lab is None:
            continue
        k = (c["item"],) if c["layer"] in ("kb", "retrieval") else akey(c["item"])
        if c["layer"] == "case":
            if c["kind"] == "checked":
                pos = c.get("polarity", "pos") == "pos"
                if lab == "neutral":
                    faults.add(("unsupported", k))
                elif (lab == "contra") == pos:
                    faults.add(("misinterp", k))
            elif c["kind"] == "required":
                faults.add(("missing" if lab == "neutral" else "omission", k))
            elif c["kind"] == "presumed" and lab == "entail":
                faults.add(("omission", k))
        elif c["layer"] == "kb" and lab != "entail":
            faults.add(("misencoded", k))
        elif c["layer"] == "retrieval" and lab != "neutral":
            faults.add(("omitted", k))
    modes = {m for m, _ in faults}
    action = ("warn" if modes & {"misencoded", "omitted"} else "confirm" if modes & {"misinterp", "omission",
              "unsupported"} else "ask" if "missing" in modes else "answer")
    return faults, action


def evaluate(tau: float | None = None, rule: str | None = None, split: str | None = None) -> dict:
    from .verify import decide

    recs = [json.loads(x) for x in RESULTS.read_text(encoding="utf-8").splitlines()]
    recs = [r for r in recs if split is None or r["split"] == split]
    rows = defaultdict(lambda: Counter())
    for r in recs:
        if tau is not None or rule is not None:
            d = decide(r["components"], [tuple(x) for x in r["competing"]], tau, rule)
            r["diagnoses"], r["action"] = d["diagnoses"], d["action"]
        gold = None if r["mode"] is None else (r["mode"], tuple(r["key"]) if r["key"] else None)
        for system, (pred, action) in (("mbd", (faults_of(r["diagnoses"], r["components"]), r["action"])),
                                       ("heuristic", heuristic(r["components"]))):
            c = rows[system]
            c["n"] += 1
            c["action_ok"] += action == EXPECTED[r["mode"]]
            if r["mode"] is None:
                c["controls"] += 1
                c["false_alarm"] += action != "answer"
                continue
            c["faulty"] += 1
            hit = any(m == gold[0] and (gold[1] is None or k == gold[1]) for m, k in pred)
            c["hit"] += hit
            c["pred"] += len(pred)
            c["tp"] += sum(1 for m, k in pred if m == gold[0] and (gold[1] is None or k == gold[1]))
            c["exact"] += hit and len(pred) == 1
            c[f"hit_{r['mode']}"] += hit
            c[f"n_{r['mode']}"] += 1
    out = {}
    for system, c in rows.items():
        p = c["tp"] / c["pred"] if c["pred"] else 0.0
        rc = c["hit"] / c["faulty"] if c["faulty"] else 0.0
        out[system] = {"instances": c["n"], "action_accuracy": round(c["action_ok"] / c["n"], 3) if c["n"] else 0,
                       "fault_precision": round(p, 3), "fault_recall": round(rc, 3),
                       "fault_f1": round(2 * p * rc / (p + rc), 3) if p + rc else 0.0,
                       "exact_isolation": round(c["exact"] / c["faulty"], 3) if c["faulty"] else 0,
                       "false_alarm_rate": round(c["false_alarm"] / c["controls"], 3) if c["controls"] else 0,
                       "recall_by_mode": {m[2:]: round(c[f"hit_{m[2:]}"] / c[m], 3) for m in c if m.startswith("n_")}}
    return out


GRID = [(t, r) for r in ("pos_neg", "pos_only") for t in (0.4, 0.5, 0.6, 0.7, 0.8, 0.9)]


def calibrate() -> dict:
    """Acceptance threshold and rule chosen on the dev split only (action accuracy, then fault F1), then reported
    on test with that choice."""
    rows = []
    for tau, rule in GRID:
        e = evaluate(tau, rule, "dev")["mbd"]
        rows.append({"tau": tau, "rule": rule, "dev_action_accuracy": e["action_accuracy"], "dev_fault_f1": e["fault_f1"],
                     "dev_false_alarm": e["false_alarm_rate"]})
        print(rows[-1], flush=True)
    best = max(rows, key=lambda r: (r["dev_action_accuracy"], r["dev_fault_f1"], -r["dev_false_alarm"]))
    test = evaluate(best["tau"], best["rule"], "test")
    out = {"grid": rows, "chosen": best, "test": test, "test_default": evaluate(None, None, "test")}
    (OUT / "inject_calibration.json").write_text(__import__("json").dumps(out, ensure_ascii=False, indent=1),
                                                 encoding="utf-8")
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "eval", "calibrate"])
    ap.add_argument("--tau", type=float)
    ap.add_argument("--rule", choices=["pos_neg", "pos_only"])
    ap.add_argument("--split", choices=["dev", "test"])
    args = ap.parse_args()
    if args.cmd == "calibrate":
        print(json.dumps(calibrate(), ensure_ascii=False, indent=1))
        return
    if args.cmd == "run":
        run()
    print(json.dumps(evaluate(args.tau, args.rule, args.split), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
