import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def is_non_empty_str(value):
    return isinstance(value, str) and value.strip() != ""


def is_layer1_usable(layer):
    if not isinstance(layer, dict):
        return False
    keys = [
        "utterance_type",
        "subject_text",
        "condition_text",
        "action_text",
        "question_focus",
    ]
    for key in keys:
        if is_non_empty_str(layer.get(key)):
            return True
    return False


def is_layer2_usable(layer):
    if not isinstance(layer, dict):
        return False
    goal = layer.get("goal")
    if isinstance(goal, dict):
        if is_non_empty_str(goal.get("predicate")):
            return True
        if isinstance(goal.get("args"), list) and len(goal.get("args")) > 0:
            return True
    if is_non_empty_str(layer.get("query_rule_candidate")):
        return True
    return False


def tail_of(value):
    if isinstance(value, list):
        return value[-1] if value else None
    if isinstance(value, dict):
        return value
    return None


def extract_from_verification_trace(vt):
    layer1 = None
    layer2 = None
    parse_final = None
    material_gain = None
    if not isinstance(vt, list):
        return layer1, layer2, parse_final, material_gain

    for entry in reversed(vt):
        if not isinstance(entry, dict):
            continue
        if parse_final is None:
            parse_final = entry.get("final_decision") or entry.get("decision")
        ni = entry.get("normalized_inputs")
        if isinstance(ni, dict):
            if layer1 is None and isinstance(ni.get("layer1"), dict):
                layer1 = ni.get("layer1")
            if layer2 is None and isinstance(ni.get("layer2"), dict):
                layer2 = ni.get("layer2")

        rd = entry.get("repair_diagnostics")
        if isinstance(rd, dict):
            before_after = rd.get("before_after")
            if isinstance(before_after, dict):
                parse_after = before_after.get("parse_after")
                if isinstance(parse_after, dict):
                    if layer1 is None and isinstance(parse_after.get("layer1"), dict):
                        layer1 = parse_after.get("layer1")
                    if layer2 is None and isinstance(parse_after.get("layer2"), dict):
                        layer2 = parse_after.get("layer2")
            post_gain = rd.get("post_repair_gain")
            if material_gain is None and isinstance(post_gain, dict):
                mg = post_gain.get("material_gain")
                if isinstance(mg, bool):
                    material_gain = mg

    return layer1, layer2, parse_final, material_gain


def normalize_bool(v):
    if isinstance(v, bool):
        return v
    return None


