# Final Section 5 tables — 300 QA, 1950 single-fault and 453 two-fault diagnostic instances

**Table 1. Main comparison.** E2E QA: all 300 questions, real GPT-4o parser. Faulty QA, Clarif./query: 1774 faulty of the 1950 diagnostic instances / all 1950. IRAC: 300 questions (1,200 answers).

| Method | E2E QA Acc. ↑ | Faulty QA Acc. ↑ | Clarif. / query ↓ | IRAC ↑ |
|---|---|---|---|---|
| GPT-4o (pure LLM) | 71.3 | N/A | N/A | 58.0 |
| Symbolic QA | 65.7 | 3.7 | 0.00 | 66.2 |
| Heuristic diagnosis | 79.0 | 88.7 | 2.27 | 70.9 |
| **Ours (cross-layer MBD)** | 78.3 | 87.9 | 1.14 | 70.7 |

**Table 2. Diagnostic performance.** Single-fault: 1950 instances; two-fault: 453 instances. A reported fault counts as correct only if it was injected.

| Method | Fault F1-score (single-fault) ↑ | Fault F1-score (two-fault) ↑ | Extra faults / query ↓ | Unnecessary questions / query ↓ |
|---|---|---|---|---|
| Direct symptom→cause mapping | 11.6 | 9.3 | 3.69 | 3.24 |
| Heuristic diagnosis | 41.0 | 57.2 | 1.87 | 2.11 |
| **Ours (cross-layer MBD)** | 53.8 | 60.0 | 1.01 | 0.98 |

Ours − Heuristic (95% paired bootstrap): fault F1 single +12.8 [10.9, 14.9], two-fault +2.7 [0.4, 5.5]; unnecessary questions/query -1.13 [-1.39, -0.90].

**Two simultaneous faults (n = 453).**

| Method | Both faults found | ≥ 1 found | QA acc. | Clarif. / query |
|---|---|---|---|---|
| Direct mapping | 0.0 | 19.7 | 1.6 | 2.81 |
| Heuristic | 66.0 | 93.8 | 83.0 | 3.33 |
| Ours | 65.3 | 93.4 | 80.8 | 1.78 |

**Figure 1 data — QA accuracy vs clarification budget (n = 1950).**

| Method | B = 0 | B = 1 | B = 2 | unlimited |
|---|---|---|---|---|
| Direct mapping | 15.5 | 43.1 | 46.9 | 54.6 |
| Heuristic | 76.3 | 86.0 | 87.0 | 89.1 |
| Ours | 75.3 | 84.9 | 86.1 | 88.4 |

**Figure 2 data — ablation (n = 1950).**

| Variant | QA acc. | Fault F1-score | Clarif. / query |
|---|---|---|---|
| Ours (full) | 88.4 | 53.8 | 1.14 |
| − acceptance test | 88.6 | 53.8 | 1.19 |
| − MBD | 54.6 | 11.6 | 3.73 |
| − diagnosis & recovery | 12.4 | – | 0.00 |
