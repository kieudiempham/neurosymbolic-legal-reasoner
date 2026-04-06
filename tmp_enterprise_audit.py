import json
from pathlib import Path
from collections import Counter

root = Path('data/processed/rulebase')
old = root / 'doanhnghiep'
new = root / 'enterprise'

old_logic = json.loads((old / 'rulebase_logic.json').read_text(encoding='utf-8'))
old_rules = old_logic['rules']
new_can = []
for line in (new / 'canonical_rules.jsonl').read_text(encoding='utf-8').splitlines():
    if line.strip():
        new_can.append(json.loads(line))
new_domain = []
for line in (new / 'canonical' / 'enterprise_core.jsonl').read_text(encoding='utf-8').splitlines():
    if line.strip():
        new_domain.append(json.loads(line))
new_runtime = json.loads((new / 'runtime' / 'rulebase_reasoning_core.json').read_text(encoding='utf-8'))
shared_rules = []
sh_path = new / 'canonical' / 'shared' / 'shared_rule_pack.jsonl'
if sh_path.exists():
    for line in sh_path.read_text(encoding='utf-8').splitlines():
        if line.strip():
            shared_rules.append(json.loads(line))

print('counts:')
print('  old rules', len(old_rules))
print('  new canonical', len(new_can))
print('  new domain core', len(new_domain))
print('  new runtime core', len(new_runtime.get('rules_reasoning_core', [])))
print('  shared rules', len(shared_rules))
print('  old metadata rule_count', old_logic.get('rule_count'))
print('  old exportable_clean_count', old_logic.get('rules_exportable_clean_count'))
print('  old traceability_only_count', old_logic.get('rules_traceability_only_count'))
print('  old excluded_from_core', len(json.loads((old / 'rulebase_reasoning_core.json').read_text(encoding='utf-8')).get('excluded_from_core', [])))


def uniq_preds(rules):
    out = set()
    for r in rules:
        head = r.get('head') if 'head' in r else r.get('canonical_head')
        if head and head.get('predicate'):
            out.add(head.get('predicate'))
        if 'predicate_candidates' in r and isinstance(r['predicate_candidates'], dict):
            v = r['predicate_candidates'].get('normalized')
            if v:
                out.add(v)
    return out

old_preds = uniq_preds(old_rules)
new_preds = uniq_preds(new_can)
print('unique predicates: old', len(old_preds), 'new', len(new_preds))

old_missing_canonical = sum(1 for r in old_rules if not ((r.get('metadata') or {}).get('canonical_predicate')))
new_missing_canonical = sum(1 for r in new_can if not (r.get('canonical_head', {}).get('predicate')))

old_missing_source = sum(1 for r in old_rules if not ((r.get('metadata') or {}).get('source_ref')))
new_missing_source = sum(1 for r in new_can if not (r.get('source_ref')))

old_missing_authority = sum(1 for r in old_rules if not ((r.get('metadata') or {}).get('authority_canonical')))
new_missing_authority = sum(
    1
    for r in new_can
    if r.get('logic_form') == 'authority_action'
    and not any(
        (item.get('predicate') == 'authority' or 'authority' in str(item.get('predicate')).lower())
        for item in (r.get('canonical_body') or [])
    )
)

old_missing_document = sum(
    1
    for r in old_rules
    if r.get('logic_form') == 'dossier' and not ((r.get('metadata') or {}).get('document_canonical'))
)
new_missing_document = sum(
    1
    for r in new_can
    if r.get('logic_form') == 'dossier'
    and not any(
        (item.get('predicate') == 'document' or 'document' in str(item.get('predicate')).lower())
        for item in (r.get('canonical_body') or [])
    )
)

old_missing_deadline = sum(
    1
    for r in old_rules
    if r.get('logic_form') == 'deadline' and not ((r.get('metadata') or {}).get('deadline_anchor'))
)
new_missing_deadline = sum(
    1
    for r in new_can
    if r.get('logic_form') == 'deadline'
    and not any(
        'deadline' in str(item.get('predicate')).lower() or 'deadline' in ' '.join(str(a) for a in item.get('args') or [])
        for item in (r.get('canonical_body') or []) + [r.get('canonical_head', {})]
    )
)

old_missing_effect = sum(
    1
    for r in old_rules
    if r.get('logic_form') == 'legal_effect' and not ((r.get('metadata') or {}).get('effect_canonical'))
)
new_missing_effect = sum(
    1
    for r in new_can
    if r.get('logic_form') == 'legal_effect'
    and not any(
        'effect' in str(item.get('predicate')).lower() or 'effect' in ' '.join(str(a) for a in item.get('args') or [])
        for item in (r.get('canonical_body') or []) + [r.get('canonical_head', {})]
    )
)

print('missing canonical_predicate: old', old_missing_canonical, 'new', new_missing_canonical)
print('missing source_ref: old', old_missing_source, 'new', new_missing_source)
print('missing authority heuristic: old', old_missing_authority, 'new', new_missing_authority)
print('missing dossier/document heuristic: old', old_missing_document, 'new', new_missing_document)
print('missing deadline: old', old_missing_deadline, 'new', new_missing_deadline)
print('missing legal_effect: old', old_missing_effect, 'new', new_missing_effect)

old_forms = Counter(r.get('logic_form') for r in old_rules)
new_forms = Counter(r.get('logic_form') for r in new_can)
print('logic_form counts old', dict(old_forms))
print('logic_form counts new', dict(new_forms))

old_signatures = Counter()
for r in old_rules:
    head = r.get('head', {})
    body = tuple((item.get('predicate'), tuple(item.get('args') or [])) for item in (r.get('body') or []))
    old_signatures[(head.get('predicate'), body)] += 1
new_signatures = Counter()
for r in new_can:
    head = r.get('canonical_head', {})
    body = tuple((item.get('predicate'), tuple(item.get('args') or [])) for item in (r.get('canonical_body') or []))
    new_signatures[(head.get('predicate'), body)] += 1
print('exact duplicate groups old', sum(1 for v in old_signatures.values() if v > 1), 'new', sum(1 for v in new_signatures.values() if v > 1))
print('total duplicate rules old', sum(v - 1 for v in old_signatures.values() if v > 1), 'new', sum(v - 1 for v in new_signatures.values() if v > 1))
print('unique signatures old', len(old_signatures), 'new', len(new_signatures))

# predicate distribution
old_pred_counter = Counter()
for r in old_rules:
    h = r.get('head', {})
    if h.get('predicate'): old_pred_counter[h.get('predicate')] += 1
new_pred_counter = Counter()
for r in new_can:
    h = r.get('canonical_head', {})
    if h.get('predicate'): new_pred_counter[h.get('predicate')] += 1
print('top old predicates', old_pred_counter.most_common(20))
print('top new predicates', new_pred_counter.most_common(20))

old_prov = sum(1 for r in old_rules if (r.get('metadata') or {}).get('provenance') or (r.get('metadata') or {}).get('source_ref_full'))
new_prov = sum(1 for r in new_can if r.get('source_doc') and r.get('source_ref'))
print('provenance usable old', old_prov, '/', len(old_rules), 'new', new_prov, '/', len(new_can))
new_doc_prov = sum(1 for r in new_can if r.get('source_doc') and r.get('doc_code') and r.get('source_unit_id'))
print('doc-level provenance present new', new_doc_prov, '/', len(new_can))

# sample shared rules
print('shared rule sample', shared_rules[:2])
