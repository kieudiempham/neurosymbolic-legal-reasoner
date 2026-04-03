"""Reasoning pipeline: retrieval outputs → backward/forward → proofs."""

from __future__ import annotations

import argparse
from pathlib import Path

from utils.io import read_yaml

from pipelines._paths import legal_qa_nesy_root


def run(backward_cfg: Path, forward_cfg: Path) -> None:
    """Merge backward and forward configs; write interim/reasoning artifacts."""
    _ = read_yaml(backward_cfg)
    _ = read_yaml(forward_cfg)
    raise NotImplementedError("reasoning pipeline")


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(description="Run reasoning pipeline.")
    p.add_argument(
        "--backward-config",
        type=Path,
        default=root / "configs" / "backward_reasoning.yaml",
    )
    p.add_argument(
        "--forward-config",
        type=Path,
        default=root / "configs" / "forward_reasoning.yaml",
    )
    args = p.parse_args()
    run(args.backward_config, args.forward_config)


if __name__ == "__main__":
    main()
