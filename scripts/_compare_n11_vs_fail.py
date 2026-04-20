import json
from pathlib import Path

# Compare n11 trace (success) vs n19/n21 trace (fail) to find the difference
cases = ['n11', 'n19', 'n21']
out_dir = Path('tests/output/validation_5case')

for cid in cases:
    p = out_dir / f'{cid}_after.json'
    data = json.loads(p.read_text(encoding='utf-8-sig'))
    dbg = data.get('debug_trace') or {}
    
    print(f"\n=== {cid} backward_select_entry + backward_gate ===")
    
    for bucket in ('rule_backward_gate', 'rule_backward_gate_rerun'):
        entries = dbg.get(bucket) or []
        for t in entries:
            if not isinstance(t, dict):
                continue
            stage = t.get('stage')
            if stage == 'backward_select_entry':
                print(f"  [{bucket}] backward_select_entry:")
                print(f"    admission_source = {t.get('admission_source')}")
                print(f"    fallback_rule_relaxation_triggered = {t.get('fallback_rule_relaxation_triggered')}")
                print(f"    rescued_backward_plan_triggered = {t.get('rescued_backward_plan_triggered')}")
                print(f"    semantic_guard_fallback_rescued = {t.get('semantic_guard_fallback_rescued')}")
                print(f"    backward_plan_candidates_count = {t.get('backward_plan_candidates_count')}")
            elif stage == 'backward_gate':
                print(f"  [{bucket}] backward_gate:")
                print(f"    backward_rescue_relaxation_triggered = {t.get('backward_rescue_relaxation_triggered')}")
                print(f"    original_final_decision = {t.get('original_final_decision')}")
                print(f"    relaxed_final_decision = {t.get('relaxed_final_decision')}")
                print(f"    ALL keys: {list(t.keys())}")
        if entries:
            break  # just first bucket
