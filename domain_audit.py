import json
import os
import glob

domain_paths = {
    "enterprise": {
        "runtime": "data/processed/rulebase/enterprise/runtime/rulebase.json",
        "canonical": "data/processed/rulebase/enterprise/canonical/shared_entities.json" 
    },
    "labor": {
        "runtime": "data/processed/rulebase/labor/runtime/rulebase.json",
        "canonical": "data/processed/rulebase/labor/canonical/shared_entities.json"
    },
    "tax": {
        "runtime": "data/processed/rulebase/tax/runtime/rulebase.json",
        "canonical": "data/processed/rulebase/tax/canonical/shared_entities.json"
    }
}

def analyze():
    print(f"{'Domain':<12} | {'Type':<10} | {'Rules':<5} | {'ProcKeys':<8} | {'>1Pred%':<8} | {'Generic'}")
    print("-" * 65)
    
    for domain, configs in domain_paths.items():
        for ft, rel_path in configs.items():
            path = os.path.join(os.getcwd(), rel_path)
            if not os.path.exists(path):
                folder = os.path.dirname(path)
                files = glob.glob(os.path.join(folder, "*.json"))
                if files: path = files[0]
                else:
                    print(f"{domain:<12} | {ft:<10} | {'NF':<5} | {'-':<8} | {'-':<8} | {'-'}")
                    continue
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Flexible handling of list/dict
            rules = []
            if isinstance(data, list):
                rules = data
            elif isinstance(data, dict):
                # Try common keys or values if it's a map
                candidates = [v for v in data.values() if isinstance(v, list)]
                if candidates:
                    # Pick the longest list
                    rules = max(candidates, key=len)
                else:
                    # Maybe it's a dict of dicts (id -> rule)
                    rules = [v for v in data.values() if isinstance(v, dict)]
            
            # Ensure each element is a dict
            rules = [r for r in rules if isinstance(r, dict)]
            total_rules = len(rules)
            
            procedure_keys = [r.get('procedure_key') for r in rules if r.get('procedure_key')]
            unique_proc_keys = set(procedure_keys)
            num_proc_keys = len(unique_proc_keys)
            
            proc_map = {}
            for r in rules:
                pk = r.get('procedure_key')
                if pk:
                    if pk not in proc_map: proc_map[pk] = set()
                    h = r.get('head')
                    if isinstance(h, dict):
                        pred = h.get('predicate')
                        if pred: proc_map[pk].add(pred)
            
            keys_gt_1_pred = [pk for pk, preds in proc_map.items() if len(preds) > 1]
            pct_gt_1 = (len(keys_gt_1_pred) / num_proc_keys * 100) if num_proc_keys > 0 else 0
            
            generic_preds = {"thong_bao", "dang_ky", "gui_ho_so", "cap_nhat"}
            generic_head_count = 0
            for r in rules:
                h = r.get('head')
                if isinstance(h, dict):
                    h_pred = h.get('predicate')
                    if h_pred in generic_preds:
                        generic_head_count += 1
            
            print(f"{domain:<12} | {ft:<10} | {total_rules:<5} | {num_proc_keys:<8} | {pct_gt_1:<8.1f} | {generic_head_count}")

            fields = ['source_doc', 'source_ref_full', 'source_unit_id', 'surface_text']
            missing_counts = {f: 0 for f in fields}
            for r in rules:
                prov = r.get('provenance', {})
                if not isinstance(prov, dict): prov = {}
                for f in fields:
                    if not prov.get(f):
                        missing_counts[f] += 1
            print(f"  Missing: " + " ".join([f"{f}:{missing_counts[f]}" for f in fields]))

analyze()
