## 12 ca REJECT moi (rerun_1) - root cause theo tung cau

| Cau | Focus | symbolic_ok | nli_label | nli_contradiction | debug_error | root_cause |
|---|---|---:|---|---:|---|---|
| q_3 | deadline | True | contradiction | 0.7935 | parse_rejected | nli_contradiction_high; overrides_symbolic_pass |
| q_6 | deadline | True | contradiction | 0.3918 | parse_rejected | nli_contradiction_moderate |
| q_8 | applicability | True | contradiction | 0.5693 | parse_rejected | nli_contradiction_moderate |
| q_10 | deadline | True | contradiction | 0.7148 | parse_rejected | nli_contradiction_high; overrides_symbolic_pass |
| q_12 | obligation | True | neutral | 0.3513 | parse_rejected | nli_contradiction_moderate |
| q_13 | deadline | True | contradiction | 0.6123 | parse_rejected | nli_contradiction_moderate |
| q_14 | deadline | True | contradiction | 0.6572 | parse_rejected | nli_contradiction_moderate |
| q_15 | legal_consequence | True | contradiction | 0.4800 | parse_rejected | nli_contradiction_moderate |
| q_18 | obligation | True | neutral | 0.4043 | parse_rejected | nli_contradiction_moderate |
| q_23 | deadline | True | contradiction | 0.6616 | parse_rejected | nli_contradiction_moderate |
| q_26 | deadline | True | contradiction | 0.6450 | parse_rejected | nli_contradiction_moderate |
| q_27 | deadline | True | contradiction | 0.5840 | parse_rejected | nli_contradiction_moderate |

## Delta 3 cot (baseline -> rerun_1 -> rerun_2)

| Chi so | Baseline | Rerun_1 | Rerun_2 |
|---|---:|---:|---:|
| total_cases | 30 | 30 | 30 |
| action_text_empty | 7 | 0 | 0 |
| parse_reject | 15 | 12 | 0 |
| parse_repair | 15 | 18 | 0 |
| has_retrieval | 15 | 18 | 0 |
| has_answer | 15 | 18 | 0 |
| degraded_honest | 15 | 18 | 0 |
| reason_no_grounded_rule_found | 15 | 18 | 0 |