def summarize_case(case_id, data):
    debug = data.get("debug_trace") if isinstance(data.get("debug_trace"), dict) else {}
    vt = data.get("verification_trace") if isinstance(data.get("verification_trace"), list) else []

    top_layer1 = data.get("layer1") if isinstance(data.get("layer1"), dict) else None
    top_layer2 = data.get("layer2") if isinstance(data.get("layer2"), dict) else None
    vt_layer1, vt_layer2, vt_parse_final, vt_material_gain = extract_from_verification_trace(vt)

    # Prefer runtime trace when top-level layers are missing.
    eff_layer1 = top_layer1 if top_layer1 is not None else vt_layer1
    eff_layer2 = top_layer2 if top_layer2 is not None else vt_layer2

    question_focus = eff_layer1.get("question_focus") if isinstance(eff_layer1, dict) else None
    goal = eff_layer2.get("goal") if isinstance(eff_layer2, dict) else None
    goal_predicate = goal.get("predicate") if isinstance(goal, dict) else None
    action_text = eff_layer1.get("action_text") if isinstance(eff_layer1, dict) else None
    action_text_empty = not is_non_empty_str(action_text)

    parse_repair_tail = tail_of(debug.get("parse_repair"))
    parse_repair_final = None
    material_gain = vt_material_gain
    if isinstance(parse_repair_tail, dict):
        parse_repair_final = parse_repair_tail.get("final_decision") or parse_repair_tail.get("decision")
        mg = normalize_bool(parse_repair_tail.get("material_gain"))
        if mg is None:
            post_gain = parse_repair_tail.get("post_repair_gain")
            if isinstance(post_gain, dict):
                mg = normalize_bool(post_gain.get("material_gain"))
        if mg is not None:
            material_gain = mg

    answer = data.get("answer") if isinstance(data.get("answer"), dict) else None
    answer_generation_mode = answer.get("generation_mode") if isinstance(answer, dict) else None
    answer_extra = answer.get("extra") if isinstance(answer, dict) and isinstance(answer.get("extra"), dict) else {}
    degraded = answer_generation_mode == "degraded_honest" or bool(answer_extra.get("degraded"))
    reason = answer_extra.get("reason")

    backend_modes = debug.get("backend_modes") if isinstance(debug.get("backend_modes"), dict) else {}
    parse_backend_mode = None
    if isinstance(backend_modes.get("parse_backend"), dict):
        parse_backend_mode = backend_modes["parse_backend"].get("mode")

    has_retrieval = (
        ("retrieval_result" in debug and debug.get("retrieval_result") is not None)
        or ("rule_retrieval" in debug and debug.get("rule_retrieval") is not None)
        or len(data.get("retrieved_rules") or []) > 0
    )

    selected_rule = data.get("selected_rule")
    has_selected_rule = selected_rule is not None and selected_rule != {}
    proof = data.get("proof")
    has_proof = proof is not None and proof != {}
    has_answer = answer is not None

    return {
        "q": case_id,
        "query_text": data.get("query_text"),
        "layer1_top": top_layer1 is not None,
        "layer2_top": top_layer2 is not None,
        "layer1_usable": is_layer1_usable(eff_layer1),
        "layer2_usable": is_layer2_usable(eff_layer2),
        "top_level_layer_missing": (data.get("layer1") is None and data.get("layer2") is None),
        "question_focus": question_focus,
        "goal_predicate": goal_predicate,
        "action_text_empty": action_text_empty,
        "debug_error": debug.get("error"),
        "parse_final_decision": vt_parse_final,
        "parse_repair_final_decision": parse_repair_final,
        "material_gain": material_gain,
        "has_retrieval": has_retrieval,
        "has_selected_rule": has_selected_rule,
        "has_proof": has_proof,
        "has_answer": has_answer,
        "answer_generation_mode": answer_generation_mode,
        "degraded": degraded,
        "reason": reason,
        "parse_backend_mode": parse_backend_mode,
        "contains_stated_condition": "stated_condition(" in json.dumps(data, ensure_ascii=False),
    }


def join_q_ids(items):
    if not items:
        return "-"
    return ", ".join(items)


