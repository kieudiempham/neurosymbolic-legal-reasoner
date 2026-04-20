"""Parser sanity probe with UTF-8 fixture input and encoding hygiene guard.

Usage (PowerShell):
  $env:PYTHONPATH='src'; python scripts/parser_sanity_probe.py
  $env:PYTHONPATH='src'; python scripts/parser_sanity_probe.py --queries-file tests/fixtures/parser_sanity_queries_utf8.json

Optional hardening:
  $env:PYTHONIOENCODING='utf-8'
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from question_side.heuristic_layer1 import parse_question_layer1_heuristic
from question_side.question_normalizer import build_layer2
from utils.text import assert_clean_unicode_input


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parse_args() -> argparse.Namespace:
    repo = _repo_root()
    parser = argparse.ArgumentParser(description="Run parser sanity probe on UTF-8 fixture queries")
    parser.add_argument(
        "--queries-file",
        type=Path,
        default=repo / "tests" / "fixtures" / "parser_sanity_queries_utf8.json",
        help="JSON file containing array of question strings (UTF-8)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional output JSON path for probe results",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo = _repo_root()
    qpath = args.queries_file if args.queries_file.is_absolute() else (repo / args.queries_file)

    data = json.loads(qpath.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
        raise ValueError("queries file must be a JSON array of strings")

    out_rows: list[dict[str, object]] = []
    for i, q in enumerate(data, 1):
        assert_clean_unicode_input(q, where=f"queries[{i}]")
        l1 = parse_question_layer1_heuristic(q)
        l2 = build_layer2(l1, user_facts=[])
        intent = (l2.diagnostics or {}).get("intent_structure") or {}
        out_rows.append(
            {
                "index": i,
                "question": q,
                "focus": l1.question_focus,
                "goal": l2.goal,
                "has_multi_intent": bool(l1.parse_metadata.get("has_multi_intent", False)),
                "intent_units": l1.parse_metadata.get("intent_units", []),
                "sub_goals": intent.get("sub_goals", []),
            }
        )

    payload = {"queries_file": str(qpath), "count": len(out_rows), "results": out_rows}
    as_json = json.dumps(payload, ensure_ascii=False, indent=2)
    print(as_json)

    if args.out is not None:
        opath = args.out if args.out.is_absolute() else (repo / args.out)
        opath.parent.mkdir(parents=True, exist_ok=True)
        opath.write_text(as_json + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())