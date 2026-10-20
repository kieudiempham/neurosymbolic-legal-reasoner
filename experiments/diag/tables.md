## Table A. Diagnostic KB and benchmark

| Item | Value |
|---|---|
| predicates | 34 |
| input_predicates | 26 |
| derived_predicates | 8 |
| rules | 28 |
| rules_multi_premise | 22 |
| rules_explicit | 21 |
| rules_a_contrario | 7 |
| exception_of | 9 |
| priority_over | 0 |
| max_chain_depth | 4 |
| source_documents | 2 |
| gold_cases | 40 |
| gold_cases_real | 18 |
| gold_cases_synthetic | 22 |
| diagnostic instances | 125 |
| instances: MissingCaseInformation/injected | 20 |
| instances: MissingCaseInformation/natural | 7 |
| instances: Normal/natural | 27 |
| instances: ParserMisinterpretation/injected | 20 |
| instances: ParserOmission/injected | 20 |
| instances: ResolvableRuleOverlap/natural | 5 |
| instances: UnresolvedKBConflict/injected | 5 |
| instances: UnresolvedKBConflict/natural | 1 |
| instances: UnsupportedParserFact/injected | 20 |

## Table 2. Main comparison

| System | Diag. Acc. | Recovery | Final Acc. (all) | Final Acc. (faulty) | Measurements/query |
|---|---|---|---|---|---|
| Neural LLM (gpt-4o) | - | - | 78.4 | 75.5 | 0.00 |
| Base NeSy | - | - | 30.4 | 11.2 | 0.00 |
| NeSy + Proposed Diagnosis | 66.4 | 57.1 | 87.2 | 86.7 | 3.96 |

## Table 3. Diagnostic performance by category (NeSy + Proposed Diagnosis)

| Category | n | Precision | Recall | F1 | Exact diagnosis acc. |
|---|---|---|---|---|---|
| Normal | 27 | 100.0 | 85.2 | 92.0 | 85.2 |
| MissingCaseInformation | 27 | 65.4 | 63.0 | 64.2 | 33.3 |
| ParserOmission | 20 | 64.7 | 55.0 | 59.5 | 60.0 |
| ParserMisinterpretation | 20 | 65.5 | 95.0 | 77.6 | 90.0 |
| UnsupportedParserFact | 20 | 55.6 | 50.0 | 52.6 | 50.0 |
| ResolvableRuleOverlap | 5 | 83.3 | 100.0 | 90.9 | 100.0 |
| UnresolvedKBConflict | 6 | 100.0 | 100.0 | 100.0 | 100.0 |

Confusion (rows = gold, columns = predicted):

| gold \ pred | Normal | MissingCaseInformation | ParserOmission | ParserMisinterpretation | UnsupportedParserFact | ResolvableRuleOverlap | UnresolvedKBConflict | Ambiguous |
|---|---|---|---|---|---|---|---|---|
| Normal | 23 | 0 | 0 | 2 | 2 | 0 | 0 | 0 |
| MissingCaseInformation | 0 | 17 | 6 | 0 | 4 | 0 | 0 | 0 |
| ParserOmission | 0 | 8 | 11 | 0 | 1 | 0 | 0 | 0 |
| ParserMisinterpretation | 0 | 0 | 0 | 19 | 1 | 0 | 0 | 0 |
| UnsupportedParserFact | 0 | 1 | 0 | 8 | 10 | 1 | 0 | 0 |
| ResolvableRuleOverlap | 0 | 0 | 0 | 0 | 0 | 5 | 0 | 0 |
| UnresolvedKBConflict | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |

## Table 5. NLI reliability (targeted measurements)

n = 467, accuracy = 86.1, macro-F1 = 81.0

| gold \ pred | entail | neutral | contra |
|---|---|---|---|
| entail | 278 | 8 | 0 |
| neutral | 33 | 57 | 8 |
| contra | 6 | 10 | 67 |

## Table 4. Ablation

| Configuration | Diag. Acc. | Measurements/query | Recovery | Final Acc. (faulty) |
|---|---|---|---|---|
| Full framework | 66.4 | 3.96 | 57.1 | 86.7 |
| Without MBD / minimal diagnosis | 48.0 | 0.00 | 33.7 | 57.1 |
| Without diagnosis-directed evidence selection | 66.4 | 4.25 | 57.1 | 86.7 |

## Table 6. Final-answer accuracy by gold category

| Category | n | Neural LLM (gpt-4o) | Base NeSy | NeSy + Proposed Diagnosis |
|---|---|---|---|---|
| Normal | 27 | 88.9 | 100.0 | 88.9 |
| MissingCaseInformation | 27 | 48.1 | 0.0 | 88.9 |
| ParserOmission | 20 | 90.0 | 0.0 | 80.0 |
| ParserMisinterpretation | 20 | 90.0 | 10.0 | 95.0 |
| UnsupportedParserFact | 20 | 100.0 | 15.0 | 75.0 |
| ResolvableRuleOverlap | 5 | 100.0 | 0.0 | 100.0 |
| UnresolvedKBConflict | 6 | 0.0 | 100.0 | 100.0 |

Answer behaviour on Missing Case Information instances (definite answer given without the missing fact):

- Neural LLM (gpt-4o): 20/27 definite answers without asking
- Base NeSy: 0/27 definite answers without asking
- NeSy + Proposed Diagnosis: 0/27 definite answers without asking

## Table 7. Real LLM parser (gpt-4o) — naturally occurring parser errors

| Item | Value |
|---|---|
| distinct questions | 93 |
| parse fact P / R / F1 | 83.4 / 83.1 / 83.2 |
| questions parsed exactly | 46.2 |
| parse errors (omitted / wrong value / spurious) | 40 / 1 / 39 |
| Base NeSy final acc. (all) | 23.7 |
| NeSy + Diagnosis final acc. (all) | 87.1 |
| questions with a parse error | 50 |
| Base NeSy final acc. on those | 14.0 |
| NeSy + Diagnosis final acc. on those | 80.0 |
| measurements / query | 3.83 |
| diagnosed fault categories | {'ParserOmission': 66, 'MissingCaseInformation': 48, 'ParserMisinterpretation': 7, 'UnsupportedParserFact': 13, 'ResolvableRuleOverlap': 2, 'UnresolvedKBConflict': 3} |
