"""Export rulebase_reasoning_core.json to ProbLog .pl + mapping JSON."""

from __future__ import annotations

import argparse
from pathlib import Path

from law_side.rulebase_reasoning_core_problog import write_reasoning_core_problog_artifacts
from pipelines._paths import legal_qa_nesy_root


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(
        description="Export rules_reasoning_core to rulebase_reasoning_core.pl + facts + mapping"
    )
    p.add_argument(
        "--input",
        type=Path,
        default=root / "data" / "processed" / "rulebase" / "rulebase_reasoning_core.json",
        help="Path to rulebase_reasoning_core.json",
    )
    p.add_argument(
        "--main",
        type=Path,
        default=root / "data" / "processed" / "rulebase" / "rulebase_reasoning_core.pl",
        help="Output main .pl",
    )
    p.add_argument(
        "--facts",
        type=Path,
        default=root / "data" / "processed" / "rulebase" / "rulebase_reasoning_core_facts.pl",
        help="Output facts .pl",
    )
    p.add_argument(
        "--mapping",
        type=Path,
        default=root / "data" / "processed" / "rulebase" / "rulebase_reasoning_core_mapping.json",
        help="Output mapping JSON",
    )
    args = p.parse_args()
    inp = args.input if args.input.is_absolute() else root / args.input
    out_m = args.main if args.main.is_absolute() else root / args.main
    out_f = args.facts if args.facts.is_absolute() else root / args.facts
    out_map = args.mapping if args.mapping.is_absolute() else root / args.mapping

    report = write_reasoning_core_problog_artifacts(
        inp, out_m, out_f, out_map, repo_root=root
    )
    s = report.get("export_summary", {})
    print(f"Wrote {out_m}")
    print(f"Wrote {out_f}")
    print(f"Wrote {out_map}")
    print(
        "Summary:",
        f"rules_ok={s.get('rules_exported_ok')}/{s.get('rules_in_core_input')}",
        f"skipped={s.get('rules_skipped')}",
        f"clauses={s.get('clauses_emitted')}",
        f"facts_file_lines={s.get('facts_file_lines_emitted')}",
        f"dossier_item={s.get('dossier_item_facts')}",
    )


if __name__ == "__main__":
    main()
