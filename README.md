# Neuro-Symbolic Legal Reasoner

## Running Backend Evaluation

This evaluation is batch API-based (calls backend HTTP endpoints), not manual UI testing.

### 1) Start backend

```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
```

### 2) Run the 20-case evaluation

```bash
python tests/runtime_checks/run_20case_eval.py
```

### 3) Paths

- Input dataset: tests/runtime_checks/20case_eval_dataset.json
- Output JSON: tests/runtime_checks/20case_eval_results.json
- Output tables: tests/runtime_checks/20case_eval_tables.md

### 4) Create a new evaluation set

1. Copy tests/runtime_checks/20case_eval_dataset.json.
2. Edit questions and labels (test_id, question_type, subtype, question).
3. Run with a custom dataset path if needed:

```bash
python tests/runtime_checks/run_20case_eval.py --dataset tests/runtime_checks/your_dataset.json
```

### 5) Crash handling and denominator policy

- If a case returns backend 500 or crashes, it is recorded with backend_error=true and retained in the per-case JSON.
- Crash cases are excluded from percentage denominators in Table 1 and Table 2.
- Crash count is reported separately for each question type in both tables.
- If backend is unreachable, the script prints a clear startup instruction and exits.

### 6) Table metrics summary

- Table 1 (IRAC-based answer quality):
  - Useful Answer (%): answer_useful=true / non-crash count.
  - Clear Legal Rule (%): answer_has_clear_legal_rule=true / non-crash count.
  - Case Application (%):
    - rule_reading: N/A.
    - fact_application: answer_has_case_application=true / non-crash count.
  - Estimated IRAC Score proxy:
    - IRAC_proxy = 0.35*clear_legal_rule + 0.40*case_application_or_analysis + 0.10*useful_answer + 0.15*grounded.
    - For rule_reading, clear_legal_rule is used as analysis proxy.

- Table 2 (Verifiability and faithfulness):
  - Grounded (%): answer_grounded_to_rule=true / non-crash count.
  - Proof Present (%): proof_present=true / non-crash count.
  - Verification Success (%): verification_success=true / non-crash count.
  - Missing Fact Correctness (%):
    - rule_reading: N/A.
    - fact_application: missing_facts_correct_if_needed=true / non-crash count.
