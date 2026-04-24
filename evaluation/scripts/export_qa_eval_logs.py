"""Export stable QA evaluation logs to JSONL/CSV from batch response artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evaluation.qa_log_exporter import (
    export_quality_degrade_summary_csv,
    export_logs_csv,
    export_logs_jsonl,
    load_jsonl_records,
    summarize_quality_degrade_metrics,
    summarize_cross_domain_metrics,
)


def parse_args() -> argparse.Namespace:
    root = ROOT
    parser = argparse.ArgumentParser(description="Export QA evaluation logs (stable contract) to JSONL/CSV.")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input JSONL where each line is either an API response object or evaluation_log object.",
    )
    parser.add_argument(
        "--out-jsonl",
        type=Path,
        default=root / "data" / "processed" / "evaluation" / "qa_eval_logs.jsonl",
        help="Output JSONL path for normalized evaluation logs.",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=root / "data" / "processed" / "evaluation" / "qa_eval_logs.csv",
        help="Output CSV path for normalized evaluation logs.",
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=root / "data" / "processed" / "evaluation" / "qa_eval_cross_domain_summary.json",
        help="Output JSON path for batch-ready cross-domain/shared-layer summary metrics.",
    )
    parser.add_argument(
        "--quality-summary-csv",
        type=Path,
        default=root / "data" / "processed" / "evaluation" / "qa_eval_quality_summary.csv",
        help="Output CSV path for compact quality/degrade counters (metric,value).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_jsonl_records(args.input)
    n_jsonl = export_logs_jsonl(records, args.out_jsonl)
    n_csv = export_logs_csv(records, args.out_csv)
    cross_domain_summary = summarize_cross_domain_metrics(records)
    quality_summary = summarize_quality_degrade_metrics(records)
    summary = {
        **cross_domain_summary,
        "quality_degrade_summary": quality_summary,
    }
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    export_quality_degrade_summary_csv(quality_summary, args.quality_summary_csv)
    print(f"[qa-eval-export] rows={n_jsonl} jsonl={args.out_jsonl}")
    print(f"[qa-eval-export] rows={n_csv} csv={args.out_csv}")
    print(f"[qa-eval-export] summary_json={args.summary_json}")
    print(
        "[qa-eval-export] quality="
        f"answered={quality_summary.get('total_answered', 0)} "
        f"partial={quality_summary.get('total_partial', 0)} "
        f"forward_fail={quality_summary.get('total_forward_failure_fallback', 0)} "
        f"unification_broken={quality_summary.get('total_unification_broken', 0)} "
        f"verified_final={quality_summary.get('total_verified_final', 0)}"
    )
    print(f"[qa-eval-export] quality_summary_csv={args.quality_summary_csv}")


if __name__ == "__main__":
    main()
