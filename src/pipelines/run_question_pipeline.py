"""Question-side pipeline: raw text → layer1/layer2 interim artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from utils.io import read_yaml

from pipelines._paths import legal_qa_nesy_root


def run(config_path: Path) -> None:
    """Run slot extraction, normalization, optional parse repair; write interim JSONL."""
    _ = read_yaml(config_path)
    # from question_side.layer1_slot_extractor import Layer1SlotExtractor
    raise NotImplementedError("question pipeline")


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(description="Run question parsing pipeline.")
    p.add_argument(
        "--config",
        type=Path,
        default=root / "configs" / "parser.yaml",
        help="Parser config YAML.",
    )
    args = p.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
