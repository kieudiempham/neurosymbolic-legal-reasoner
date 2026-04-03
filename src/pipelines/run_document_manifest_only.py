"""Generate only document_manifest.xlsx for configured law docs."""

from __future__ import annotations

import argparse
from pathlib import Path

from law_side.doc_loader import DocLoader
from law_side.export_to_excel import export_document_manifest
from pipelines._paths import legal_qa_nesy_root
from utils.io import read_yaml


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(description="Generate only document manifest Excel.")
    p.add_argument(
        "--config",
        type=Path,
        default=root / "configs" / "law_rulebase_pipeline.yaml",
        help="YAML config with input_dir and doc_files.",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=root / "data/raw/legal_corpus/manifest/document_manifest.xlsx",
        help="Output manifest xlsx path.",
    )
    args = p.parse_args()

    cfg = read_yaml(args.config)

    input_dir = Path(cfg.get("input_dir", "data/raw/legal_corpus/doc"))
    if not input_dir.is_absolute():
        input_dir = root / input_dir

    doc_files = list(cfg.get("doc_files", []))
    if not doc_files:
        raise ValueError("Config `doc_files` is empty. Please provide the two input .doc files.")

    loader = DocLoader(config=cfg.get("doc_loader", {}))
    documents = loader.load_documents(input_dir, doc_files)

    out_path = args.output
    if not out_path.is_absolute():
        out_path = root / out_path
    export_document_manifest(
        documents=documents,
        out_document_manifest=out_path,
        autosize=bool(cfg.get("autosize", False)),
    )
    print(f"Document manifest generated: {out_path}")


if __name__ == "__main__":
    main()
