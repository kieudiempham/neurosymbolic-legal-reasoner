"""Generate only legal_units_review.xlsx for configured law docs."""

from __future__ import annotations

import argparse
from pathlib import Path

from law_side.doc_loader import DocLoader
from law_side.export_to_excel import export_legal_units_review
from law_side.legal_segmenter import LegalSegmenter
from law_side.law_rulebase_models import LegalUnit
from pipelines._paths import legal_qa_nesy_root
from utils.io import read_yaml


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(description="Generate only legal units review Excel.")
    p.add_argument(
        "--config",
        type=Path,
        default=root / "configs" / "law_rulebase_pipeline.yaml",
        help="YAML config with input_dir and doc_files.",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=root / "data/interim/law_parsing/legal_units_review.xlsx",
        help="Output legal units xlsx path.",
    )
    args = p.parse_args()

    cfg = read_yaml(args.config)

    input_dir = Path(cfg.get("input_dir", "data/raw/legal_corpus/doc"))
    if not input_dir.is_absolute():
        input_dir = root / input_dir

    doc_files = list(cfg.get("doc_files", []))
    if not doc_files:
        raise ValueError("Config `doc_files` is empty. Please provide input .doc files.")

    loader = DocLoader(config=cfg.get("doc_loader", {}))
    docs = loader.load_documents(input_dir, doc_files)

    segmenter = LegalSegmenter(config=cfg.get("segmentation", {}))
    legal_units: list[LegalUnit] = []
    for doc in docs:
        legal_units.extend(segmenter.segment(doc))

    out_path = args.output
    if not out_path.is_absolute():
        out_path = root / out_path
    export_legal_units_review(
        legal_units=legal_units,
        out_legal_units=out_path,
        autosize=bool(cfg.get("autosize", False)),
    )
    print(f"Legal units review generated: {out_path}")


if __name__ == "__main__":
    main()