def build_markdown(rows, summary_rows, diag_rows):
    lines = []
    lines.append("## Phan A - Bang tong hop so lieu chung")
    lines.append("")
    lines.append("| Chi so | Gia tri |")
    lines.append("|---|---:|")
    for name, value in summary_rows:
        lines.append(f"| {name} | {value} |")

    lines.append("")
    lines.append("## Phan B - Bang phan bo loi/chan doan chinh")
    lines.append("")
    lines.append("| Nhom loi chinh | So cau | Cau minh hoa |")
    lines.append("|---|---:|---|")
    for name, count, examples in diag_rows:
        lines.append(f"| {name} | {count} | {examples} |")

    lines.append("")
    lines.append("## Phu luc - Chi tiet 30 cau")
    lines.append("")
    lines.append(
        "| Cau | layer1 | layer2 | question_focus | goal.predicate | action_text_rong | debug_error | parse_final | parse_repair_final | material_gain | retrieval | selected_rule | proof | answer | generation_mode | degraded | reason |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for row in rows:
        lines.append(
            "| {q} | {l1} | {l2} | {focus} | {pred} | {act_empty} | {dbg} | {pf} | {prf} | {mg} | {ret} | {sr} | {pf2} | {ans} | {gm} | {deg} | {reason} |".format(
                q=row["q"],
                l1="yes" if row["layer1_usable"] else "no",
                l2="yes" if row["layer2_usable"] else "no",
                focus=row["question_focus"] or "",
                pred=row["goal_predicate"] or "",
                act_empty="yes" if row["action_text_empty"] else "no",
                dbg=row["debug_error"] or "",
                pf=row["parse_final_decision"] or "",
                prf=row["parse_repair_final_decision"] or "",
                mg=row["material_gain"] if row["material_gain"] is not None else "",
                ret="yes" if row["has_retrieval"] else "no",
                sr="yes" if row["has_selected_rule"] else "no",
                pf2="yes" if row["has_proof"] else "no",
                ans="yes" if row["has_answer"] else "no",
                gm=row["answer_generation_mode"] or "",
                deg="yes" if row["degraded"] else "no",
                reason=row["reason"] or "",
            )
        )
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Summarize q_1..q_30 runtime JSON into report tables.")
    parser.add_argument("--input-dir", required=True, help="Directory containing q_1.json .. q_30.json")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to write outputs (default: input dir)",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir) if args.output_dir else input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for i in range(1, 31):
        file_path = input_dir / f"q_{i}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Missing required file: {file_path}")
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        rows.append(summarize_case(f"q_{i}", data))

    count = Counter()
    examples = {
        "action_text_rong": [],
        "parse_rejected": [],
        "drift_sang_obligation": [],
        "condition_fallback_stated_condition": [],
        "retrieval_khong_grounded": [],
        "answer_degraded": [],
    }

    for row in rows:
        if row["parse_backend_mode"] == "llm_real":
            count["parser_llm_real"] += 1
        if row["layer1_usable"]:
            count["layer1_usable"] += 1
        if row["layer2_usable"]:
            count["layer2_usable"] += 1
        if row["top_level_layer_missing"]:
            count["missing_top_layers"] += 1
        if row["action_text_empty"]:
            count["action_text_empty"] += 1
            examples["action_text_rong"].append(row["q"])

        pf = (row["parse_final_decision"] or "").upper()
        if pf == "REJECT":
            count["parse_reject"] += 1
            examples["parse_rejected"].append(row["q"])
        elif pf == "REPAIR":
            count["parse_repair"] += 1
        elif pf == "ACCEPT":
            count["parse_accept"] += 1

        if row["parse_repair_final_decision"]:
            prf_key = f"parse_repair_final_{str(row['parse_repair_final_decision']).upper()}"
            count[prf_key] += 1

        if row["material_gain"] is True:
            count["material_gain_true"] += 1
        if row["has_retrieval"]:
            count["has_retrieval"] += 1
        if row["has_selected_rule"]:
            count["has_selected_rule"] += 1
        if row["has_proof"]:
            count["has_proof"] += 1
        if row["has_answer"]:
            count["has_answer"] += 1
        if row["answer_generation_mode"] == "degraded_honest":
            count["gen_degraded_honest"] += 1
        if row["degraded"]:
            examples["answer_degraded"].append(row["q"])
        if row["reason"] == "no_grounded_rule_found":
            count["reason_no_grounded_rule_found"] += 1
            examples["retrieval_khong_grounded"].append(row["q"])

        qtext = (row["query_text"] or "").lower()
        if row["question_focus"] == "obligation" and ("hay khong" in qtext or "hay không" in qtext):
            examples["drift_sang_obligation"].append(row["q"])
        if row["contains_stated_condition"]:
            examples["condition_fallback_stated_condition"].append(row["q"])

    summary_rows = [
        ("Tong so cau", len(rows)),
        ("Cau co parser backend llm_real", count["parser_llm_real"]),
        ("Cau co layer1 usable", count["layer1_usable"]),
        ("Cau co layer2 usable", count["layer2_usable"]),
        ("Cau mat top-level layer1/layer2", count["missing_top_layers"]),
        ("Cau co action_text rong", count["action_text_empty"]),
        ("Cau parse final = REJECT", count["parse_reject"]),
        ("Cau parse final = REPAIR", count["parse_repair"]),
        ("Cau parse final = ACCEPT", count["parse_accept"]),
        ("Cau material_gain = true", count["material_gain_true"]),
        ("Cau di toi retrieval", count["has_retrieval"]),
        ("Cau co selected_rule", count["has_selected_rule"]),
        ("Cau co proof", count["has_proof"]),
        ("Cau co answer", count["has_answer"]),
        ("Cau generation_mode = degraded_honest", count["gen_degraded_honest"]),
        ("Cau reason = no_grounded_rule_found", count["reason_no_grounded_rule_found"]),
    ]

    diag_rows = [
        (
            "action_text rong",
            len(examples["action_text_rong"]),
            join_q_ids(examples["action_text_rong"]),
        ),
        (
            "parse_rejected",
            len(examples["parse_rejected"]),
            join_q_ids(examples["parse_rejected"]),
        ),
        (
            "drift sang obligation",
            len(examples["drift_sang_obligation"]),
            join_q_ids(examples["drift_sang_obligation"]),
        ),
        (
            "condition fallback stated_condition(...)",
            len(examples["condition_fallback_stated_condition"]),
            join_q_ids(examples["condition_fallback_stated_condition"]),
        ),
        (
            "retrieval khong grounded",
            len(examples["retrieval_khong_grounded"]),
            join_q_ids(examples["retrieval_khong_grounded"]),
        ),
        (
            "answer degraded",
            len(examples["answer_degraded"]),
            join_q_ids(examples["answer_degraded"]),
        ),
    ]

    markdown_text = build_markdown(rows, summary_rows, diag_rows)
    md_path = output_dir / "bang_tong_hop_30_cau.md"
    md_path.write_text(markdown_text, encoding="utf-8")

    csv_path = output_dir / "bang_tong_hop_30_cau.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Phan A - Tong hop so lieu chung"])
        writer.writerow(["Chi so", "Gia tri"])
        for item in summary_rows:
            writer.writerow(item)
        writer.writerow([])
        writer.writerow(["Phan B - Phan bo loi/chan doan chinh"])
        writer.writerow(["Nhom loi chinh", "So cau", "Cau minh hoa"])
        for item in diag_rows:
            writer.writerow(item)
        writer.writerow([])
        writer.writerow(["Phu luc - Chi tiet 30 cau"])
        writer.writerow(
            [
                "q",
                "query_text",
                "layer1_usable",
                "layer2_usable",
                "top_level_layer_missing",
                "question_focus",
                "goal_predicate",
                "action_text_empty",
                "debug_error",
                "parse_final_decision",
                "parse_repair_final_decision",
                "material_gain",
                "has_retrieval",
                "has_selected_rule",
                "has_proof",
                "has_answer",
                "answer_generation_mode",
                "degraded",
                "reason",
                "parse_backend_mode",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row["q"],
                    row["query_text"],
                    row["layer1_usable"],
                    row["layer2_usable"],
                    row["top_level_layer_missing"],
                    row["question_focus"],
                    row["goal_predicate"],
                    row["action_text_empty"],
                    row["debug_error"],
                    row["parse_final_decision"],
                    row["parse_repair_final_decision"],
                    row["material_gain"],
                    row["has_retrieval"],
                    row["has_selected_rule"],
                    row["has_proof"],
                    row["has_answer"],
                    row["answer_generation_mode"],
                    row["degraded"],
                    row["reason"],
                    row["parse_backend_mode"],
                ]
            )

    print(f"Created: {md_path}")
    print(f"Created: {csv_path}")
    print("Top 5 metrics:")
    for key in [
        "parser_llm_real",
        "parse_reject",
        "parse_repair",
        "has_answer",
        "reason_no_grounded_rule_found",
    ]:
        print(f"- {key}: {count[key]}")


if __name__ == "__main__":
    main()
