"""Offline parser quality: heuristic Layer1 + Layer2 vs regression fixtures (no LLM)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from question_side.parse_regression_eval import aggregate_stats, evaluate_case  # noqa: E402
from question_side.parse_regression_fixtures import load_parse_regression_cases  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Parser regression report (heuristic-only).")
    ap.add_argument(
        "--gap-report",
        type=Path,
        default=None,
        help="Write JSON lines: per-case gap hints (lexicon / ambiguity).",
    )
    ap.add_argument(
        "--json-summary",
        type=Path,
        default=None,
        help="Write full aggregate stats as JSON.",
    )
    args = ap.parse_args()

    cases = load_parse_regression_cases()
    results = [evaluate_case(c) for c in cases]
    stats = aggregate_stats(results)

    n = stats["total"]
    print(f"total_cases={n}")
    print(f"parser_backend={stats.get('parser_backend', '')}")
    print(f"stated_condition_rate={stats.get('stated_condition_rate', 0)} count={stats.get('stated_condition_count', 0)}")
    print(f"ambiguity_cases_flagged_layer2={stats.get('ambiguity_cases_flagged_layer2', 0)}")
    acc = stats.get("field_level_accuracy") or {}
    for k in sorted(acc):
        print(f"field_accuracy.{k}={acc[k]}")
    gaps = stats.get("lexicon_gap_counts") or {}
    if gaps:
        print("lexicon_gap_counts:", gaps)

    failed = [r for r in results if r.failed_fields]
    print(f"failed_cases={len(failed)}")

    tag_counts: dict[str, int] = {}
    stated_snap = 0
    amb_cases = 0
    for r, c in zip(results, cases, strict=True):
        exp = c.get("expected") or {}
        if (exp.get("canonical_snapshot") or "") == "stated_condition" or (
            exp.get("canonical_snapshot") == "" and not (exp.get("condition_predicate_tokens") or [])
        ):
            stated_snap += 1
        ambs = (r.layer2.get("diagnostics") or {}).get("ambiguities") or []
        if ambs:
            amb_cases += 1
        for t in c.get("tags") or []:
            tag_counts[t] = tag_counts.get(t, 0) + 1
    print(f"tag_counts={dict(sorted(tag_counts.items(), key=lambda x: -x[1])[:25])}")
    print(f"cases_with_stated_or_empty_canonical_snapshot~={stated_snap}")
    print(f"cases_with_layer2_ambiguities_non_empty={amb_cases}")

    if args.json_summary:
        args.json_summary.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.json_summary}")

    if args.gap_report:
        lines = []
        for r, c in zip(results, cases, strict=True):
            exp = c.get("expected") or {}
            cn = (r.layer2.get("diagnostics") or {}).get("condition_normalization") or {}
            lines.append(
                {
                    "qid": r.qid,
                    "question_text": r.question_text,
                    "tags": c.get("tags") or [],
                    "predicted_canonical_predicate": r.canonical_predicate,
                    "predicted_atoms": (r.layer2.get("condition_atoms") or [])[:6],
                    "confidence": cn.get("confidence"),
                    "alternatives": cn.get("alternative_atoms") if isinstance(cn, dict) else [],
                    "ambiguity_reason": cn.get("ambiguity_reason"),
                    "lexicon_gap_label": r.lexicon_gap_label,
                    "failed_fields": r.failed_fields,
                    "expected_canonical_snapshot": exp.get("canonical_snapshot"),
                }
            )
        args.gap_report.write_text(
            "\n".join(json.dumps(x, ensure_ascii=False) for x in lines) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {args.gap_report}")


if __name__ == "__main__":
    main()
