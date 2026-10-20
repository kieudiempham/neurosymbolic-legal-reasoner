# ACIIDS result tables

Measurement (NLI) for all diagnosing methods: mDeBERTa + GPT-4o-mini (mean of label distributions, prompt v4, τ = 0.50, positive template), all chosen on the **development split only**. Numbers are on **held-out test** data unless marked dev.

## Table 1 — Overall performance (controlled fault injection, 5 domains, test pooled)

n = 451 test instances (each a question with one injected or natural fault, or none).

| Method | QA accuracy | QA acc. on faulty inputs | Diagnosis acc. | Diagnostic macro-F1 | Correct action | Recovery gain (pp) | Clarifications / query |
|---|---|---|---|---|---|---|---|
| Symbolic QA (no diagnosis) | 15.3 | 4.3 | – | – | – | – | 0.00 |
| Direct symptom→cause (no MBD) | 57.0 | 51.4 | 39.7 | 24.6 | 39.7 | +47.1 | 3.16 |
| Heuristic IF–THEN diagnosis | 85.1 | 85.7 | 68.5 | 67.4 | 68.5 | +81.5 | 3.71 |
| **Ours: Cross-Layer MBD** | 81.6 | 81.7 | 63.4 | 62.1 | 65.0 | +77.4 | 0.35 |

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
|  diagnosis acc. 70.3 [51, 87], correct action 73.0, QA acc. 73.3, false alarms on CONTROL 33.3, clarifications/query 0.58 | | | |

Correct action = diagnosis correct, or the only open choice is missing-vs-omitted on the true proposition and the system asks the user about exactly it. 95% CI: bootstrap over source questions.

## Table 3 — Effect of the measurement (NLI) model on Ours (external F1–F4, test)

| Measurement | NLI macro-F1 (dev pairs) | Diagnosis acc. | Correct action | QA acc. | False alarms | Clarifications / query |
|---|---|---|---|---|---|---|
| mDeBERTa-v3 (XNLI classifier) | 0.44 | 35.1 | 51.4 | 53.3 | 16.7 | 0.32 |
| Qwen2.5-7B-Instruct (open LLM) | 0.68 | 32.4 | 35.1 | 65.0 | 50.0 | 1.02 |
| GPT-4o-mini | 0.71 | 62.2 | 64.9 | 71.7 | 33.3 | 0.75 |
| mDeBERTa + Qwen2.5-7B | 0.68 | 45.9 | 56.8 | 65.0 | 16.7 | 0.58 |
| **mDeBERTa + GPT-4o-mini** | 0.70 | 70.3 | 73.0 | 73.3 | 33.3 | 0.58 |
| Perfect measurement (oracle, upper bound) | 1.00 | 100.0 | 100.0 | 91.7 | 0.0 | – |

NLI macro-F1: argmax label vs. annotated question content on 1,306 labelled development pairs.

## Table 4 — Per domain (controlled fault injection, Ours vs Heuristic)

| Domain | Split | n | QA acc. Ours | QA acc. Heur. | Diag. Ours | Diag. Heur. | Clarif./q Ours | Clarif./q Heur. |
|---|---|---|---|---|---|---|---|---|
| Social insurance | dev | 994 | 85.8 | 91.4 | 71.3 | 71.2 | 0.54 | 1.96 |
| Enterprise | dev | 163 | 87.1 | 87.7 | 65.6 | 68.1 | 0.48 | 0.53 |
| Enterprise | test | 164 | 72.6 | 75.0 | 51.2 | 54.3 | 0.35 | 0.47 |
| Tax | dev | 151 | 83.4 | 90.7 | 43.0 | 44.4 | 0.55 | 3.74 |
| Tax | test | 130 | 72.3 | 81.5 | 58.5 | 63.8 | 0.30 | 11.80 |
| Labour | dev | 82 | 90.2 | 93.9 | 72.0 | 74.4 | 0.13 | 0.43 |
| Labour | test | 51 | 96.1 | 96.1 | 80.4 | 84.3 | 0.25 | 0.25 |
| Cross-domain | dev | 109 | 91.7 | 80.7 | 50.5 | 54.1 | 0.33 | 1.10 |
| Cross-domain | test | 106 | 100.0 | 100.0 | 80.2 | 88.7 | 0.46 | 0.45 |

Social insurance has no test split (all 90 questions were used to develop the KB).

## Table 5 — Ablation (controlled fault injection, test pooled)

| Variant | QA acc. | Diagnosis acc. | Clarifications / query |
|---|---|---|---|
| Ours (full) | 81.6 | 63.4 | 0.35 |
| − acceptance test (raw NLI labels) | 81.6 | 59.6 | 0.35 |
| − MBD (symptom→cause mapping) | 57.0 | 39.7 | 3.16 |
| − diagnosis & recovery | 15.3 | – | 0.00 |
## Table 6 — QA accuracy under an equal clarification budget (injected faults, test, n = 451)

The simulated user answers at most B clarification questions per query (budgets fixed in advance).

| Method | B = 0 | B = 1 | B = 2 | unlimited | NLI measurements / query | KB checks / query |
|---|---|---|---|---|---|---|
| Direct symptom→cause (no MBD) | 20.6 | 48.6 | 49.5 | 57.0 | 0.00 | 0.00 |
| Heuristic IF–THEN | 72.5 | 82.7 | 82.9 | 85.1 | 5.79 | 0.37 |
| **Ours: Cross-Layer MBD** | 69.0 | 79.2 | 79.8 | 81.6 | 5.54 | 0.34 |

