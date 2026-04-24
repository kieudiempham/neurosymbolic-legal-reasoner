"""Aggregate cross-domain/shared-layer contribution metrics from QA evaluation logs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evaluation.qa_log_exporter import load_jsonl_records
from evaluation.cross_domain_metrics_aggregator import aggregate_contribution_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate contribution of shared-layer and cross-domain reasoning from QA eval logs.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input normalized QA evaluation logs JSONL.",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=ROOT / "data" / "processed" / "evaluation" / "cross_domain_metrics_summary.json",
        help="Output JSON summary path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_jsonl_records(args.input)
    summary = aggregate_contribution_metrics(records)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[cross-domain-agg] rows={summary.get('rows_total', 0)}")
    print(f"[cross-domain-agg] jump_success_rate={summary.get('contribution_metrics', {}).get('jump_success_rate', 0.0):.4f}")
    print(f"[cross-domain-agg] shared_layer_activation_rate={summary.get('contribution_metrics', {}).get('shared_layer_activation_rate', 0.0):.4f}")
    print(f"[cross-domain-agg] out={args.out_json}")


if __name__ == "__main__":
    main()
