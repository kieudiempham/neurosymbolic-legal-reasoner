"""Build controlled vocabulary Excel from rulebase_seed (does not modify seed)."""

from __future__ import annotations

import argparse
from pathlib import Path

from law_side.controlled_vocabulary_builder import write_controlled_vocabulary_excel
from pipelines._paths import legal_qa_nesy_root


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(
        description="Build controlled_vocabulary.xlsx from rulebase_seed and optional lexicon."
    )
    p.add_argument(
        "--rulebase",
        type=Path,
        default=root / "data" / "processed" / "rulebase" / "rulebase_seed.xlsx",
    )
    p.add_argument(
        "--lexicon",
        type=Path,
        default=root / "data" / "processed" / "ontology" / "predicate_lexicon.xlsx",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=root / "data" / "processed" / "ontology" / "controlled_vocabulary.xlsx",
    )
    p.add_argument("--no-lexicon", action="store_true", help="Skip predicate_lexicon merge.")
    args = p.parse_args()

    rb = args.rulebase if args.rulebase.is_absolute() else root / args.rulebase
    out = args.output if args.output.is_absolute() else root / args.output
    lex = None if args.no_lexicon else (args.lexicon if args.lexicon.is_absolute() else root / args.lexicon)

    write_controlled_vocabulary_excel(rb, out, lex)
    print("Wrote:", out)


if __name__ == "__main__":
    main()
