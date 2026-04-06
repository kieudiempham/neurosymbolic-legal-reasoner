#!/usr/bin/env python
"""Re-audit enterprise multi-rule pipeline: verify input corpus and semantic quality."""

import json
from pathlib import Path
from collections import Counter

# ==============================================================================
# A. VERIFY INPUT CORPUS
# ==============================================================================
print("=" * 80)
print("A. VERIFY INPUT CORPUS & DATA INTEGRITY")
print("=" * 80)

doc_dir = Path('data/raw/legal_corpus/doc')
print(f"\nDocument files in {doc_dir}:")
for f in sorted(doc_dir.glob('*.doc')):
    size = f.stat().st_size
    print(f"  {f.name}: {size} bytes")

# Check canonical artifacts
canon_path = Path('data/processed/rulebase/enterprise/canonical_rules.jsonl')
print(f"\nCanonical rules artifact exists: {canon_path.exists()}")

if canon_path.exists():
    lines = [l for l in canon_path.read_text(encoding='utf-8').splitlines() if l.strip()]
    print(f"  Total lines (rules): {len(lines)}")
    
    if lines:
        obj = json.loads(lines[0])
        print(f"\n  Sample rule 1:")
        print(f"    surface_text: {obj.get('surface_text', 'N/A')[:100]}")
        print(f"    source_doc: {obj.get('source_doc')}")
        print(f"    rule_id: {obj.get('rule_id')}")
        print(f"    logic_form: {obj.get('logic_form')}")
        
        # Sample a middle rule
        if len(lines) > 500:
            obj = json.loads(lines[500])
            print(f"\n  Sample rule 500:")
            print(f"    surface_text: {obj.get('surface_text', 'N/A')[:100]}")
            print(f"    logic_form: {obj.get('logic_form')}")
        
        obj = json.loads(lines[-1])
        print(f"\n  Sample rule (last):")
        print(f"    surface_text: {obj.get('surface_text', 'N/A')[:100]}")
        print(f"    logic_form: {obj.get('logic_form')}")

# Check if content is dummy or real
dummy_indicators = ["dummy", "test", "fixture", "sample", "example"]
real_content_found = False
total_rules = len(lines) if canon_path.exists() else 0

