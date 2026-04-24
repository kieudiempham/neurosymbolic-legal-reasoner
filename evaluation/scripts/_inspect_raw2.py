import json
from pathlib import Path

# Look deeper at a few raw cases
cases = ['n11', 'n13', 'n17', 'n19', 'n21']
raw_dir = Path('tests/output/raw')

for cid in cases:
    p = raw_dir / f'{cid}.json'
    data = json.loads(p.read_text(encoding='utf-8-sig'))
    dbg = data.get('debug_trace') or {}
    
    # Print all keys in debug_trace
    keys = [k for k in dbg.keys()]
    
    # Look at retrieval details
    retrieval = dbg.get('retrieval') or {}
    
    # Look at parse
    parse = dbg.get('parse') or {}
    parsed_intent = parse.get('intent', '') if isinstance(parse, dict) else ''
    
    # Look at what stages are present
    stages_present = [k for k in keys if dbg.get(k)]
    
    print(f"\n=== {cid} ===")
    print(f"debug_trace keys: {keys}")
    print(f"parse intent: {parsed_intent}")
    print(f"retrieval type: {type(retrieval)}")
    if isinstance(retrieval, dict):
        print(f"retrieval keys: {list(retrieval.keys())}")
        print(f"retrieval snippet: {str(retrieval)[:300]}")
    
    # Look at error
    print(f"debug_trace.error: {dbg.get('error')}")
    print(f"top-level error: {data.get('error')}")
