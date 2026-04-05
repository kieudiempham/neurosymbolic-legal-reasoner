"""Regression: load parse fixtures, heuristic pipeline, field-level checks (no LLM)."""

from __future__ import annotations

from question_side.parse_regression_eval import aggregate_stats, evaluate_case
from question_side.parse_regression_fixtures import load_parse_regression_cases


def test_parse_regression_fixtures_load() -> None:
    cases = load_parse_regression_cases()
    assert len(cases) >= 85
    for c in cases:
        assert c.get("qid")
        assert c.get("question_text")
        assert "expected" in c


def test_parse_regression_heuristic_all_pass() -> None:
    cases = load_parse_regression_cases()
    results = [evaluate_case(c) for c in cases]
    failed = [r for r in results if r.failed_fields]
    stats = aggregate_stats(results)
    assert not failed, f"failed: {[(r.qid, r.failed_fields) for r in failed[:12]]}"
    assert stats["total"] == len(cases)
    assert stats["field_level_accuracy"].get("utterance_type", 0) >= 0.99


def test_parser_quality_report_script_smoke() -> None:
    import runpy
    import sys
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    script = repo / "scripts" / "parser_quality_report.py"
    sys.argv = [str(script), "--json-summary", str(repo / "tests" / ".parser_report_smoke.json")]
    try:
        runpy.run_path(str(script), run_name="__main__")
    finally:
        p = repo / "tests" / ".parser_report_smoke.json"
        if p.is_file():
            p.unlink()
