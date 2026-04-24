#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.runtime_checks.run_all_types_minimal_eval import (
    BASE_URL,
    TEST_CASES,
    _build_summary,
    _error_row,
    _eval_case,
    _run_case,
)

OUT_PATH = Path("tests/runtime_checks/10case_final_tables.json")
CASES = TEST_CASES[:10]

rows = []
for case in CASES:
    print(f"  Running {case['test_id']} ({case['question_label']}) ...", flush=True)
    try:
        resp, http_status = _run_case(case)
        if http_status == 500:
            raise RuntimeError(f"HTTP 500 from server: {resp.get('detail','')}")
        row = _eval_case(case, resp)
    except Exception as exc:
        http_st = 500 if "500" in str(exc) else 0
        row = _error_row(case, exc, http_status=http_st)
    rows.append(row)
    err_tag = f" [{row.get('_error_type','')}]" if row.get("_error_type") else ""
    status = "PASS" if (row.get("answer_useful") and row.get("answer_grounded_to_rule")) else "FAIL"
    print(f"    mode={row['question_mode']} answer_type={row['answer_type']} {status}{err_tag}", flush=True)

summary = _build_summary(rows, CASES)
payload = {
    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "base_url": BASE_URL,
    "tests": rows,
    "summary": summary,
}
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nWROTE {OUT_PATH}")
print(f"\n=== SUMMARY ===")
print(f"  rule_reading_pass:     {summary['rule_reading_pass_count']}/{summary.get('rule_reading_total', summary.get('rule_reading_total_non_crash', 0))}" )
print(f"  fact_application_pass: {summary['fact_application_pass']}")
print(f"  table2 criteria:       {summary['table2_criteria_pass_count']}/{summary.get('table2_total', summary.get('table2_non_crash_total', 0))}")
print(f"  table1_ready:          {summary['table1_ready']}")
print(f"  table2_ready:          {summary['table2_ready']}")
if summary["blocker_types"]:
    print(f"  BLOCKERS:")
    for b in summary["blocker_types"]:
        print(f"    - {b}")
else:
    print(f"  No blockers.")
