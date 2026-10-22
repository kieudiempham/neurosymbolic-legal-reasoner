# Norm extraction: gpt-4.1-mini vs gpt-4.1 on a random sample (30 norms)

Sample: 30 norms drawn at random (seed 7) from the KB extracted with gpt-4.1-mini (units with > 40 characters).
For each, the same article was re-extracted with gpt-4.1 (same prompt and vocabulary, one pass, no re-asking of
skipped units) and the gpt-4.1 norms of the same unit were compared.

Graded by Claude (one grader, not a human annotator), 5 binary criteria per unit, 1 point each:
M modality, S holder type correct and specific, C conditions complete and not invented, L variables linked
correctly, H action / conclusion / formula correct. A unit that should be skipped (entry into force, pure
delegation) scores 5 when skipped or harmless, 0 when a wrong norm is produced; a normative unit with no norm
scores 0.

| # | norm (mini) | mini | gpt-4.1 | note |
|---|---|---|---|---|
| 1 | 41/2024/QH15:D60.K3#5 | 4 | 5 | mini: no holder |
| 2 | 145/2020/NĐ-CP:D71.K2.b#2 | 4 | 4 | both: holder typed ca_nhan / to_chuc; 4.1 covers the whole unit |
| 3 | 45/2019/QH14:D91.K4#3 | 4 | 4 | mini: misses "quyết định, công bố mức lương tối thiểu" |
| 4 | 123/2020/NĐ-CP:D24.K2#4 | 3 | 4 | mini: invented condition, holder too narrow |
| 5 | 126/2020/NĐ-CP:D11.K1.b#1 | 4 | 4 | both miss the place of filing |
| 6 | 126/2020/NĐ-CP:D32.K4.a#1 | 3 | 5 | mini: misses the limit and the enforcement decision |
| 7 | 45/2019/QH14:D202.K2#1 | 2 | 5 | mini: vague definition on giay_to |
| 8 | 123/2020/NĐ-CP:D4.K2#1 | 4 | 4 | 4.1: an OR written as AND |
| 9 | 67/VBHN-VPQH:D88.K3.a#2 | 2 | 2 | both invert condition and conclusion |
| 10 | 168/2025/NĐ-CP:D50.K2#1 | 4 | 5 | mini: condition on the company instead of the founding shareholder |
| 11 | 123/2020/NĐ-CP:D10.K2#2 | 0 | 5 | mini: invented norm (unit only refers to Ministry guidance) |
| 12 | 126/2020/NĐ-CP:D18.K7.a#18 | 3 | 0 | 4.1: unit skipped |
| 13 | 67/VBHN-VPQH:D135.K2#1 | 4 | 3 | mini: obligation instead of permission; 4.1 misses the permission |
| 14 | 67/VBHN-VPQH:D103.K3.d#11 | 5 | 2 | 4.1: wrong head, undeclared variable |
| 15 | 123/2020/NĐ-CP:D9.K1#7 | 2 | 3 | both miss "thời điểm = chuyển giao quyền sở hữu" |
| 16 | 181/2025/NĐ-CP:D17.K3.a#5 | 3 | 3 | both miss the definition of international transport |
| 17 | 126/2020/NĐ-CP:D26.K2.a#5 | 3 | 0 | 4.1: unit skipped |
| 18 | 67/VBHN-VPQH:D115.K1.d#4 | 4 | 3 | mini: meaningless condition; 4.1: holder too general, tautology |
| 19 | 123/2020/NĐ-CP:D42.K2#1 | 1 | 1 | both meaningless |
| 20 | 145/2020/NĐ-CP:D114.K1#0 | 0 | 4 | mini: entry-into-force clause encoded as an obligation |
| 21 | 168/2025/NĐ-CP:D68.K1#1 | 4 | 4 | both miss the forgery condition; 4.1 covers the deadline |
| 22 | 123/2020/NĐ-CP:D49.K2.c#0 | 3 | 5 | mini: wrong head |
| 23 | 45/2019/QH14:D99.K3.a#4 | 4 | 5 | mini: misses the cause condition from the lead-in |
| 24 | 123/2020/NĐ-CP:D26.K4#10 | 0 | 5 | mini: prohibition not in the text |
| 25 | 168/2025/NĐ-CP:D64.K5#11 | 3 | 4 | mini: wrong head, generic types |
| 26 | 123/2020/NĐ-CP:D22a@70/2025/NĐ-CP.K1#1 | 5 | 5 | |
| 27 | 145/2020/NĐ-CP:D31.K4#5 | 5 | 4 | 4.1: no head |
| 28 | 41/2024/QH15:D102.K2.c#2 | 3 | 5 | mini: formula missing |
| 29 | 67/VBHN-VPQH:D107.K2#1 | 5 | 5 | |
| 30 | 145/2020/NĐ-CP:D54.K1#0 | 4 | 5 | mini: vague head |

| | gpt-4.1-mini | gpt-4.1 |
|---|---|---|
| mean score (of 5) | 3.17 (63%) | 3.77 (75%) |
| units fully correct (5/5) | 4 / 30 (13%) | 12 / 30 (40%) |
| units with severe errors (score ≤ 2) | 7 / 30 (23%) | 5 / 30 (17%), of which 2 skipped units |

Caveats: 30 units give wide uncertainty (about ±10 points on the mean); one grader; gpt-4.1 ran a single pass
while the mini KB had up to three re-asks for skipped units, which favours mini on coverage.
