"""Emit rulebase_reasoning_core.json from rulebase_logic.json (high-precision subset)."""

from __future__ import annotations

import argparse
from pathlib import Path

from law_side.rulebase_reasoning_core import (
    build_reasoning_core_package,
    load_logic_json,
    write_reasoning_core_json,
)
from pipelines._paths import legal_qa_nesy_root


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(description="Extract rules_reasoning_core from rulebase_logic.json")
    p.add_argument(
        "--input",
        type=Path,
        default=root / "data" / "processed" / "rulebase" / "rulebase_logic.json",
        help="Path to rulebase_logic.json",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=root / "data" / "processed" / "rulebase" / "rulebase_reasoning_core.json",
        help="Output path for reasoning core package",
    )
    args = p.parse_args()
    inp = args.input if args.input.is_absolute() else root / args.input
    out = args.output if args.output.is_absolute() else root / args.output

    payload = load_logic_json(inp)
    pkg = build_reasoning_core_package(
        logic_payload=payload,
        source_path=inp.relative_to(root) if inp.is_relative_to(root) else inp,
    )
    write_reasoning_core_json(pkg, out)
    r = pkg.get("report") or {}
    print(f"Wrote {pkg['core_rule_count']} core rules -> {out}")
    print(
        "Report:",
        f"total={r.get('total_rules')}",
        f"exportable_clean={r.get('exportable_clean_count')}",
        f"core={r.get('core_rule_count')}",
        f"excluded_from_exportable_clean={r.get('excluded_exportable_clean_count')}",
    )


if __name__ == "__main__":
    main()
