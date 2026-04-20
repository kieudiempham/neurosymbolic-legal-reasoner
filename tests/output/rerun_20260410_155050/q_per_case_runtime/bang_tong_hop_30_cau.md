## Phan A - Bang tong hop so lieu chung

| Chi so | Gia tri |
|---|---:|
| Tong so cau | 30 |
| Cau co parser backend llm_real | 30 |
| Cau co layer1 usable | 30 |
| Cau co layer2 usable | 30 |
| Cau mat top-level layer1/layer2 | 13 |
| Cau co action_text rong | 7 |
| Cau parse final = REJECT | 15 |
| Cau parse final = REPAIR | 15 |
| Cau parse final = ACCEPT | 0 |
| Cau material_gain = true | 0 |
| Cau di toi retrieval | 15 |
| Cau co selected_rule | 0 |
| Cau co proof | 0 |
| Cau co answer | 15 |
| Cau generation_mode = degraded_honest | 15 |
| Cau reason = no_grounded_rule_found | 15 |

## Phan B - Bang phan bo loi/chan doan chinh

| Nhom loi chinh | So cau | Cau minh hoa |
|---|---:|---|
| action_text rong | 7 | q_3, q_9, q_11, q_13, q_14, q_23, q_29 |
| parse_rejected | 15 | q_3, q_6, q_8, q_9, q_10, q_11, q_13, q_14, q_15, q_18, q_19, q_23, q_26, q_27, q_29 |
| drift sang obligation | 3 | q_4, q_9, q_18 |
| condition fallback stated_condition(...) | 17 | q_1, q_2, q_4, q_6, q_7, q_8, q_12, q_16, q_17, q_18, q_19, q_20, q_21, q_25, q_26, q_28, q_30 |
| retrieval khong grounded | 15 | q_1, q_2, q_4, q_5, q_7, q_12, q_16, q_17, q_20, q_21, q_22, q_24, q_25, q_28, q_30 |
| answer degraded | 15 | q_1, q_2, q_4, q_5, q_7, q_12, q_16, q_17, q_20, q_21, q_22, q_24, q_25, q_28, q_30 |

## Phu luc - Chi tiet 30 cau

| Cau | layer1 | layer2 | question_focus | goal.predicate | action_text_rong | debug_error | parse_final | parse_repair_final | material_gain | retrieval | selected_rule | proof | answer | generation_mode | degraded | reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| q_1 | yes | yes | obligation | obligation | no | no_grounded_rule_found | REPAIR | REPAIR | False | yes | no | no | yes | degraded_honest | yes | no_grounded_rule_found |
| q_2 | yes | yes | obligation | obligation | no | no_grounded_rule_found | REPAIR | REPAIR | False | yes | no | no | yes | degraded_honest | yes | no_grounded_rule_found |
| q_3 | yes | yes | deadline | deadline | yes | parse_rejected | REJECT | REJECT | False | no | no | no | no |  | no |  |
| q_4 | yes | yes | obligation | obligation | no | no_grounded_rule_found | REPAIR | REPAIR | False | yes | no | no | yes | degraded_honest | yes | no_grounded_rule_found |
| q_5 | yes | yes | procedure | obligation | no | no_grounded_rule_found | REPAIR | REPAIR | False | yes | no | no | yes | degraded_honest | yes | no_grounded_rule_found |
| q_6 | yes | yes | deadline | deadline | no | parse_rejected | REJECT | REJECT | False | no | no | no | no |  | no |  |
| q_7 | yes | yes | obligation | obligation | no | no_grounded_rule_found | REPAIR | REPAIR | False | yes | no | no | yes | degraded_honest | yes | no_grounded_rule_found |
| q_8 | yes | yes | applicability | applies_if | no | parse_rejected | REJECT | REJECT | False | no | no | no | no |  | no |  |
| q_9 | yes | yes | obligation | obligation | yes | parse_rejected | REJECT | REJECT | False | no | no | no | no |  | no |  |
| q_10 | yes | yes | deadline | deadline | no | parse_rejected | REJECT | REJECT | False | no | no | no | no |  | no |  |
| q_11 | yes | yes | obligation | obligation | yes | parse_rejected | REJECT | REJECT | False | no | no | no | no |  | no |  |
| q_12 | yes | yes | obligation | obligation | no | no_grounded_rule_found | REPAIR | REPAIR | False | yes | no | no | yes | degraded_honest | yes | no_grounded_rule_found |
| q_13 | yes | yes | deadline | deadline | yes | parse_rejected | REJECT | REJECT | False | no | no | no | no |  | no |  |
| q_14 | yes | yes | deadline | deadline | yes | parse_rejected | REJECT | REJECT | False | no | no | no | no |  | no |  |
| q_15 | yes | yes | legal_consequence | legal_effect | no | parse_rejected | REJECT | REJECT | False | no | no | no | no |  | no |  |
| q_16 | yes | yes | obligation | obligation | no | no_grounded_rule_found | REPAIR | REPAIR | False | yes | no | no | yes | degraded_honest | yes | no_grounded_rule_found |
| q_17 | yes | yes | obligation | obligation | no | no_grounded_rule_found | REPAIR | REPAIR | False | yes | no | no | yes | degraded_honest | yes | no_grounded_rule_found |
| q_18 | yes | yes | obligation | obligation | no | parse_rejected | REJECT | REJECT | False | no | no | no | no |  | no |  |
| q_19 | yes | yes | obligation | obligation | no | parse_rejected | REJECT | REJECT | False | no | no | no | no |  | no |  |
| q_20 | yes | yes | obligation | obligation | no | no_grounded_rule_found | REPAIR | REPAIR | False | yes | no | no | yes | degraded_honest | yes | no_grounded_rule_found |
| q_21 | yes | yes | obligation | obligation | no | no_grounded_rule_found | REPAIR | REPAIR | False | yes | no | no | yes | degraded_honest | yes | no_grounded_rule_found |
| q_22 | yes | yes | obligation | obligation | no | no_grounded_rule_found | REPAIR | REPAIR | False | yes | no | no | yes | degraded_honest | yes | no_grounded_rule_found |
| q_23 | yes | yes | deadline | deadline | yes | parse_rejected | REJECT | REJECT | False | no | no | no | no |  | no |  |
| q_24 | yes | yes | obligation | obligation | no | no_grounded_rule_found | REPAIR | REPAIR | False | yes | no | no | yes | degraded_honest | yes | no_grounded_rule_found |
| q_25 | yes | yes | obligation | obligation | no | no_grounded_rule_found | REPAIR | REPAIR | False | yes | no | no | yes | degraded_honest | yes | no_grounded_rule_found |
| q_26 | yes | yes | deadline | deadline | no | parse_rejected | REJECT | REJECT | False | no | no | no | no |  | no |  |
| q_27 | yes | yes | deadline | deadline | no | parse_rejected | REJECT | REJECT | False | no | no | no | no |  | no |  |
| q_28 | yes | yes | obligation | obligation | no | no_grounded_rule_found | REPAIR | REPAIR | False | yes | no | no | yes | degraded_honest | yes | no_grounded_rule_found |
| q_29 | yes | yes | obligation | obligation | yes | parse_rejected | REJECT | REJECT | False | no | no | no | no |  | no |  |
| q_30 | yes | yes | obligation | obligation | no | no_grounded_rule_found | REPAIR | REPAIR | False | yes | no | no | yes | degraded_honest | yes | no_grounded_rule_found |
