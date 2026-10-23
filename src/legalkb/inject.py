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
from itertools import combinations
import hashlib
from .splits import DOMAIN_PATHS, split_of
from .policy import SYSTEMS, budget_arg
from pathlib import Path

from .compile import ROOT
from .runtime import compile_sample as write_and_check
from .db import connect

OUT = ROOT / "experiments" / "legalkb"
BASE_FILE, RESULTS = OUT / "inject_base.json", OUT / "inject_results.jsonl"
BATCH = "inject_v2"
NEW_OUT = Path(__file__).with_name("reports")
EXPECTED = {None: "answer", "missing": "ask", "misinterp": "confirm", "omission": "confirm",
            "unsupported": "confirm", "misencoded": "warn", "omitted": "warn", "double": "confirm"}
ADDABLE = ["dang_huong_luong_huu_hoac_tro_cap_hang_thang(toi)", "lam_viec_khong_tron_thoi_gian(toi)"]


def akey(atom: str) -> tuple:
    """Component identity independent of its form: attr(hd1, thoi_han, 12) and attr(hd1,thoi_han)>=1 match."""
    s = atom.replace(" ", "")
    m = re.match(r"attr\(([^,]+),([^,()]+)", s)
    if m:
        return ("attr", m.group(1), m.group(2))
    m = re.match(r"([a-z_0-9]+)\((.*)\)$", s)
    return (m.group(1), m.group(2)) if m else (s,)


