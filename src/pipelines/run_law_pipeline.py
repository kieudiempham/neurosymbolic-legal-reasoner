"""Law-side pipeline: corpus → segments → frames → rules → processed rulebase."""

from __future__ import annotations

import argparse
from pathlib import Path

from utils.io import read_yaml

from pipelines._paths import legal_qa_nesy_root


def run(config_path: Path) -> None:
    """PDF text, segmentation, normative detection, frames, rules, then export."""
    _ = read_yaml(config_path)
    raise NotImplementedError("law pipeline")


def main() -> None:
    root = legal_qa_nesy_root()
    p = argparse.ArgumentParser(description="Run law / rule construction pipeline.")
    p.add_argument(
        "--config",
        type=Path,
        default=root / "configs" / "rule_builder.yaml",
        help="Rule builder config YAML.",
    )
    args = p.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
