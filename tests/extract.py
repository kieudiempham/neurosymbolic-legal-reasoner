import json
with open('tests/output/case_tax_delay_after_layer1_prompt_patch.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
rule_id = data.get('selected_rule', {}).get('rule_id')
verdicts = data.get('debug_trace', {}).get('verification', {}).get('candidate_verdicts', {})
tier = verdicts.get(rule_id, {}).get('semantic_family_match_tier', 'Not found')
reorder_data = data.get('debug_trace', {}).get('retrieval', {}).get('semantic_reorder')
if reorder_data:
    reorder = f"original_ids: {reorder_data.get('original_ids')}, reordered_ids: {reorder_data.get('reordered_ids')}"
else:
    reorder = 'not present'
relax = data.get('debug_trace', {}).get('verification', {}).get('forward_trace', {}).get('forward_soft_match_relaxation_triggered', 'Not found')
print(f'selected rule id: {rule_id}')
print(f'selected semantic tier: {tier}')
print(f'semantic reorder evidence: {reorder}')
print(f'forward relaxation flag: {relax}')
