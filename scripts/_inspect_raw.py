import json
from pathlib import Path

cases = ['n11', 'n13', 'n17', 'n19', 'n21', 'n17', 'n25', 'n14', 'n09', 'n20', 'n22', 'n26']
raw_dir = Path('tests/output/raw')

for cid in cases:
    p = raw_dir / f'{cid}.json'
    if not p.exists():
        print(f'{cid}: FILE NOT FOUND')
        continue
    data = json.loads(p.read_text(encoding='utf-8-sig'))
    dbg = data.get('debug_trace') or {}
    
    # Get admission_source from rule_backward_gate traces
    admission_sources = set()
    rescue_triggers = set()
    errors = set()
    fallback_relaxation = False
    backward_plan_rescue = False
    
    for bucket in ('rule_backward_gate', 'rule_backward_gate_rerun'):
        for t in (dbg.get(bucket) or []):
            if isinstance(t, dict):
                as_ = t.get('admission_source')
                if as_:
                    admission_sources.add(as_)
                rt = t.get('rescue_triggered')
                if rt:
                    rescue_triggers.add(str(rt))
                if t.get('fallback_rule_relaxation_triggered'):
                    fallback_relaxation = True
                if t.get('rescued_backward_plan_triggered'):
                    backward_plan_rescue = True
    
    err = dbg.get('error', '')
    sr = data.get('selected_rule')
    proof = data.get('proof')
    
    retrieval = dbg.get('retrieval') or {}
    cands = retrieval.get('candidates_count', 0) if isinstance(retrieval, dict) else 0
    
    print(f"{cid}: err={err} rule={'Y' if sr else 'N'} proof={'Y' if proof else 'N'} "
          f"cands={cands} admission={admission_sources} "
          f"fallback_relax={fallback_relaxation} bk_rescue={backward_plan_rescue}")
