import argparse
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_cases(input_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i in range(1, 31):
        path = input_dir / f"q_{i}.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")
        rows.append(_read_json(path))
    return rows


def _last_parse_verification(entry: dict[str, Any]) -> dict[str, Any] | None:
    vt = entry.get("verification_trace")
    if not isinstance(vt, list):
        return None
    for record in reversed(vt):
        if isinstance(record, dict) and record.get("mode") == "parse_verification":
            return record
    return None


def _effective_layer1(entry: dict[str, Any], parse_record: dict[str, Any] | None) -> dict[str, Any] | None:
    layer1 = entry.get("layer1")
    if isinstance(layer1, dict):
        return layer1
    if isinstance(parse_record, dict):
        normalized = parse_record.get("normalized_inputs")
        if isinstance(normalized, dict) and isinstance(normalized.get("layer1"), dict):
            return normalized.get("layer1")
    return None


def _extract_reason_list(parse_record: dict[str, Any] | None) -> list[str]:
    if not isinstance(parse_record, dict):
        return []
    for key in ("reasons", "diagnostics"):
        values = parse_record.get(key)
        if isinstance(values, list):
            return [str(v) for v in values if str(v).strip()]
    return []


def _bool(v: Any) -> bool:
    return bool(v)


def summarize_metrics(cases: list[dict[str, Any]]) -> dict[str, int]:
    out = {
        "total_cases": len(cases),
        "action_text_empty": 0,
        "parse_reject": 0,
        "parse_repair": 0,
        "has_retrieval": 0,
        "has_answer": 0,
        "degraded_honest": 0,
        "reason_no_grounded_rule_found": 0,
    }

    for c in cases:
        parse_record = _last_parse_verification(c)
        layer1 = _effective_layer1(c, parse_record)
        if isinstance(layer1, dict) and not str(layer1.get("action_text") or "").strip():
            out["action_text_empty"] += 1

        final_decision = str((parse_record or {}).get("final_decision") or (parse_record or {}).get("decision") or "").upper()
        if final_decision == "REJECT":
            out["parse_reject"] += 1
        elif final_decision == "REPAIR":
            out["parse_repair"] += 1

        debug = c.get("debug_trace") if isinstance(c.get("debug_trace"), dict) else {}
        has_retrieval = (
            ("retrieval_result" in debug and debug.get("retrieval_result") is not None)
            or ("rule_retrieval" in debug and debug.get("rule_retrieval") is not None)
            or len(c.get("retrieved_rules") or []) > 0
        )
        if has_retrieval:
            out["has_retrieval"] += 1

        answer = c.get("answer") if isinstance(c.get("answer"), dict) else None
        if answer:
            out["has_answer"] += 1
            if answer.get("generation_mode") == "degraded_honest":
                out["degraded_honest"] += 1
            extra = answer.get("extra") if isinstance(answer.get("extra"), dict) else {}
            if extra.get("reason") == "no_grounded_rule_found":
                out["reason_no_grounded_rule_found"] += 1

    return out


def build_reject_root_cause_table(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, c in enumerate(cases, start=1):
        parse_record = _last_parse_verification(c)
        final_decision = str((parse_record or {}).get("final_decision") or (parse_record or {}).get("decision") or "").upper()
        if final_decision != "REJECT":
            continue

        layer1 = _effective_layer1(c, parse_record) or {}
        nli = (parse_record or {}).get("nli_result") if isinstance((parse_record or {}).get("nli_result"), dict) else {}
        scores = nli.get("scores") if isinstance(nli.get("scores"), dict) else {}
        reasons = _extract_reason_list(parse_record)
        debug = c.get("debug_trace") if isinstance(c.get("debug_trace"), dict) else {}

        rows.append(
            {
                "q": f"q_{idx}",
                "focus": str(layer1.get("question_focus") or ""),
                "symbolic_ok": _bool((parse_record or {}).get("symbolic_ok")),
                "nli_label": str(nli.get("label") or ""),
                "nli_contradiction": float(scores.get("contradiction", 0.0) or 0.0),
                "debug_error": str(debug.get("error") or ""),
                "root_cause": "; ".join(reasons) if reasons else "(none)",
            }
        )
    return rows


def markdown_table_delta(
    metrics_base: dict[str, int],
    metrics_r1: dict[str, int],
    metrics_r2: dict[str, int],
) -> str:
    ordered = [
        "total_cases",
        "action_text_empty",
        "parse_reject",
        "parse_repair",
        "has_retrieval",
        "has_answer",
        "degraded_honest",
        "reason_no_grounded_rule_found",
    ]
    lines = [
        "## Delta 3 cot (baseline -> rerun_1 -> rerun_2)",
        "",
        "| Chi so | Baseline | Rerun_1 | Rerun_2 |",
        "|---|---:|---:|---:|",
    ]
    for k in ordered:
        lines.append(f"| {k} | {metrics_base[k]} | {metrics_r1[k]} | {metrics_r2[k]} |")
    return "\n".join(lines)


def markdown_table_root_causes(rows: list[dict[str, Any]]) -> str:
    lines = [
        "## 12 ca REJECT moi (rerun_1) - root cause theo tung cau",
        "",
        "| Cau | Focus | symbolic_ok | nli_label | nli_contradiction | debug_error | root_cause |",
        "|---|---|---:|---|---:|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['q']} | {r['focus']} | {str(r['symbolic_ok'])} | {r['nli_label']} | {r['nli_contradiction']:.4f} | {r['debug_error']} | {r['root_cause']} |"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export rerun reject root causes and 3-column delta table")
    parser.add_argument("--baseline-dir", required=True, help="Directory containing q_1..q_30 baseline")
    parser.add_argument("--rerun1-dir", required=True, help="Directory containing q_1..q_30 rerun_1")
    parser.add_argument("--rerun2-dir", required=True, help="Directory containing q_1..q_30 rerun_2")
    parser.add_argument("--output", required=True, help="Output markdown path")
    args = parser.parse_args()

    baseline_cases = _load_cases(Path(args.baseline_dir))
    rerun1_cases = _load_cases(Path(args.rerun1_dir))
    rerun2_cases = _load_cases(Path(args.rerun2_dir))

    root_rows = build_reject_root_cause_table(rerun1_cases)
    m_base = summarize_metrics(baseline_cases)
    m_r1 = summarize_metrics(rerun1_cases)
    m_r2 = summarize_metrics(rerun2_cases)

    out = []
    out.append(markdown_table_root_causes(root_rows))
    out.append("")
    out.append(markdown_table_delta(m_base, m_r1, m_r2))
    text = "\n".join(out) + "\n"

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")

    print(f"Created: {output_path}")
    print(f"reject_rows={len(root_rows)}")
    print(f"parse_reject: baseline={m_base['parse_reject']}, rerun_1={m_r1['parse_reject']}, rerun_2={m_r2['parse_reject']}")


if __name__ == "__main__":
    main()
