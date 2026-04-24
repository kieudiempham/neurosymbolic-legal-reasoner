import json
from pathlib import Path

# Inspect the top_retrieved_rule_ids in baseline to verify retrieval was happening
cases = ['n11', 'n13', 'n17', 'n19', 'n21']
raw_dir = Path('tests/output/raw')

for cid in cases:
    p = raw_dir / f'{cid}.json'
    data = json.loads(p.read_text(encoding='utf-8-sig'))
    dbg = data.get('debug_trace') or {}
    
    rbg = dbg.get('rule_backward_gate') or []
    for t in rbg:
        if isinstance(t, dict) and t.get('stage') == 'backward_plan_empty':
            top_ids = t.get('top_retrieved_rule_ids') or []
            goal = t.get('goal') or {}
            print(f"{cid}: goal={str(goal)[:100]}")
            print(f"     top_retrieved: {top_ids[:3]}")
            print(f"     repair_applied: {t.get('repair_applied')}")
            print()
