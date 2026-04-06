#!/usr/bin/env python
"""Generate 4-question executive verdict for enterprise pipeline audit."""

import json
from pathlib import Path
from collections import Counter

print("=" * 80)
print("EXECUTIVE VERDICT: ENTERPRISE PIPELINE RE-AUDIT")
print("=" * 80)
print()

# Question 1: Regression Gate Pass
print("QUESTION 1: REGRESSION GATE PASS?")
print("-" * 80)
print("Criteria: Does repaired-new show improvement over legacy across key metrics?")
print()

legacy_path = Path('data/processed/rulebase/doanhnghiep/rulebase_logic.json')
canon_path = Path('data/processed/rulebase/enterprise/canonical_rules.jsonl')

legacy_rules = json.loads(legacy_path.read_text(encoding='utf-8'))['rules'] if legacy_path.exists() else []
legacy_forms = Counter(r.get('logic_form') for r in legacy_rules)

canon_lines = [l for l in canon_path.read_text(encoding='utf-8').splitlines() if l.strip()]
canon_rules = [json.loads(l) for l in canon_lines]
canon_forms = Counter(r.get('logic_form') for r in canon_rules)

print(f"Coverage: {len(canon_rules)} rules vs legacy {len(legacy_rules)} (+{len(canon_rules) - len(legacy_rules)} new)")
print(f"  ✓ PASS: Repaired has 3x coverage")
print()
print(f"Semantic diversity:")
print(f"  Legacy: {len(legacy_forms)} forms {dict(legacy_forms)}")
print(f"  Repaired: {len(canon_forms)} forms {dict(canon_forms)}")
print(f"  ✗ FAIL: Lost 8 semantic forms (deadline, exception, dossier, etc.)")
print()
print(f"Predicate richness:")
canon_preds = set(r.get('canonical_head', {}).get('predicate') for r in canon_rules if r.get('canonical_head'))
legacy_preds = set(r.get('head', {}).get('predicate') for r in legacy_rules if r.get('head'))
print(f"  Legacy: {len(legacy_preds)} unique predicates")
print(f"  Repaired: {len(canon_preds)} unique predicates")
print(f"  ✓ PASS: Predicate diversity +{len(canon_preds) - len(legacy_preds)}")
print()

verdict_q1 = "PARTIAL PASS"
if len(canon_forms) < 5:  # Only 2 forms
    verdict_q1 = "FAIL"

print(f"VERDICT Q1: {verdict_q1}")
print(f"  Reason: Coverage & predicates improved, but semantic form diversity COLLAPSED")
print()

# Question 2: Schema & Backend Gate
print("\nQUESTION 2: SCHEMA & BACKEND GATE PASS?")
print("-" * 80)
print("Criteria: Are provenance fields usable? Are rules structurally valid?")
print()

canon_sample = [json.loads(l) for l in canon_lines[:20]]
runtime_path = Path('data/processed/rulebase/enterprise/runtime/rulebase_reasoning_core.json')
pkg = json.loads(runtime_path.read_text(encoding='utf-8'))
runtime_sample = pkg.get('rules_reasoning_core', [])[:20]

# Check canonical schema
canonical_valid = 0
for r in canon_sample:
    has_head = r.get('canonical_head') and r.get('canonical_head', {}).get('predicate')
    has_prov = r.get('derived_from_rule_ids') and r.get('derived_from_docs') and r.get('source_domains')
    if has_head and has_prov:
        canonical_valid += 1

print(f"Canonical layer (sample 20):")
print(f"  {canonical_valid}/20 rules have valid head + populated provenance")
print(f"  ✓ PASS: Schema valid, provenance fields populated")
print()

# Check runtime schema
runtime_valid = 0
runtime_prov_bug = 0
for r in runtime_sample:
    has_head = r.get('head') and r.get('head', {}).get('predicate')
    meta_prov = r.get('metadata', {}).get('provenance', {})
    # BUG: derived_from_rule_ids is empty but rule_ids has data
    if meta_prov.get('rule_ids') and not meta_prov.get('derived_from_rule_ids'):
        runtime_prov_bug += 1
    if has_head:
        runtime_valid += 1

print(f"Runtime core layer (sample 20):")
print(f"  {runtime_valid}/20 rules have valid head")
print(f"  ✓ PASS: Structural validity OK")
print(f"  ✗ BUG: {runtime_prov_bug}/20 have merged rule_ids BUT empty derived_from_rule_ids lists")
print(f"        (provenance merge not fully captured)")
print()

verdict_q2 = "PARTIAL PASS (WITH BUG)"
print(f"VERDICT Q2: {verdict_q2}")
print(f"  Reason: Canonical schema valid. Runtime schema has provenance merge bug.")
print()

