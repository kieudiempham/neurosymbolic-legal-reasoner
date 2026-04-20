import json
from pathlib import Path

results = json.loads(Path('tests/output/30_case_audit_results.json').read_text(encoding='utf-8-sig'))

failed = []
for r in results:
    err = r.get('error_stage_final', '')
    sr = r.get('selected_rule_id')
    proof = r.get('proof_present', False)
    if sr is None or not proof:
        rule_flag = 'Y' if sr else 'N'
        proof_flag = 'Y' if proof else 'N'
        failed.append({
            'id': r['id'],
            'question': r['question'][:80],
            'domain': r.get('domain_hint', ''),
            'intent': r.get('intent_hint', ''),
            'error': err,
            'selected_rule': sr,
            'proof': proof,
            'final_status': r.get('final_status', ''),
        })
        print("%s [%s/%s] err=%s rule=%s proof=%s" % (
            r['id'], r.get('domain_hint',''), r.get('intent_hint',''),
            err, rule_flag, proof_flag
        ))
        print("  Q: %s" % r['question'][:100])
        print()

print("Total failed: %d" % len(failed))
