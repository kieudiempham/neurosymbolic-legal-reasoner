import json
from pathlib import Path

# Full detail of n13 rule_gate events
cid = 'n13'
out_dir = Path('tests/output/validation_5case')
p = out_dir / f'{cid}_after.json'
data = json.loads(p.read_text(encoding='utf-8-sig'))
dbg = data.get('debug_trace') or {}

for bucket in ('rule_backward_gate',):
    entries = dbg.get(bucket) or []
    for t in entries:
        if isinstance(t, dict) and t.get('stage') == 'rule_gate':
            print(f"\n--- rule_gate ---")
            for k, v in t.items():
                print(f"  {k}: {str(v)[:120]}")
