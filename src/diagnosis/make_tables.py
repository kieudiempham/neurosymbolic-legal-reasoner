"""Render experiments/diag/results.json as Markdown tables for the paper."""

from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[2] / "experiments" / "diag"
NAMES = {
    "neural_llm": "Neural LLM",
    "base_nesy": "Base NeSy",
    "nesy_diag": "NeSy + Proposed Diagnosis",
    "no_mbd": "Without MBD / minimal diagnosis",
    "exhaustive_evidence": "Without diagnosis-directed evidence selection",
}
CATS = [
    "Normal",
    "MissingCaseInformation",
    "ParserOmission",
    "ParserMisinterpretation",
    "UnsupportedParserFact",
    "ResolvableRuleOverlap",
    "UnresolvedKBConflict",
]


def pct(x) -> str:
    return "-" if x is None else f"{100 * x:.1f}"


def main() -> None:
    data = json.loads((OUT_DIR / "results.json").read_text(encoding="utf-8"))
    R = data["results"]
    llm_f = OUT_DIR / "results_llm.json"
    if llm_f.exists():
        llm = json.loads(llm_f.read_text(encoding="utf-8"))
        ids = {r["iid"] for r in data["per_instance"][next(iter(data["per_instance"]))]}
        rows = [r for r in llm["rows"] if r["iid"] in ids]  # same instance subset as the other systems
        faulty = [r for r in rows if r["gold_category"] != "Normal"]
        R["neural_llm"] = dict(llm["summary"],
                               final_answer_acc=sum(r["answer_ok"] for r in rows) / len(rows),
                               final_answer_acc_faulty=sum(r["answer_ok"] for r in faulty) / max(1, len(faulty)))
        NAMES["neural_llm"] = f"Neural LLM ({R['neural_llm']['model']})"
    L = []
    ks = data["kb_stats"]
    L += ["## Table A. Diagnostic KB and benchmark", "", "| Item | Value |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in ks.items()]
    L += [f"| diagnostic instances | {data['n_instances']} |"]
    L += [f"| instances: {k} | {v} |" for k, v in sorted(data["by_origin"].items())]

    L += ["", "## Table 2. Main comparison", "",
          "| System | Diag. Acc. | Recovery | Final Acc. (all) | Final Acc. (faulty) | Measurements/query |",
          "|---|---|---|---|---|---|"]
    for key in ("neural_llm", "base_nesy", "nesy_diag"):
        if key in R:
            s = R[key]
            L.append(f"| {NAMES[key]} | {pct(s.get('diagnosis_acc'))} | {pct(s.get('recovery_success_rate'))} | "
                     f"{pct(s['final_answer_acc'])} | {pct(s['final_answer_acc_faulty'])} | "
                     f"{s.get('measurements_per_query', 0):.2f} |")

    if "nesy_diag" in R:
        s = R["nesy_diag"]
        L += ["", "## Table 3. Diagnostic performance by category (NeSy + Proposed Diagnosis)", "",
              "| Category | n | Precision | Recall | F1 | Exact diagnosis acc. |", "|---|---|---|---|---|---|"]
        for c in CATS:
            m = s["per_category"][c]
            L.append(f"| {c} | {m['support']} | {pct(m['precision'])} | {pct(m['recall'])} | {pct(m['f1'])} | "
                     f"{pct(s['per_category_acc'][c])} |")
        L += ["", "Confusion (rows = gold, columns = predicted):", "",
              "| gold \\ pred | " + " | ".join([*CATS, "Ambiguous"]) + " |", "|---|" + "---|" * (len(CATS) + 1)]
        for g in CATS:
            row = s["confusion"].get(g, {})
            L.append(f"| {g} | " + " | ".join(str(row.get(p, 0)) for p in [*CATS, "Ambiguous"]) + " |")
        if "nli" in s:
            n = s["nli"]
            L += ["", "## Table 5. NLI reliability (targeted measurements)", "",
                  f"n = {n['n']}, accuracy = {pct(n['accuracy'])}, macro-F1 = {pct(n['macro_f1'])}", "",
                  "| gold \\ pred | entail | neutral | contra |", "|---|---|---|---|"]
            for g in ("entail", "neutral", "contra"):
                row = n["confusion"].get(g, {})
                L.append(f"| {g} | {row.get('entail', 0)} | {row.get('neutral', 0)} | {row.get('contra', 0)} |")

    L += ["", "## Table 4. Ablation", "",
          "| Configuration | Diag. Acc. | Measurements/query | Recovery | Final Acc. (faulty) |", "|---|---|---|---|---|"]
    for key, label in (("nesy_diag", "Full framework"), ("no_mbd", NAMES["no_mbd"]),
                       ("exhaustive_evidence", NAMES["exhaustive_evidence"])):
        if key in R:
            s = R[key]
            L.append(f"| {label} | {pct(s.get('diagnosis_acc'))} | {s['measurements_per_query']:.2f} | "
                     f"{pct(s.get('recovery_success_rate'))} | {pct(s['final_answer_acc_faulty'])} |")
    # Per-category final-answer accuracy for every system (fair comparison: the LLM has no parser layer).
    per_inst = dict(data["per_instance"])
    if llm_f.exists():
        ids = {r["iid"] for r in data["per_instance"][next(iter(data["per_instance"]))]}
        per_inst["neural_llm"] = [r for r in json.loads(llm_f.read_text(encoding="utf-8"))["rows"] if r["iid"] in ids]
    systems = [k for k in ("neural_llm", "base_nesy", "nesy_diag") if k in per_inst]
    L += ["", "## Table 6. Final-answer accuracy by gold category", "",
          "| Category | n | " + " | ".join(NAMES[k] for k in systems) + " |", "|---|---|" + "---|" * len(systems)]
    for c in CATS:
        cells = []
        n = 0
        for k in systems:
            rs = [r for r in per_inst[k] if r["gold_category"] == c]
            n = len(rs)
            cells.append(pct(sum(r["answer_ok"] for r in rs) / n) if n else "-")
        L.append(f"| {c} | {n} | " + " | ".join(cells) + " |")
    L += ["", "Answer behaviour on Missing Case Information instances (definite answer given without the missing fact):", ""]
    for k in systems:
        rs = [r for r in per_inst[k] if r["gold_category"] == "MissingCaseInformation"]
        if k == "nesy_diag":
            definite = sum(r["answer"] in ("true", "false") and not r.get("recovery") for r in rs)
        else:
            definite = sum(r["answer"] in ("true", "false") for r in rs)
        L.append(f"- {NAMES[k]}: {definite}/{len(rs)} definite answers without asking")

    rp_f = OUT_DIR / "results_real_parser.json"
    if rp_f.exists():
        s = json.loads(rp_f.read_text(encoding="utf-8"))["summary"]
        L += ["", f"## Table 7. Real LLM parser ({s['parser_model']}) — naturally occurring parser errors", "",
              "| Item | Value |", "|---|---|",
              f"| distinct questions | {s['instances']} |",
              f"| parse fact P / R / F1 | {pct(s['parse_fact_precision'])} / {pct(s['parse_fact_recall'])} / {pct(s['parse_fact_f1'])} |",
              f"| questions parsed exactly | {pct(s['parse_exact_rate'])} |",
              f"| parse errors (omitted / wrong value / spurious) | {s['parse_error_counts'].get('omitted', 0)} / "
              f"{s['parse_error_counts'].get('wrong_value', 0)} / {s['parse_error_counts'].get('spurious', 0)} |",
              f"| Base NeSy final acc. (all) | {pct(s['base_nesy_acc'])} |",
              f"| NeSy + Diagnosis final acc. (all) | {pct(s['nesy_diag_acc'])} |",
              f"| questions with a parse error | {s['instances_with_parse_error']} |",
              f"| Base NeSy final acc. on those | {pct(s['base_nesy_acc_on_parse_errors'])} |",
              f"| NeSy + Diagnosis final acc. on those | {pct(s['nesy_diag_acc_on_parse_errors'])} |",
              f"| measurements / query | {s['measurements_per_query']:.2f} |",
              f"| diagnosed fault categories | {s['parser_faults_diagnosed']} |"]
    text = "\n".join(L) + "\n"
    (OUT_DIR / "tables.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