def build_base(sample_db: Path, sample_pl: Path, domains=None, base_file: Path | None = None, parameters=None) -> list[dict]:
    from .batch import load_benchmark
    from .parse import Parser
    from .questions import answer
    from .reason import Reasoner
    from .sample_kb import PARAMETERS

    from .parse import PARSER_VERSION
    parameters = PARAMETERS if parameters is None else parameters
    base_file = base_file or NEW_OUT / "inject_base_v2.json"
    fingerprint = hashlib.sha256(sample_pl.read_bytes()).hexdigest()
    wanted = set(domains or DOMAIN_PATHS)
    if base_file.exists():
        saved = json.loads(base_file.read_text(encoding="utf-8"))
        rows = saved if isinstance(saved, list) else saved["records"]
        covered = set(saved.get("domains", [])) if isinstance(saved, dict) else {r.get("domain", "bhxh") for r in rows}
        if not wanted <= covered:
            raise ValueError("Base cache lacks requested domains; choose a fresh --base-file")
        if isinstance(saved, dict) and (saved.get("kb_sha256") != fingerprint or saved.get("parser_version") != PARSER_VERSION):
            raise ValueError("Base cache belongs to another KB/parser; choose a fresh --base-file")
        if isinstance(saved, list) and sample_db.name != "sample_bhxh.sqlite":
            raise ValueError("Legacy base cache is only valid for the sample BHXH experiment")
        return rows
    con, r = connect(sample_db), Reasoner(sample_pl)
    parser, base = Parser(con), []
    for it in load_benchmark():
        if domains and it["domain"] not in domains:
            continue
        facts, ff, qs, _ = parser.parse(it["question"])
        q = next((x for x in qs if x.type not in ("who", "conditions", "exceptions", "definition", "validity")), None)
        if q is None:
            continue
        part = answer(q, parameters + facts, r, con, ff)
        base.append({"id": it["id"], "domain": it["domain"], "split": it["split"], "question": it["question"], "gold": it["expected"], "facts": facts,
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
    base_file.parent.mkdir(parents=True, exist_ok=True)
    base_file.write_text(json.dumps({"kb_sha256": fingerprint, "parser_version": PARSER_VERSION, "domains": sorted(wanted),
                                     "records": base}, ensure_ascii=False, indent=1), encoding="utf-8")
    con.close()
    return base


def _leaves(n):
    yield n
    for c in n.get("children", []):
        yield from _leaves(c)


def _same(a: str, b: str) -> bool:
    return a.replace(" ", "") == b.replace(" ", "")


def instances(base: list[dict], addable: dict | None = None, double: bool = True) -> list[dict]:
    out = []
    for b in base:
        begin = len(out)
        common = {"base": b["id"], "domain": b.get("domain", "bhxh"),
                  "split": split_of(b["id"], b.get("domain"), fallback=b.get("split")), "question": b["question"], "q": b["q"]}
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
                wrong_value = 0 if float(m.group(3)) != 0 else 1
                wrong = f"attr({m.group(1).strip()}, {m.group(2).strip()}, {wrong_value})"
                ff = b["false_facts"]
            elif m:
                wrong = f"attr({m.group(1).strip()}, {m.group(2).strip()}, xac_dinh_thoi_han)" \
                    if "khong_xac_dinh" in m.group(3) else f"attr({m.group(1).strip()}, {m.group(2).strip()}, khac)"
                ff = b["false_facts"]
            else:  # a relation / status read with the wrong polarity
                wrong, ff = None, b["false_facts"] + [f]
            if wrong and _same(wrong, f):
                wrong = f"attr({m.group(1).strip()}, {m.group(2).strip()}, gia_tri_sai_mau)"
            out.append({**common, "id": f"{b['id']}/misinterp{k}", "mode": "misinterp", "key": akey(f),
                        "facts": rest + ([wrong] if wrong else []), "false_facts": ff})
        for k, f in enumerate(b["false_facts"]):  # a fact the question denies, read as true
            out.append({**common, "id": f"{b['id']}/misinterp_neg{k}", "mode": "misinterp", "key": akey(f),
                        "facts": b["facts"] + [f], "false_facts": [x for x in b["false_facts"] if x != f]})
        for k, f in enumerate((addable or {}).get(b["id"], ADDABLE if b.get("domain", "bhxh") == "bhxh" else [])):
            if not any(akey(f) == akey(x) for x in b["facts"] + b["false_facts"]):
                out.append({**common, "id": f"{b['id']}/unsupported{k}", "mode": "unsupported", "key": akey(f),
                            "facts": b["facts"] + [f], "false_facts": b["false_facts"]})
        if double:
            singles = [i for i in out[begin:] if i["mode"] in ("misinterp", "omission", "unsupported")]
            made = set()
            for left, right in combinations(singles, 2):
                if left["key"] == right["key"]:
                    continue
                modes = tuple(sorted((left["mode"], right["mode"])))
                if modes in made:
                    continue  # one reproducible case of each mode pair per base
                made.add(modes)
                removed = (set(b["facts"]) - set(left["facts"])) | (set(b["facts"]) - set(right["facts"]))
                added = (set(left["facts"]) | set(right["facts"])) - set(b["facts"])
                neg_removed = (set(b["false_facts"]) - set(left["false_facts"])) | (set(b["false_facts"]) - set(right["false_facts"]))
                neg_added = (set(left["false_facts"]) | set(right["false_facts"])) - set(b["false_facts"])
                fs = sorted((set(b["facts"]) - removed) | added)
                ff = sorted((set(b["false_facts"]) - neg_removed) | neg_added)
                if set(fs) & set(ff):
                    continue
                out.append({**common, "id": f"{b['id']}/double_{len(made)}", "mode": "double", "key": None,
                            "faults": [{"mode": i["mode"], "key": i["key"]} for i in (left, right)],
                            "facts": fs, "false_facts": ff})
        for k, n in enumerate(b["proof_norms"]):
            out.append({**common, "id": f"{b['id']}/omitted{k}", "mode": "omitted", "key": (n,), "drop": [n],
                        "facts": b["facts"], "false_facts": b["false_facts"]})
            for how in ("negate", "threshold"):
                out.append({**common, "id": f"{b['id']}/misencoded{k}_{how}", "mode": "misencoded", "key": (n,),
                            "variant": [n, how], "facts": b["facts"], "false_facts": b["false_facts"]})
    return out


def addable_facts(con, base):
    """Ground absent positive conditions from each domain's actual KB vocabulary.

    Types come from norm variables; no BHXH-only predicate list for other domains.
    """
    out = {}
    for b in base:
        entity_types = defaultdict(list)
        for f in b["facts"]:
            match = re.fullmatch(r"instance_of\(\s*([^,]+),\s*([^()]+)\)", f)
            if match:
                entity_types[match[2].strip()].append(match[1].strip())
        facts = []
        for nid, pred, args in con.execute("SELECT norm_id,pred,args FROM norm_conditions WHERE kind='atom' AND COALESCE(negated,0)=0"):
            types = dict(con.execute("SELECT var,type FROM norm_variables WHERE norm_id=?", (nid,)))
            ground = []
            for arg in (args or "").split(","):
                arg = arg.strip()
                if arg in types:
                    candidates = entity_types.get(types[arg], [])
                    if not candidates:
                        break
                    ground.append(candidates[0])
                else:
                    ground.append(arg)
            else:
                atom = f"{pred}({', '.join(ground)})"
                if not any(akey(atom) == akey(f) for f in b["facts"] + b["false_facts"]):
                    facts.append(atom)
        out[b["id"]] = sorted(set(facts))[:4]
    return out


def variant(sample_db: Path, norm: str, how: str) -> tuple[Path, Path] | None:
    """A copy of the sample KB with one rule perturbed; None when the perturbation does not apply."""
    tag = re.sub(r"\W", "_", f"{norm}_{how}")
    db = sample_db.with_name(f"variant_{tag}.sqlite")
    pl = db.with_suffix(".pl")
    fingerprint = hashlib.sha256(sample_db.read_bytes()).hexdigest()
    stamp = db.with_suffix(".sha256")
    if db.exists() and pl.exists() and stamp.exists() and stamp.read_text() == fingerprint:
        return db, pl
    shutil.copy(sample_db, db)
    con = connect(db)
    if how == "negate":
        n = con.execute("UPDATE norms SET conclusion_negated = 1 - COALESCE(conclusion_negated, 0) "
                        "WHERE norm_id=? AND conclusion_pred IS NOT NULL", (norm,)).rowcount
    else:
        n = con.execute("UPDATE norm_conditions SET value_num = value_num / 2 WHERE norm_id=? AND "
                        "kind='compare' AND value_num IS NOT NULL AND value_num != 0", (norm,)).rowcount
    con.commit()
    if not n:
        con.close()
        db.unlink()
        return None
    write_and_check(con, pl)
    con.close()
    stamp.write_text(fingerprint)
    return db, pl


def run(domains=None, results: Path | None = None, base_file: Path | None = None,
        system="mbd", budget=None, kb_db: Path | None = None, kb_pl: Path | None = None, split=None) -> None:
    from .offline import extractor
    from .questions import Question, answer
    from .reason import Reasoner
    from .sample_kb import PARAMETERS, SAMPLE_DB, SAMPLE_PL, build
    from .trace import connect_runs, save_run
    from .verify import verify

    from .policy import policy
    if bool(kb_db) != bool(kb_pl):
        raise ValueError("--kb-db and --kb-pl must be supplied together")
    if kb_db is None:
        build()
    sample_db, sample_pl = kb_db or SAMPLE_DB, kb_pl or SAMPLE_PL
    parameters = [] if kb_db else PARAMETERS
    results = results or RESULTS
    results.parent.mkdir(parents=True, exist_ok=True)
    base = build_base(sample_db, sample_pl, domains, base_file, parameters)
    base = [b for b in base if not domains or b.get("domain", "bhxh") in domains]
    con_add = connect(sample_db)
    insts = [i for i in instances(base, addable=addable_facts(con_add, base))
             if split is None or i["split"] == split]
    con_add.close()
    done = {json.loads(x)["id"] for x in results.read_text(encoding="utf-8").splitlines()} if results.exists() else set()
    print(f"{len(base)} base questions, {len(insts)} instances, {len(done)} done", flush=True)
    client, runs = extractor("gpt-4.1-mini").client, connect_runs()
    kbs = {"": (connect(sample_db), sample_pl)}
    reasoners = {"": Reasoner(sample_pl)}
    with results.open("a", encoding="utf-8") as out:
        for k, inst in enumerate(insts, 1):
            if inst["id"] in done:
                continue
            key = ""
            if inst.get("variant"):
                v = variant(sample_db, *inst["variant"])
                if v is None:
                    continue
                key = str(v[1])
                if key not in kbs:
                    kbs[key] = (connect(v[0]), v[1])
                    reasoners[key] = Reasoner(v[1])
            con, pl = kbs[key]
            q = Question(**inst["q"])
            part = answer(q, parameters + inst["facts"], reasoners[key], con, inst["false_facts"],
                          drop=set(inst.get("drop", [])))
            part.update(question=inst["question"], facts=inst["facts"], false_facts=inst["false_facts"],
                        parsed=inst["q"], seconds=0)
            with policy(system, budget):
                mbd = verify(inst["question"], inst["facts"], [part], con, client)
            run_id = save_run(runs, time="inject", question=inst["question"], kb_program=str(pl), kb_database="",
                              parser_model="(injected)", parser_output=None, facts=inst["facts"],
                              false_facts=inst["false_facts"], parameters=parameters, parse_seconds=0,
                              parts=[part], batch=BATCH, item_id=inst["id"],
                              gold=json.dumps({"mode": inst["mode"], "key": inst["key"]}), mbd=mbd)
            rec = {k2: inst[k2] for k2 in ("id", "base", "split", "mode", "key")}
            rec.update(faults=inst.get("faults"), domain=inst.get("domain"), system=system,
                       supports=mbd.get("supports", []), run=run_id, verdict=part["verdict"], action=mbd["action"], diagnoses=mbd["diagnoses"],
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


def gold_faults(rec):
    if rec.get("faults"):
        return [(f["mode"], tuple(f["key"]) if f["key"] else None) for f in rec["faults"]]
    return [] if rec["mode"] is None else [(rec["mode"], tuple(rec["key"]) if rec["key"] else None)]


def score_predictions(rows):
    """Micro fault scores, one-to-one matching; controls contribute false positives.

    Historical scoring excluded control predictions from precision and could count
    several predictions against one wildcard gold fault. This scorer does neither.
    """
    counts, mode_n, mode_hits = Counter(), Counter(), Counter()
    for rec, pred, action in rows:
        gold = gold_faults(rec)
        remaining = set(pred)
        matched = 0
        for mode, key in gold:
            mode_n[mode] += 1
            hit = next(((m, k) for m, k in sorted(remaining) if m == mode and (key is None or k == key)), None)
            if hit:
                remaining.remove(hit)
                matched += 1
                mode_hits[mode] += 1
        counts["n"] += 1
        counts["tp"] += matched
        counts["pred"] += len(pred)
        counts["gold"] += len(gold)
        counts["action_ok"] += action == EXPECTED[rec["mode"]]
        counts["exact"] += matched == len(gold) and len(pred) == len(gold)
        if not gold:
            counts["controls"] += 1
            counts["false_alarm"] += action != "answer"
            counts["lack_of_confidence"] += action in ("confirm", "warn")
        if rec["mode"] == "double":
            counts["double_n"] += 1
            counts["double_exact"] += matched == len(gold) and len(pred) == len(gold)
    precision = counts["tp"] / counts["pred"] if counts["pred"] else 0
    recall = counts["tp"] / counts["gold"] if counts["gold"] else 0
    return {"instances": counts["n"], "action_accuracy": round(counts["action_ok"] / max(counts["n"], 1), 3),
            "fault_precision": round(precision, 3), "fault_recall": round(recall, 3),
            "fault_f1": round(2 * precision * recall / (precision + recall), 3) if precision + recall else 0,
            "exact_isolation": round(counts["exact"] / max(counts["n"], 1), 3),
            "false_alarm_rate": round(counts["false_alarm"] / max(counts["controls"], 1), 3),
            "lack_of_confidence": counts["lack_of_confidence"],
            "double_instances": counts["double_n"],
            "double_exact": round(counts["double_exact"] / max(counts["double_n"], 1), 3),
            "recall_by_mode": {m: round(mode_hits[m] / n, 3) for m, n in sorted(mode_n.items())}}


def read_records(path=None, split=None, domains=None):
    rows = [json.loads(x) for x in (path or RESULTS).read_text(encoding="utf-8").splitlines() if x.strip()]
    seen, out = set(), []
    for r in rows:
        if r["id"] in seen:
            raise ValueError(f"Duplicate injection record: {r['id']}")
        seen.add(r["id"])
        r["split"] = split_of(r["base"], r.get("domain"), fallback=r.get("split"))
        if (split is None or r["split"] == split) and (not domains or r.get("domain", "bhxh") in domains):
            out.append(r)
    return out


def evaluate(tau=None, rule=None, split=None, *, records=None, path=None,
             systems=SYSTEMS, budget=None, domains=None):
    from copy import deepcopy
    from .verify import decide
    recs = read_records(path, split, domains) if records is None else [r for r in records if split is None or r["split"] == split]
    out = {}
    for system in systems:
        scored = []
        for rec in recs:
            result = decide(deepcopy(rec["components"]), rec.get("competing", []), tau, rule,
                            supports=rec.get("supports", []), system=system, budget=budget)
            # A single chosen diagnosis is a prediction. Union of mutually exclusive
            # diagnoses is not an isolated fault set.
            pred = faults_of(result["diagnoses"][:1], result["components"])
            scored.append((rec, pred, result["action"]))
        out[system] = score_predictions(scored)
    return out


def analyze_errors(records, tau, rule, split="dev"):
    """Explain isolation misses from stored measurements; never uses labels for inference."""
    from copy import deepcopy
    from .verify import decide
    counts, examples = defaultdict(Counter), defaultdict(list)
    for rec in records:
        if rec["split"] != split:
            continue
        result = decide(deepcopy(rec["components"]), rec.get("competing", []), tau, rule,
                        supports=rec.get("supports", []))
        predicted = faults_of(result["diagnoses"][:1], result["components"])
        for mode, key in gold_faults(rec):
            counts[mode]["total"] += 1
            if any(m == mode and (key is None or k == key) for m, k in predicted):
                counts[mode]["hit"] += 1
                continue
            target = [r for r in result["components"] if key is not None and
                      ((r["item"],) if r["layer"] in ("kb", "retrieval") else akey(r["item"])) == key]
            reason = ("no_localized_gold_key" if key is None else "target_not_observed" if not target else
                      "unaccepted_label" if all(r.get("label") is None for r in target) else "different_diagnosis")
            counts[mode][reason] += 1
            if len(examples[mode]) < 5:
                examples[mode].append({"id":rec["id"], "reason":reason, "diagnosis":result["diagnoses"][:1]})
        if rec["mode"] is None and result["action"] != "answer":
            examples["control_alarms"].append({"id":rec["id"], "diagnosis":result["diagnoses"][:1],
                                              "symptoms":[r for r in result["components"] if r.get("symptom")]})
    return {"split":split, "counts":dict(counts), "examples":dict(examples)}


GRID = [(t, r) for r in ("pos_neg", "pos_only") for t in (0.4, 0.5, 0.6, 0.7, 0.8, 0.9)]


def calibrate(records=None, path=None) -> dict:
    """Choose only on dev. This function never evaluates test, even for tie-breaking."""
    dev = read_records(path, "dev") if records is None else [r for r in records if r["split"] == "dev"]
    if not dev:
        raise ValueError("Calibration requires a nonempty dev split")
    rows = []
    for tau, rule in GRID:
        e = evaluate(tau, rule, records=dev, systems=("mbd",))["mbd"]
        rows.append({"tau": tau, "rule": rule, "dev_action_accuracy": e["action_accuracy"],
                     "dev_fault_f1": e["fault_f1"], "dev_false_alarm": e["false_alarm_rate"]})
    best = max(rows, key=lambda r: (r["dev_action_accuracy"], r["dev_fault_f1"], -r["dev_false_alarm"]))
    return {"grid": rows, "chosen": best, "selection_split": "dev"}


def comparison(path=None, records=None):
    """Freeze dev choice before reporting held-out test and all budget settings."""
    records = read_records(path) if records is None else records
    calibrated = calibrate(records)
    choice = calibrated["chosen"]
    return {"calibration": calibrated,
            "scores": {sp: {str(b) if b is not None else "unlimited":
                evaluate(choice["tau"], choice["rule"], sp, records=records, budget=b)
                for b in (0, 1, 2, None)} for sp in ("dev", "test")},
            "budget_protocol": "First action before user replies; B>0 permits one question. "
                               "Use policy.evaluate_dialogue with supplied replies for multi-turn outcomes."}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "eval", "calibrate", "compare"])
    ap.add_argument("--offline", action="store_true", help="read caches only; fail on a missing measurement")
    ap.add_argument("--tau", type=float)
    ap.add_argument("--rule", choices=["pos_neg", "pos_only"])
    ap.add_argument("--split", choices=["dev", "test"])
    ap.add_argument("--domain", choices=list(DOMAIN_PATHS), action="append")
    ap.add_argument("--system", choices=SYSTEMS, action="append")
    ap.add_argument("--budget", type=budget_arg, default=None)
    ap.add_argument("--results", type=Path)
    ap.add_argument("--base-file", type=Path)
    ap.add_argument("--kb-db", type=Path)
    ap.add_argument("--kb-pl", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    if args.offline:
        __import__("os").environ["LEGALKB_OFFLINE"] = "1"
    args.results = args.results or (NEW_OUT / "inject_results_v2.jsonl" if args.cmd == "run" else RESULTS)
    if args.cmd == "run":
        if len(args.system or []) > 1:
            ap.error("run accepts one system per output; eval/compare replays all systems")
        run(args.domain, args.results, args.base_file, (args.system or ["mbd"])[0], args.budget,
            args.kb_db, args.kb_pl, args.split)
    records = read_records(args.results, domains=args.domain)
    if args.cmd == "calibrate":
        result = calibrate(records)
    elif args.cmd == "compare":
        result = comparison(records=records)
    else:
        result = evaluate(args.tau, args.rule, args.split, records=records,
                          systems=args.system or SYSTEMS, budget=args.budget)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
