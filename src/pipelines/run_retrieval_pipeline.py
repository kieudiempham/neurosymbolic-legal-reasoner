"""Retrieval pipeline: parsed question + rulebase → ranked rules + evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from utils.io import read_yaml

from pipelines._paths import legal_qa_nesy_root


def run(config_path: Path) -> None:
    """Retrieve and rank rules, pull evidence spans; write interim/retrieval."""
    _ = read_yaml(config_path)
    raise NotImplementedError("retrieval pipeline")


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(description="Run retrieval pipeline.")
    p.add_argument(
        "--config",
        type=Path,
        default=root / "configs" / "retrieval.yaml",
    )
    args = p.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
