"""Export stable QA evaluation logs to JSONL/CSV from batch response artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evaluation.qa_log_exporter import export_logs_csv, export_logs_jsonl, load_jsonl_records


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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_jsonl_records(args.input)
    n_jsonl = export_logs_jsonl(records, args.out_jsonl)
    n_csv = export_logs_csv(records, args.out_csv)
    print(f"[qa-eval-export] rows={n_jsonl} jsonl={args.out_jsonl}")
    print(f"[qa-eval-export] rows={n_csv} csv={args.out_csv}")


if __name__ == "__main__":
    main()
