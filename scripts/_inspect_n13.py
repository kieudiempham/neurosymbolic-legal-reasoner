import json
from pathlib import Path

# Detailed inspection of n13
cid = 'n13'
out_dir = Path('tests/output/validation_5case')
p = out_dir / f'{cid}_after.json'
data = json.loads(p.read_text(encoding='utf-8-sig'))
dbg = data.get('debug_trace') or {}

print(f"=== {cid} FULL TRACE ===")
print(f"error: {dbg.get('error')}")

for bucket in ('rule_backward_gate', 'rule_backward_gate_rerun'):
    entries = dbg.get(bucket) or []
    if entries:
        print(f"\n--- {bucket} ({len(entries)} events) ---")
        for t in entries:
            if not isinstance(t, dict):
                continue
            stage = t.get('stage')
            print(f"  stage={stage}")
            if stage == 'candidate_semantic_guard_fallback_rescue':
                print(f"    admission_source={t.get('admission_source')}")
                print(f"    rescue_decision={t.get('rescue_decision')}")
                print(f"    reason={t.get('reason')}")
            elif stage == 'rule_gate':
                print(f"    rule_id={t.get('rule_id')}")
                print(f"    decision={t.get('decision')}")
                print(f"    reason={t.get('reason')}")
            elif stage == 'rule_gate_fallback_relaxation':
                print(f"    rule_id={t.get('rule_id')}")
                print(f"    decision={t.get('decision')}")
                print(f"    reason={t.get('reason')}")
            elif stage == 'post_rule_gate_survivor':
                print(f"    rule_id={t.get('rule_id')}")
                print(f"    admission_source={t.get('admission_source')}")
            elif stage == 'backward_select_entry':
                print(f"    admission_source={t.get('admission_source')}")
                print(f"    backward_plan_candidates_count={t.get('backward_plan_candidates_count')}")
                print(f"    fallback_rule_relaxation_triggered={t.get('fallback_rule_relaxation_triggered')}")
            elif stage == 'backward_gate':
                print(f"    final_decision={t.get('final_decision')}")
                print(f"    bk_relax={t.get('backward_rescue_relaxation_triggered')}")
                print(f"    rejection_reason={t.get('rejection_reason')}")