if total_rules > 10:
    real_content_found = True
    for i in [0, len(lines)//2, -1]:
        try:
            obj = json.loads(lines[i])
            text = obj.get('surface_text', '').lower()
            if any(ind in text for ind in dummy_indicators):
                real_content_found = False
                break
        except:
            pass

print(f"\nDummy content detected: {not real_content_found}")
print(f"Real corpus used: {real_content_found and total_rules > 100}")

# ==============================================================================
# B. AUDIT SEMANTIC DIVERSITY
# ==============================================================================
print("\n" + "=" * 80)
print("B. AUDIT SEMANTIC DIVERSITY FROM ARTIFACTS")
print("=" * 80)

paths_to_check = {
    'canonical_rules.jsonl': Path('data/processed/rulebase/enterprise/canonical_rules.jsonl'),
    'enterprise_core.jsonl': Path('data/processed/rulebase/enterprise/canonical/enterprise_core.jsonl'),
    'runtime_core': Path('data/processed/rulebase/enterprise/runtime/rulebase_reasoning_core.json'),
}

semantic_data = {}

for label, path in paths_to_check.items():
    if not path.exists():
        print(f"\n{label}: NOT FOUND")
        continue
    
    print(f"\n{label}:")
    rules = []
    
    if 'jsonl' in label:
        rules = [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
    else:
        pkg = json.loads(path.read_text(encoding='utf-8'))
        rules = pkg.get('rules_reasoning_core', [])
    
    print(f"  Total rules: {len(rules)}")
    
    logic_forms = Counter(r.get('logic_form', 'unknown') for r in rules)
    print(f"  Logic forms distribution: {dict(logic_forms)}")
    print(f"  Unique logic forms: {len(logic_forms)}")
    
    semantic_data[label] = {'count': len(rules), 'forms': dict(logic_forms)}

# Compare with legacy
legacy_path = Path('data/processed/rulebase/doanhnghiep/rulebase_logic.json')
if legacy_path.exists():
    legacy = json.loads(legacy_path.read_text(encoding='utf-8'))
    legacy_rules = legacy.get('rules', [])
    legacy_forms = Counter(r.get('logic_form', 'unknown') for r in legacy_rules)
    print(f"\nLEGACY enterprise (rulebase_logic.json):")
    print(f"  Total rules: {len(legacy_rules)}")
    print(f"  Logic forms: {dict(legacy_forms)}")
    semantic_data['legacy'] = {'count': len(legacy_rules), 'forms': dict(legacy_forms)}

# ==============================================================================
# C. SAMPLE AUDIT - CANONICAL
# ==============================================================================
print("\n" + "=" * 80)
print("C. SAMPLE AUDIT - CANONICAL RULES (first 20)")
print("=" * 80)

if canon_path.exists():
    lines = [l for l in canon_path.read_text(encoding='utf-8').splitlines() if l.strip()]
    samples = [json.loads(lines[i]) for i in range(min(20, len(lines)))]
    
    print("\nQuality indicators across first 20 canonical rules:")
    good_head = 0
    has_body = 0
    has_provenance = 0
    unique_sigs = set()
    
    for i, rule in enumerate(samples, 1):
        head = rule.get('canonical_head', {})
        pred = head.get('predicate', '')
        body = rule.get('canonical_body', [])
        
        if pred and len(pred) > 2:
            good_head += 1
        if body and len(body) > 0:
            has_body += 1
        
        prov = rule.get('derived_from_rule_ids') and rule.get('derived_from_docs')
        if prov:
            has_provenance += 1
        
        sig = (rule.get('logic_form'), pred, len(body))
        unique_sigs.add(sig)
        
        if i <= 5:
            print(f"\n  Rule {i}: {rule.get('rule_id')}")
            print(f"    logic_form: {rule.get('logic_form')}")
            print(f"    head_predicate: {pred}")
            print(f"    body_len: {len(body)}")
            print(f"    surface: {rule.get('surface_text', 'N/A')[:80]}")
    
    print(f"\nSummary of first 20:")
    print(f"  Good head predicates: {good_head}/20")
    print(f"  With body: {has_body}/20")
    print(f"  With derivation provenance: {has_provenance}/20")
    print(f"  Unique signatures: {len(unique_sigs)}/20 (duplicates: {20 - len(unique_sigs)})")

# ==============================================================================
# D. SAMPLE AUDIT - RUNTIME CORE
# ==============================================================================
print("\n" + "=" * 80)
print("D. SAMPLE AUDIT - RUNTIME CORE RULES (first 20)")
print("=" * 80)

runtime_path = Path('data/processed/rulebase/enterprise/runtime/rulebase_reasoning_core.json')
if runtime_path.exists():
    pkg = json.loads(runtime_path.read_text(encoding='utf-8'))
    core_rules = pkg.get('rules_reasoning_core', [])[:20]
    
    print(f"\nQuality indicators across first 20 runtime core rules:")
    good_head = 0
    has_body = 0
    has_provenance = 0
    merged_variants = 0
    unique_sigs = set()
    
    for i, rule in enumerate(core_rules, 1):
        head = rule.get('head', {})
        pred = head.get('predicate', '')
        body = rule.get('body', [])
        
        if pred and len(pred) > 2:
            good_head += 1
        if body and len(body) > 0:
            has_body += 1
        
        meta = rule.get('metadata', {})
        prov = meta.get('provenance', {})
        if prov.get('derived_from_rule_ids') or prov.get('source_ref'):
            has_provenance += 1
        
        if prov.get('merged_variants', 0) > 0:
            merged_variants += 1
        
        sig = (rule.get('logic_form'), pred, len(body))
        unique_sigs.add(sig)
        
        if i <= 5:
            print(f"\n  Rule {i}: {rule.get('rule_id')}")
            print(f"    logic_form: {rule.get('logic_form')}")
            print(f"    head_predicate: {pred}")
            print(f"    body_len: {len(body)}")
            print(f"    merged_variants: {prov.get('merged_variants', 0)}")
    
    print(f"\nSummary of first 20:")
    print(f"  Good head predicates: {good_head}/20")
    print(f"  With body: {has_body}/20")
    print(f"  With provenance: {has_provenance}/20")
    print(f"  With merged variants (dedup evidence): {merged_variants}/20")
    print(f"  Unique signatures: {len(unique_sigs)}/20")

# ==============================================================================
# E. PROVENANCE LINEAGE CHECK
# ==============================================================================
print("\n" + "=" * 80)
print("E. PROVENANCE LINEAGE VERIFICATION")
print("=" * 80)

if canon_path.exists():
    lines = [l for l in canon_path.read_text(encoding='utf-8').splitlines() if l.strip()]
    sample_rules = [json.loads(lines[i]) for i in [0, len(lines)//2, len(lines)-1]]
    
    print("\nDerived provenance fields check (canonical layer):")
    for i, rule in enumerate(sample_rules):
        print(f"\n  Sample rule {i+1}: {rule.get('rule_id')}")
        print(f"    derived_from_rule_ids: {rule.get('derived_from_rule_ids')}")
        print(f"    derived_from_docs: {rule.get('derived_from_docs')}")
        print(f"    source_domains: {rule.get('source_domains')}")
        print(f"    source_ref: {rule.get('source_ref')[:50] if rule.get('source_ref') else None}")

if runtime_path.exists():
    pkg = json.loads(runtime_path.read_text(encoding='utf-8'))
    core_rules = pkg.get('rules_reasoning_core', [])
    sample_rules = [core_rules[i] for i in [0, len(core_rules)//2, len(core_rules)-1] if i < len(core_rules)]
    
    print("\nDerived provenance fields check (runtime core):")
    for i, rule in enumerate(sample_rules):
        prov = rule.get('metadata', {}).get('provenance', {})
        print(f"\n  Sample rule {i+1}: {rule.get('rule_id')}")
        print(f"    derived_from_rule_ids: {prov.get('derived_from_rule_ids')}")
        print(f"    derived_from_docs: {prov.get('derived_from_docs')}")
        print(f"    source_domains: {prov.get('source_domains')}")
        print(f"    rule_ids (multiplicity): {prov.get('rule_ids')}")

# ==============================================================================
# F. RUNTIME FILTER ANALYSIS
# ==============================================================================
print("\n" + "=" * 80)
print("F. RUNTIME FILTER / DEDUP ANALYSIS")
print("=" * 80)

if runtime_path.exists():
    pkg = json.loads(runtime_path.read_text(encoding='utf-8'))
    report = pkg.get('report', {})
    
    print(f"\nFilter report from package:")
    print(f"  Total canonical: {report.get('total_rules')}")
    print(f"  Exportable clean: {report.get('exportable_clean_rules')}")
    print(f"  Reasoning core (after dedup): {pkg['core_rule_count']}")
    print(f"  Duplicate reduction: {report.get('duplicate_reduction_count')}")
    print(f"  Excluded from core: {len(pkg.get('excluded_from_core', []))}")
    print(f"  Traceability only: {len(pkg.get('traceability_only', []))}")
    
    core_forms = report.get('core_by_logic_form', {})
    print(f"  Core by logic form: {core_forms}")
    
    exclusion_reasons = report.get('exclusion_reason_histogram', {})
    print(f"  Exclusion reasons: {exclusion_reasons}")

# ==============================================================================
# G. LEGACY COMPARISON
# ==============================================================================
print("\n" + "=" * 80)
print("G. LEGACY vs REPAIRED-NEW COMPARISON")
print("=" * 80)

legacy_path = Path('data/processed/rulebase/doanhnghiep/rulebase_logic.json')
legacy_runtime_path = Path('data/processed/rulebase/doanhnghiep/rulebase_reasoning_core.json')

if legacy_path.exists():
    legacy_logic = json.loads(legacy_path.read_text(encoding='utf-8'))
    legacy_rules = legacy_logic.get('rules', [])
    legacy_predicates = set(r.get('head', {}).get('predicate', 'unknown') for r in legacy_rules if r.get('head'))
    
    print(f"\nLEGACY ENTERPRISE:")
    print(f"  Rules in rulebase_logic: {len(legacy_rules)}")
    print(f"  Unique predicates: {len(legacy_predicates)}")
    
    if legacy_runtime_path.exists():
        legacy_runtime = json.loads(legacy_runtime_path.read_text(encoding='utf-8'))
        core = legacy_runtime.get('rules_reasoning_core', [])
        print(f"  Runtime core rules: {len(core)}")

print(f"\nREPAIRED-NEW ENTERPRISE:")
if canon_path.exists():
    lines = [l for l in canon_path.read_text(encoding='utf-8').splitlines() if l.strip()]
    new_rules = [json.loads(l) for l in lines]
    new_predicates = set(r.get('canonical_head', {}).get('predicate', 'unknown') for r in new_rules if r.get('canonical_head'))
    
    print(f"  Rules in canonical: {len(new_rules)}")
    print(f"  Unique predicates: {len(new_predicates)}")
    
    if runtime_path.exists():
        pkg = json.loads(runtime_path.read_text(encoding='utf-8'))
        print(f"  Runtime core rules: {pkg['core_rule_count']}")
        print(f"  Dedup reduction: {pkg.get('report', {}).get('duplicate_reduction_count')}")

print("\n" + "=" * 80)
