"""Emit rulebase_reasoning_core.json from rulebase_logic.json (high-precision subset)."""

from __future__ import annotations

import argparse
from pathlib import Path

from law_side.rulebase_reasoning_core import (
    build_reasoning_core_package,
    build_reasoning_core_package_from_canonical,
    load_canonical_jsonl,
    load_logic_json,
    write_reasoning_core_json,
)
from pipelines._paths import legal_qa_nesy_root


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(
        description=(
            "Extract rulebase_reasoning_core.json from canonical_rules.jsonl (preferred) "
            "or legacy rulebase_logic.json (fallback)."
        )
    )
    p.add_argument(
        "--input",
        type=Path,
        default=root / "data" / "processed" / "rulebase" / "enterprise" / "canonical_rules.jsonl",
        help="Path to canonical_rules.jsonl or legacy rulebase_logic.json",
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

    if inp.suffix == ".jsonl":
        canonical_rules = load_canonical_jsonl(inp)
        pkg = build_reasoning_core_package_from_canonical(
            canonical_rules=canonical_rules,
            source_path=inp.relative_to(root) if inp.is_relative_to(root) else inp,
        )
    else:
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
        f"core={r.get('core_rule_count')}",
    )


if __name__ == "__main__":
    main()
