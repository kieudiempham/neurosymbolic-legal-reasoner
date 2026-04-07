"""CLI runner for the Vietnamese law rule-base first-pass pipeline.

This script is meant to be easy to run in a research setting.
If you execute it directly (not via editable install), it will add `src/`
to `sys.path` so imports like `law_side.*` work.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure `src/` is importable when running the file directly.
_this_file = Path(__file__).resolve()
_src_root = _this_file.parents[1]
_repo_root = _this_file.parents[2]
if str(_src_root) not in sys.path:
    sys.path.insert(0, str(_src_root))

from law_side.law_rulebase_pipeline import LawRulebasePipeline  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    root = _repo_root
    p = argparse.ArgumentParser(description="Run law rule-base first-pass pipeline (rule-based NLP).")
    p.add_argument(
        "--config",
        type=Path,
        default=root / "configs" / "law_rulebase_pipeline.yaml",
        help="YAML config for the pipeline.",
    )
    p.add_argument(
        "--domain",
        type=str,
        default=None,
        help="Domain to process (enterprise, labor, tax).",
    )
    p.add_argument(
        "--input_dir",
        type=Path,
        default=None,
        help="Override input document directory.",
    )
    p.add_argument(
        "--doc_files",
        nargs="+",
        default=None,
        help="Override list of input .doc filenames.",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()
    root = _repo_root

    # Load pipeline from config.
    pipeline = LawRulebasePipeline.from_yaml(args.config)

    # Apply domain override
    if args.domain is not None:
        pipeline._config.domain = args.domain  # type: ignore[attr-defined]

    # Apply overrides.
    if args.input_dir is not None:
        pipeline._config.input_dir = args.input_dir  # type: ignore[attr-defined]
    if args.doc_files is not None:
        pipeline._config.doc_files = list(args.doc_files)  # type: ignore[attr-defined]

    outputs = pipeline.run()
    print("Rule-base pipeline finished. Outputs:")
    for k, v in outputs.items():
        print(f"- {k}: {v}")


if __name__ == "__main__":
    main()

