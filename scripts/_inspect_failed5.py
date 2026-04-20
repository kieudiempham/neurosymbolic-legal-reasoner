import json
from pathlib import Path

cases = ['n13', 'n19', 'n21']
out_dir = Path('tests/output/validation_5case')

for cid in cases:
    p = out_dir / f'{cid}_after.json'
    data = json.loads(p.read_text(encoding='utf-8-sig'))
    dbg = data.get('debug_trace') or {}
    
    print(f"\n{'='*60}")
    print(f"=== {cid} ===")
    print(f"error: {dbg.get('error')}")
    print(f"selected_rule: {str(data.get('selected_rule'))[:100]}")
    
    for bucket in ('rule_backward_gate', 'rule_backward_gate_rerun'):
        entries = dbg.get(bucket) or []
        if entries:
            print(f"\n--- {bucket} ({len(entries)} events) ---")
            for t in entries:
                if not isinstance(t, dict):
                    continue
                stage = t.get('stage')
                print(f"  stage={stage}")
                if stage == 'backward_select_entry':
                    print(f"    admission_source={t.get('admission_source')}")
                    print(f"    backward_plan_candidates_count={t.get('backward_plan_candidates_count')}")
                    print(f"    rescue_triggered={t.get('rescue_triggered')}")
                    print(f"    fallback_rule_relaxation_triggered={t.get('fallback_rule_relaxation_triggered')}")
                    print(f"    rescued_backward_plan_triggered={t.get('rescued_backward_plan_triggered')}")
                elif stage == 'backward_gate':
                    print(f"    final_decision={t.get('final_decision')}")
                    print(f"    relaxed_final_decision={t.get('relaxed_final_decision')}")
                    print(f"    verification_level={t.get('verification_level')}")
                    print(f"    backward_rescue_relaxation_triggered={t.get('backward_rescue_relaxation_triggered')}")
                    print(f"    original_final_decision={t.get('original_final_decision')}")
                    print(f"    rejection_reason={t.get('rejection_reason')}")
                elif stage == 'backward_gate_rescued_relaxation':
                    print(f"    rule_id={t.get('rule_id')}")
                    print(f"    rescued_flow_active={t.get('rescued_flow_active')}")
                    print(f"    backward_rescue_relaxation_triggered={t.get('backward_rescue_relaxation_triggered')}")
                    print(f"    effective_back_decision={t.get('effective_back_decision')}")
                elif stage == 'backward_repair_promoted_for_rescued_fallback':
                    print(f"    reason={t.get('reason')}")
                elif stage == 'backward_plan_empty':
                    print(f"    reason={t.get('reason')}")
                    print(f"    repair_applied={t.get('repair_applied')}")
                    ids = t.get('top_retrieved_rule_ids') or []
                    print(f"    top_ids={ids[:2]}")
