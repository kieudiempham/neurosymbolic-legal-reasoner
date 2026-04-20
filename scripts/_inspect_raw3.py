import json
from pathlib import Path

# Look at rule_backward_gate and retrieval_result for baseline cases
cases = ['n11', 'n13', 'n17', 'n19', 'n21']
raw_dir = Path('tests/output/raw')

for cid in cases:
    p = raw_dir / f'{cid}.json'
    data = json.loads(p.read_text(encoding='utf-8-sig'))
    dbg = data.get('debug_trace') or {}
    
    print(f"\n=== {cid} ===")
    
    # retrieval_result
    rr = dbg.get('retrieval_result') or {}
    if isinstance(rr, dict):
        print(f"  retrieval_result keys: {list(rr.keys())[:10]}")
        # Try to get candidates
        cands = rr.get('candidates') or rr.get('results') or []
        print(f"  retrieval candidates count: {len(cands)}")
        if cands:
            print(f"  first candidate: {str(cands[0])[:200]}")
    
    # rule_backward_gate - list of trace events
    rbg = dbg.get('rule_backward_gate') or []
    print(f"  rule_backward_gate entries: {len(rbg)}")
    for i, t in enumerate(rbg[:3]):
        if isinstance(t, dict):
            stage = t.get('stage')
            print(f"  [{i}] stage={stage} keys={list(t.keys())[:8]}")
            if stage == 'backward_select_entry':
                print(f"      admission_source={t.get('admission_source')}")
                print(f"      rescue_triggered={t.get('rescue_triggered')}")
                print(f"      backward_plan_candidates_count={t.get('backward_plan_candidates_count')}")
            elif stage == 'backward_gate':
                print(f"      final_decision={t.get('final_decision')}")
                print(f"      rejection_reason={t.get('rejection_reason')}")
