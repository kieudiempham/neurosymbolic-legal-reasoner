| Setting | Method | n | fault_precision | fault_recall | fault_f1 | exact_isolation | mean_diagnosis_size | clarifications_per_query | clarification_precision | unnecessary_clarifications_per_query | qa_acc | questions_per_correct_answer |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single test | Heuristic | 451 | 0.2402 | 0.7475 | 0.3635 | 0.5898 | 3.07 | 3.71 | 0.0455 | 3.54 | 0.8514 | 4.35 |
| single test | Ours | 451 | 0.3451 | 0.735 | 0.4696 | 0.5876 | 2.1 | 1.7 | 0.0966 | 1.53 | 0.8514 | 1.99 |
| single test | Ours - acceptance test | 451 | 0.3406 | 0.7075 | 0.4598 | 0.5521 | 2.03 | 1.69 | 0.0929 | 1.54 | 0.8514 | 1.99 |
| single test | Ours - MBD | 451 | 0.0893 | 0.34 | 0.1414 | 0.2971 | 4.56 | 3.16 | 0.1542 | 2.68 | 0.5698 | 5.55 |
| single dev | Heuristic | 1499 | 0.2893 | 0.7999 | 0.425 | 0.6197 | 2.76 | 1.84 | 0.0863 | 1.68 | 0.9033 | 2.04 |
| single dev | Ours | 1499 | 0.4351 | 0.7875 | 0.5605 | 0.6244 | 1.81 | 0.98 | 0.1631 | 0.82 | 0.8933 | 1.09 |
| single dev | Ours - acceptance test | 1499 | 0.4401 | 0.781 | 0.563 | 0.6111 | 1.76 | 1.04 | 0.1491 | 0.88 | 0.8959 | 1.16 |
| single dev | Ours - MBD | 1499 | 0.0666 | 0.3002 | 0.109 | 0.2402 | 5.03 | 3.9 | 0.1257 | 3.41 | 0.539 | 7.23 |
| two_faults test | Heuristic | 104 | 0.4082 | 0.4808 | 0.4415 | 0.0769 | 2.4 | 5.79 | 0.0432 | 5.54 | 0.8173 | 7.08 |
| two_faults test | Ours | 104 | 0.5673 | 0.4663 | 0.5119 | 0.0769 | 1.68 | 2.38 | 0.1129 | 2.12 | 0.8173 | 2.92 |
| two_faults test | Ours - MBD | 104 | 0.052 | 0.1058 | 0.0697 | 0.0 | 8.63 | 5.62 | 0.0667 | 5.25 | 0.0192 | 292.5 |
| two_faults dev | Heuristic | 349 | 0.7728 | 0.5215 | 0.6228 | 0.1289 | 1.38 | 2.6 | 0.1101 | 2.32 | 0.8338 | 3.12 |
| two_faults dev | Ours | 349 | 0.7896 | 0.5215 | 0.6281 | 0.1289 | 1.35 | 1.6 | 0.1914 | 1.3 | 0.8052 | 1.99 |
| two_faults dev | Ours - MBD | 349 | 0.1147 | 0.096 | 0.1045 | 0.0 | 3.42 | 1.97 | 0.1802 | 1.62 | 0.0143 | 137.6 |
