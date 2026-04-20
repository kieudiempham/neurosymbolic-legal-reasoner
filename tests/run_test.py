import requests
import json
import os

url = 'http://127.0.0.1:8000/ask'
payload = {
    'question': 'Kể từ khi có thay đổi nội dung đăng ký doanh nghiệp, công ty phải gửi thông báo trong thời hạn mấy ngày?',
    'session_id': 'sess_acceptance_option3_final',
    'domain': 'tax',
    'user_facts': []
}

try:
    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    
    os.makedirs('tests/output', exist_ok=True)
    with open('tests/output/case_tax_delay_after_layer1_prompt_patch.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print('needs_clarification:', data.get('needs_clarification'))
    print('evaluation_log.final_status:', data.get('evaluation_log', {}).get('final_status'))
    
    debug_trace = data.get('debug_trace', {})
    print('debug_trace.domain_hint_ignored:', debug_trace.get('domain_hint_ignored'))
    
    rule_retrieval = debug_trace.get('rule_retrieval', {})
    print('debug_trace.rule_retrieval.domain_hint_ignored:', rule_retrieval.get('domain_hint_ignored'))
    
    top_rules = rule_retrieval.get('top', [])
    if top_rules:
        top1 = top_rules[0]
        rule_id = top1.get('rule_id', '')
        print('top1 rule id:', rule_id)
        print('top1 source_doc:', top1.get('source_doc'))
        print('top1 is D36_K5:', rule_id.startswith('D36_K5'))
    
    breakdown = rule_retrieval.get('final_top10_score_breakdown', [])
    print('\nScore Breakdown (First 10):')
    for row in breakdown[:10]:
        rid = row.get('rule_id')
        score = row.get('score_total')
        comp = row.get('score_components', {})
        pos_boost = comp.get('enterprise_registration_positive_boost')
        tax_pen = comp.get('tax_attractor_penalty')
        sem_mis = comp.get('semantic_family_mismatch_penalty')
        print(f'Rule: {rid}, Total: {score}, PosBoost: {pos_boost}, TaxPen: {tax_pen}, SemMis: {sem_mis}')
    
    print('\nRows where tax_attractor_penalty != 0:')
    for row in breakdown:
        comp = row.get('score_components', {})
        tax_pen = comp.get('tax_attractor_penalty', 0)
        if tax_pen != 0:
            rid = row.get('rule_id')
            score = row.get('score_total')
            print(f'Rule: {rid}, Total: {score}, TaxPen: {tax_pen}')

except Exception as e:
    import traceback
    print(f'Error: {e}')
    traceback.print_exc()
