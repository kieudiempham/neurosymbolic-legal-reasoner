# ACIIDS result tables

Measurement (NLI) for all diagnosing methods: mDeBERTa + GPT-4o-mini (mean of label distributions, prompt v4, τ = 0.50, positive template), all chosen on the **development split only**. Numbers are on **held-out test** data unless marked dev.

## Table 1 — Overall performance (controlled fault injection, 5 domains, test pooled)

n = 451 test instances (each a question with one injected or natural fault, or none).

| Method | QA accuracy | QA acc. on faulty inputs | Diagnosis acc. | Diagnostic macro-F1 | Correct action | Recovery gain (pp) | Clarifications / query |
|---|---|---|---|---|---|---|---|
| Symbolic QA (no diagnosis) | 15.3 | 4.3 | – | – | – | – | 0.00 |
| Direct symptom→cause (no MBD) | 57.0 | 51.4 | 39.7 | 24.6 | 39.7 | +47.1 | 3.16 |
| Heuristic IF–THEN diagnosis | 85.1 | 85.7 | 68.5 | 67.4 | 68.5 | +81.5 | 3.71 |
| **Ours: Cross-Layer MBD** | 85.1 | 85.7 | 66.1 | 66.8 | 68.3 | +81.5 | 1.70 |

GPT-4o (pure LLM) and IRAC score: not run yet.

## Table 2 — Diagnosis by fault type (external F1–F4 set, faults chosen without the KB, test)

| Fault type | Heuristic | Ours | n |
|---|---|---|---|
| F1 — MissingCaseInformation | 72.7 | 72.7 | 11 |
| F2 — ParserOmission | 42.9 | 42.9 | 7 |
| F3 — ParserMisinterpretation | 87.5 | 87.5 | 8 |
| F4 — UnsupportedParserFact | 81.8 | 81.8 | 11 |
| *Heuristic: all observable* | | | |
|  diagnosis acc. 73.0 [55, 88], correct action 73.0, QA acc. 71.7, false alarms on CONTROL 33.3, clarifications/query 1.58 | | | |
| *Ours: all observable* | | | |
|  diagnosis acc. 70.3 [51, 87], correct action 73.0, QA acc. 73.3, false alarms on CONTROL 33.3, clarifications/query 0.55 | | | |

Correct action = diagnosis correct, or the only open choice is missing-vs-omitted on the true proposition and the system asks the user about exactly it. 95% CI: bootstrap over source questions.

## Table 3 — Effect of the measurement (NLI) model on Ours (external F1–F4, test)

| Measurement | NLI macro-F1 (dev pairs) | Diagnosis acc. | Correct action | QA acc. | False alarms | Clarifications / query |
|---|---|---|---|---|---|---|
| mDeBERTa-v3 (XNLI classifier) | 0.44 | 35.1 | 51.4 | 56.7 | 16.7 | 1.40 |
| Qwen2.5-7B-Instruct (open LLM) | 0.68 | 32.4 | 35.1 | 80.0 | 50.0 | 4.38 |
| GPT-4o-mini | 0.71 | 62.2 | 64.9 | 71.7 | 33.3 | 0.72 |
| mDeBERTa + Qwen2.5-7B | 0.68 | 45.9 | 59.5 | 75.0 | 16.7 | 3.72 |
| **mDeBERTa + GPT-4o-mini** | 0.70 | 70.3 | 73.0 | 73.3 | 33.3 | 0.55 |
| Perfect measurement (oracle, upper bound) | 1.00 | 100.0 | 100.0 | 91.7 | 0.0 | – |

NLI macro-F1: argmax label vs. annotated question content on 1,306 labelled development pairs.

## Table 4 — Per domain (controlled fault injection, Ours vs Heuristic)

| Domain | Split | n | QA acc. Ours | QA acc. Heur. | Diag. Ours | Diag. Heur. | Clarif./q Ours | Clarif./q Heur. |
|---|---|---|---|---|---|---|---|---|
| Social insurance | dev | 994 | 89.8 | 91.4 | 71.5 | 71.2 | 0.92 | 1.96 |
| Enterprise | dev | 163 | 88.3 | 87.7 | 66.9 | 68.1 | 0.55 | 0.53 |
| Enterprise | test | 164 | 75.0 | 75.0 | 51.2 | 54.3 | 0.48 | 0.47 |
| Tax | dev | 151 | 90.1 | 90.7 | 44.4 | 44.4 | 2.05 | 3.74 |
| Tax | test | 130 | 81.5 | 81.5 | 60.8 | 63.8 | 4.82 | 11.80 |
| Labour | dev | 82 | 92.7 | 93.9 | 74.4 | 74.4 | 0.37 | 0.43 |
| Labour | test | 51 | 96.1 | 96.1 | 80.4 | 84.3 | 0.25 | 0.25 |
| Cross-domain | dev | 109 | 82.6 | 80.7 | 53.2 | 54.1 | 1.13 | 1.10 |
| Cross-domain | test | 106 | 100.0 | 100.0 | 88.7 | 88.7 | 0.45 | 0.45 |

