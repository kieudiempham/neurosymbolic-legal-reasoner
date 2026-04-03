"""End-to-end pipeline: orchestrate question → law → retrieval → reasoning → verify → generate."""

from __future__ import annotations

import argparse
from pathlib import Path

from utils.io import read_yaml

from pipelines._paths import legal_qa_nesy_root


def run(exp_config: Path) -> None:
    """Chain sub-pipelines, write logs under experiments/logs and predictions under experiments/predictions."""
    _ = read_yaml(exp_config)
    raise NotImplementedError("end-to-end pipeline")


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(description="Run end-to-end experiment pipeline.")
    p.add_argument(
        "--config",
        type=Path,
        default=root / "configs" / "experiments" / "exp_end2end.yaml",
    )
    args = p.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
