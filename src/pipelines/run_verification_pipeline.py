"""Verification pipeline: run verifiers over interim artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from utils.io import read_yaml

from pipelines._paths import legal_qa_nesy_root


def run(config_path: Path) -> None:
    """Run parse, rule, backward, forward, and answer verifiers; write interim/verification."""
    _ = read_yaml(config_path)
    raise NotImplementedError("verification pipeline")


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(description="Run verification pipeline.")
    p.add_argument(
        "--config",
        type=Path,
        default=root / "configs" / "verification.yaml",
    )
    args = p.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