Social insurance has no test split (all 90 questions were used to develop the KB).

## Table 5 — Ablation (controlled fault injection, test pooled)

| Variant | QA acc. | Diagnosis acc. | Clarifications / query |
|---|---|---|---|
| Ours (full) | 85.1 | 66.1 | 1.70 |
| − acceptance test (raw NLI labels) | 85.1 | 62.3 | 1.69 |
| − MBD (symptom→cause mapping) | 57.0 | 39.7 | 3.16 |
| − diagnosis & recovery | 15.3 | – | 0.00 |
## Table 6 — QA accuracy under an equal clarification budget (injected faults, test, n = 451)

The simulated user answers at most B clarification questions per query (budgets fixed in advance).

| Method | B = 0 | B = 1 | B = 2 | unlimited | NLI measurements / query | KB checks / query |
|---|---|---|---|---|---|---|
| Direct symptom→cause (no MBD) | 20.6 | 48.6 | 49.5 | 57.0 | 0.00 | 0.00 |
| Heuristic IF–THEN | 72.5 | 82.7 | 82.9 | 85.1 | 5.79 | 0.37 |
| **Ours: Cross-Layer MBD** | 71.4 | 81.6 | 82.3 | 85.1 | 5.56 | 0.37 |

## Table 8 — End-to-end QA on the 300 questions (real GPT-4o parser, oracle goal, no simulated user) and IRAC

Parser vs gold facts: precision 88.9, recall 84.7. IRAC: 40 stratified questions, blind, judge GPT-4.1, rubric 100·(0.10 I + 0.35 R + 0.40 A + 0.15 C).

| Method | QA test (n=106) | QA dev (n=194) | QA all (n=300) | yes / no / insufficient (all) | IRAC | I | R | A | C |
|---|---|---|---|---|---|---|---|---|---|
| GPT-4o (pure LLM) | 70.8 | 71.7 | 71.3 | 82.6 / 68.2 / 52.1 | 71.2 | 1.0 | 0.55 | 0.787 | 0.7 |
| Symbolic QA | 61.3 | 68.0 | 65.7 | 57.6 / 67.1 / 80.3 | 68.8 | 0.775 | 0.613 | 0.738 | 0.675 |
| Heuristic IF–THEN | 66.0 | 86.1 | 79.0 | 89.6 / 68.2 / 70.4 | 71.1 | 0.675 | 0.625 | 0.762 | 0.8 |
| **Ours: Cross-Layer MBD** | 65.1 | 85.6 | 78.3 | 88.2 / 68.2 / 70.4 | 70.0 | 0.713 | 0.637 | 0.725 | 0.775 |

Test QA by domain (social insurance: dev): bhxh: gpt4o 68.9, heuristic 92.2, ours 92.2 (n=90); doanh_nghiep: gpt4o 74.3, heuristic 62.9, ours 62.9 (n=35); thue: gpt4o 63.9, heuristic 58.3, ours 55.6 (n=36); lao_dong: gpt4o 80.0, heuristic 60.0, ours 60.0 (n=15); lien_nganh: gpt4o 70.0, heuristic 90.0, ours 90.0 (n=20)

## Table 7 — Two simultaneous faults on different propositions (test; dev in parentheses)

| Method | Both faults found | ≥ 1 found | QA acc. | Clarifications / query | n |
|---|---|---|---|---|---|
| Direct symptom→cause (no MBD) | 0.0 (0.0) | 21.1 (19.2) | 1.9 (1.4) | 5.62 (1.97) | 104 (349) |
| Heuristic IF–THEN | 59.6 (67.9) | 90.4 (94.8) | 81.7 (83.4) | 5.79 (2.60) | 104 (349) |
| **Ours: Cross-Layer MBD** | 59.6 (67.0) | 88.5 (94.8) | 81.7 (80.5) | 2.38 (1.60) | 104 (349) |

