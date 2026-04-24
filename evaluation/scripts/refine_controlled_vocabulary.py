"""Ghi đè controlled_vocabulary.xlsx bản tinh chỉnh (không sửa rulebase_seed)."""

from __future__ import annotations

import argparse
from pathlib import Path

from law_side.refine_controlled_vocabulary import refine_controlled_vocabulary_workbook
from pipelines._paths import legal_qa_nesy_root


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(description="Refine controlled_vocabulary.xlsx in place.")
    p.add_argument(
        "--vocab",
        type=Path,
        default=root / "data" / "processed" / "ontology" / "controlled_vocabulary.xlsx",
    )
    p.add_argument(
        "--rulebase",
        type=Path,
        default=root / "data" / "processed" / "rulebase" / "rulebase_seed.xlsx",
    )
    p.add_argument("--output", type=Path, default=None, help="Default: overwrite --vocab")
    args = p.parse_args()
    vocab = args.vocab if args.vocab.is_absolute() else root / args.vocab
    rb = args.rulebase if args.rulebase.is_absolute() else root / args.rulebase
    out = args.output
    refine_controlled_vocabulary_workbook(vocab, rb, out_path=out)
    print("Wrote:", out or vocab)


if __name__ == "__main__":
    main()
