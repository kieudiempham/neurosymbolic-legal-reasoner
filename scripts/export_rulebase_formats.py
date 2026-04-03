"""Export rulebase_seed.xlsx to rulebase.jsonl and rulebase_logic.json."""

from __future__ import annotations

import argparse
from pathlib import Path

from law_side.rulebase_export_formats import export_rulebase_formats
from pipelines._paths import legal_qa_nesy_root


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(
        description="Export rulebase_seed.xlsx to JSONL (rich) and JSON (logic)."
    )
    p.add_argument(
        "--input",
        type=Path,
        default=root / "data" / "processed" / "rulebase" / "rulebase_seed.xlsx",
        help="Path to rulebase_seed.xlsx",
    )
    p.add_argument(
        "--jsonl",
        type=Path,
        default=root / "data" / "processed" / "rulebase" / "rulebase.jsonl",
        help="Output JSONL path",
    )
    p.add_argument(
        "--logic",
        type=Path,
        default=root / "data" / "processed" / "rulebase" / "rulebase_logic.json",
        help="Output logic JSON path",
    )
    args = p.parse_args()

    inp = args.input if args.input.is_absolute() else root / args.input
    out_j = args.jsonl if args.jsonl.is_absolute() else root / args.jsonl
    out_l = args.logic if args.logic.is_absolute() else root / args.logic

    n, m = export_rulebase_formats(inp, out_j, out_l)
    print(f"Wrote {n} lines -> {out_j}")
    print(f"Wrote {m} logic records -> {out_l}")


if __name__ == "__main__":
    main()
