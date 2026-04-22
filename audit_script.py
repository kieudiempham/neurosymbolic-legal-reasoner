import json
import os
import glob
from collections import Counter, defaultdict

files_json = glob.glob("data/processed/rulebase/*/runtime/rulebase_reasoning_core.json")
files_jsonl = glob.glob("data/processed/rulebase/*/canonical/*.jsonl")

all_rules = []

def get_deep(d, path):
    keys = path.split(".")
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return None
    return d

for fpath in files_json:
    domain = fpath.split(os.sep)[-3]
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            rules = data.get("rules_reasoning_core", [])
            for r in rules:
                r["__domain"] = domain
                r["__file_source"] = fpath
                all_rules.append(r)
    except Exception as e:
        print(f"Error reading {fpath}: {e}")

for fpath in files_jsonl:
    domain = fpath.split(os.sep)[-3]
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                r = json.loads(line)
                r["__domain"] = domain
                r["__file_source"] = fpath
                all_rules.append(r)
    except Exception as e:
        print(f"Error reading {fpath}: {e}")

print(f"Total rules loaded: {len(all_rules)}")

proc_keys = ["metadata.provenance.source_unit_id", "metadata.provenance.source_ref_full", "metadata.provenance.source_ref", "metadata.provenance.source_article", "metadata.provenance.generated_from_frame_id"]

def resolve_proc_key(r):
    for pk in proc_keys:
        val = get_deep(r, pk)
        if val and str(val).lower() not in ["", "null", "unknown", "none"]:
            return str(val)
    return None

pred_by_proc = defaultdict(set)
for r in all_rules:
    pk = resolve_proc_key(r)
    head_pred = get_deep(r, "head.predicate")
    if pk and head_pred:
        pred_by_proc[pk].add(head_pred)

fragmented = {k: v for k, v in pred_by_proc.items() if len(v) > 1}
sorted_fragmented = sorted(fragmented.items(), key=lambda x: len(x[1]), reverse=True)

print("\nTop 20 Most Fragmented Keys:")
for k, preds in sorted_fragmented[:20]:
    print(f"Key: {k} | Count: {len(preds)} | Preds: {list(preds)[:5]}...")

conc_1 = sum(1 for v in pred_by_proc.values() if len(v) == 1)
total_pk = len(pred_by_proc)
if total_pk > 0:
    print(f"\nConcentration: {conc_1}/{total_pk} ({conc_1/total_pk:.2%} with exactly 1 predicate)")

req_fields = ["metadata.domain", "metadata.layer", "metadata.rulebase_id", "metadata.provenance.source_doc", "metadata.provenance.source_ref_full", "metadata.provenance.source_unit_id", "metadata.provenance.surface_text"]
missing_counts = defaultdict(lambda: defaultdict(int))
placeholder_counts = defaultdict(lambda: defaultdict(int))
placeholders = {"", "null", "unknown", "unknown_subject_x", "none"}

for r in all_rules:
    dom = r["__domain"]
    for field in req_fields:
        val = get_deep(r, field)
        if val is None:
            missing_counts["overall"][field] += 1
            missing_counts[dom][field] += 1
        elif str(val).lower() in placeholders:
            placeholder_counts["overall"][field] += 1
            placeholder_counts[dom][field] += 1

print("\nMetadata Missingness / Placeholders (Overall):")
total_rules = len(all_rules)
if total_rules > 0:
    for field in req_fields:
        m = missing_counts["overall"][field]
        p = placeholder_counts["overall"][field]
        print(f"{field}: Missing {m} ({m/total_rules:.2%}), Placeholder {p} ({p/total_rules:.2%})")

def get_subtype(r):
    fid = get_deep(r, "metadata.provenance.generated_from_frame_id") or ""
    subtype_f = fid.split("_H")[0] if "_H" in fid else fid
    hp = get_deep(r, "head.predicate") or ""
    parts = hp.split("_")
    subtype_p = "_".join(parts[:2]) if len(parts) > 1 else hp
    return f"{subtype_f}:{subtype_p}"

subtypes_by_proc = defaultdict(set)
for r in all_rules:
    pk = resolve_proc_key(r)
    if pk:
        subtypes_by_proc[pk].add(get_subtype(r))

stable_sub = sum(1 for v in subtypes_by_proc.values() if len(v) == 1)
total_sub_pk = len(subtypes_by_proc)
if total_sub_pk > 0:
    print(f"\nSubtype Stability: {stable_sub}/{total_sub_pk} ({stable_sub/total_sub_pk:.2%})")

target_id = "RULE_ND168_D30_K2_B_E000697_H1A1CEF5CFB94__90169f111c1548"
target_rule = next((r for r in all_rules if r.get("rule_id") == target_id), None)
if target_rule:
    u_id = get_deep(target_rule, "metadata.provenance.source_unit_id")
    r_full = get_deep(target_rule, "metadata.provenance.source_ref_full")
    print(f"\nTarget Rule {target_id} found. Siblings (unit={u_id}, ref={r_full}):")
    sib = [r for r in all_rules if (get_deep(r, "metadata.provenance.source_unit_id") == u_id or get_deep(r, "metadata.provenance.source_ref_full") == r_full) and r.get("rule_id")!=target_id]
    for s in sib[:10]:
        print(f"  ID: {s.get('rule_id')} | Pred: {get_deep(s, 'head.predicate')} | Logic: {s.get('logic_form')}")
else:
    print(f"\nTarget {target_id} not found.")
