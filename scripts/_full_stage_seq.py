import json
from pathlib import Path

# Compare full trace sequence for n11 (success) vs n21 (fail)
cases = ['n11', 'n21']
out_dir = Path('tests/output/validation_5case')

for cid in cases:
    p = out_dir / f'{cid}_after.json'
    data = json.loads(p.read_text(encoding='utf-8-sig'))
    dbg = data.get('debug_trace') or {}
    
    print(f"\n=== {cid} FULL STAGE SEQUENCE ===")
    
    for bucket in ('rule_backward_gate', 'rule_backward_gate_rerun'):
        entries = dbg.get(bucket) or []
        if entries:
            print(f"\n  [{bucket}] ({len(entries)} entries):")
            for t in entries:
                if isinstance(t, dict):
                    stage = t.get('stage')
                    extras = {}
                    if stage == 'backward_materiality_guard':
                        extras = {'result': t.get('result'), 'material_gain': t.get('material_gain'), 'reason': t.get('reason'), 'all_keys': list(t.keys())}
                    elif stage == 'backward_gate':
                        extras = {'final_decision': t.get('final_decision'), 'relaxed': t.get('relaxed_final_decision'), 'bk_relax': t.get('backward_rescue_relaxation_triggered')}
                    elif stage == 'backward_repair_promoted_for_rescued_fallback':
                        extras = {'reason': t.get('reason')}
                    print(f"      {stage} {extras}")