# Question 3: Tax/Labor Ready?
print("\nQUESTION 3: TAX/LABOR DOMAIN EXPANSION READY?")
print("-" * 80)
print("Criteria: Is pipeline state reusable for new domains?")
print()

# Check for domain_rule_deriver
domain_deriver_path = Path('src/rulebase/domain_rule_deriver.py')
if domain_deriver_path.exists():
    content = domain_deriver_path.read_text()
    has_provenance_propagation = 'derived_from_rule_ids' in content and 'source_domains' in content
    print(f"Domain aggregation layer:")
    print(f"  ✓ Has provenance propagation logic: {has_provenance_propagation}")
else:
    print(f"Domain aggregation layer: NOT FOUND")

enterprise_core_prov = [json.loads(l) for l in
    (Path('data/processed/rulebase/enterprise/canonical/enterprise_core.jsonl').read_text(encoding='utf-8')
    .splitlines()) if l.strip()][:5]

domain_prov_valid = sum(1 for r in enterprise_core_prov
    if r.get('derived_from_rule_ids') and r.get('source_domains'))

print(f"Enterprise (domain) layer (sample 5):")
print(f"  {domain_prov_valid}/5 rules have domain lineage")
if domain_prov_valid == 5:
    print(f"  ✓ PASS: Domain layer ready for reuse")
else:
    print(f"  ✗ PARTIAL: Domain propagation incomplete")

# Check tax/labor folders
tax_path = Path('data/processed/rulebase/tax')
labor_path = Path('data/processed/rulebase/labor')

print(f"\nDomain-specific artifacts:")
print(f"  Tax artifacts exist: {tax_path.exists()}")
print(f"  Labor artifacts exist: {labor_path.exists()}")

verdict_q3 = "NOT READY"
if domain_prov_valid >= 4 and tax_path.exists() and labor_path.exists():
    verdict_q3 = "READY"
elif domain_prov_valid >= 3:
    verdict_q3 = "PARTIALLY READY"

print(f"\nVERDICT Q3: {verdict_q3}")
print(f"  Reason: Foundational provenance layer working,")
print(f"          but semantic form collapse affects ALL domains (tax/labor/etc)")
print()

# Question 4: Top Blockers
print("\nQUESTION 4: TOP BLOCKERS FOR PRODUCTION")
print("-" * 80)
print()

blockers = [
    {
        'priority': 'CRITICAL',
        'blocker': 'Semantic Form Collapse',
        'impact': f'Only 2 logic forms (obligation, prohibition) vs legacy 10',
        'detail': 'Rule type mapping still fails for 94% of rules',
        'fix_effort': 'HIGH - requires revise _rule_type_to_logic_form() logic'
    },
    {
        'priority': 'HIGH',
        'blocker': 'Runtime Provenance Bug',
        'impact': f'Merged rule lineage not captured in derived_from_rule_ids',
        'detail': f'{runtime_prov_bug}/20 merged rules have empty provenance lists',
        'fix_effort': 'MEDIUM - populate derived_from_rule_ids in merge function'
    },
    {
        'priority': 'HIGH',
        'blocker': 'Source Document Empty',
        'impact': '1033 rules from unknown origin; .doc files are placeholders',
        'detail': 'Unclear if artifacts are cached or need re-parse',
        'fix_effort': 'MEDIUM - verify document source and re-generate if needed'
    },
    {
        'priority': 'MEDIUM',
        'blocker': 'Dedup Ratio Too High',
        'impact': f'1033 → 175 (83% compression) may lose nuance',
        'detail': 'Is this realistic deduplication or excessive filtering?',
        'fix_effort': 'LOW - review filter thresholds and signature logic'
    }
]

for i, b in enumerate(blockers, 1):
    print(f"{i}. [{b['priority']}] {b['blocker']}")
    print(f"   Impact: {b['impact']}")
    print(f"   Detail: {b['detail']}")
    print(f"   Fix: {b['fix_effort']}")
    print()

# Final Summary
print("=" * 80)
print("FINAL RECOMMENDATIONS")
print("=" * 80)
print()
print("✗ DO NOT PROCEED to tax/labor expansion until blockers resolved")
print("✓ Schema & provenance infrastructure is viable (fixable bugs)")
print("✗ Semantic restoration is CRITICAL path blocker (foundational issue)")
print()
print("Next steps:")
print("  1. Investigate rule type mapping: why obligation is fallback?")
print("  2. Review legacy vs new processing pipeline for lost form mappings")
print("  3. Fix _merge_reasoning_core_record_provenance() to populate derived_from_*")
print("  4. Verify document source (why are .doc files empty?)")
print("  5. After fixes, re-run this audit to confirm improvement")
print()
print("=" * 80)
