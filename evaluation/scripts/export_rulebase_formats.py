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
    p.add_argument(
        "--vocab",
        type=Path,
        default=root / "data" / "processed" / "ontology" / "controlled_vocabulary.xlsx",
        help="controlled_vocabulary.xlsx (join for canonical fields)",
    )
    p.add_argument(
        "--problog",
        type=Path,
        default=None,
        help="Optional ProbLog-style text (omit this step to only refresh JSONL + logic JSON)",
    )
    args = p.parse_args()

    inp = args.input if args.input.is_absolute() else root / args.input
    out_j = args.jsonl if args.jsonl.is_absolute() else root / args.jsonl
    out_l = args.logic if args.logic.is_absolute() else root / args.logic
    vocab = args.vocab if args.vocab.is_absolute() else root / args.vocab
    out_p = None
    if args.problog is not None:
        out_p = args.problog if args.problog.is_absolute() else root / args.problog

    n, m, stats = export_rulebase_formats(inp, out_j, out_l, vocab_path=vocab, out_problog=out_p)
    print(f"Wrote {n} lines -> {out_j}")
    print(f"Wrote {m} logic records -> {out_l}")
    if out_p:
        print(f"Wrote ProbLog -> {out_p}")
    print(
        "Stats:",
        f"predicate_mapped={stats.get('predicate_mapped')}",
        f"effect_mapped={stats.get('effect_mapped')}",
        f"object_mapped={stats.get('object_mapped')}",
        f"threshold={stats.get('threshold_rules')}",
        f"threshold_range={stats.get('threshold_range_rules')}",
        f"raw_condition_body={stats.get('body_used_raw_condition')}",
        f"raw_scope_body={stats.get('body_used_raw_scope')}",
    )


if __name__ == "__main__":
    main()
