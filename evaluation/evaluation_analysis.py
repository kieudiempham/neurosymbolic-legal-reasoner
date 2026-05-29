#!/usr/bin/env python3
"""Analyze 290 legal QA answers - IRAC, citations, hallucinations"""
import json

# Load and parse
data = []
with open('evaluation/results/qa_290_answers.jsonl', encoding='utf-8') as f:
    for line in f:
        data.append(json.loads(line))

# Extract by domain
domains = {'BHXH': [], 'DOANH_NGHIEP': [], 'THUE': [], 'LIEN_NGANH': []}
for item in data:
    case_id = item['id']
    domain = case_id.split('-')[0]
    domains[domain].append(item)

# ===== IRAC SCORES =====
print('='*60)
print('IRAC SCORES ANALYSIS')
print('='*60)
for domain, items in domains.items():
    irac_list = [i.get('irac', {}) for i in items]
    I_vals = [s.get('I', 0) for s in irac_list if 'I' in s]
    R_vals = [s.get('R', 0) for s in irac_list if 'R' in s]
    A_vals = [s.get('A', 0) for s in irac_list if 'A' in s]
    C_vals = [s.get('C', 0) for s in irac_list if 'C' in s]
    L_vals = [s.get('L', 0) for s in irac_list if 'L' in s]
    scores_vals = [s.get('score', 0) for s in irac_list if 'score' in s]
    
    if I_vals:
        print(f'\n{domain} (n={len(items)})')
        print(f'  Issue (I)     : avg={sum(I_vals)/len(I_vals):.2f}, range=[{min(I_vals):.2f}, {max(I_vals):.2f}]')
        print(f'  Rule (R)      : avg={sum(R_vals)/len(R_vals):.2f}, range=[{min(R_vals):.2f}, {max(R_vals):.2f}]')
        print(f'  Analysis (A)  : avg={sum(A_vals)/len(A_vals):.2f}, range=[{min(A_vals):.2f}, {max(A_vals):.2f}]')
        print(f'  Conclusion(C) : avg={sum(C_vals)/len(C_vals):.2f}, range=[{min(C_vals):.2f}, {max(C_vals):.2f}]')
        print(f'  Legal (L)     : avg={sum(L_vals)/len(L_vals):.2f}, range=[{min(L_vals):.2f}, {max(L_vals):.2f}]')
        print(f'  Overall score : avg={sum(scores_vals)/len(scores_vals):.2f}, range=[{min(scores_vals):.2f}, {max(scores_vals):.2f}]')

# ===== QUALITY METRICS =====
print('\n' + '='*60)
print('QUALITY METRICS BY DOMAIN')
print('='*60)
total_stats = {'has_citation': 0, 'citation_correct': 0, 'hallucination': 0}

for domain, items in domains.items():
    has_cit = sum(1 for i in items if i.get('has_citation', False))
    cit_corr = sum(1 for i in items if i.get('citation_correct', False))
    halluc = sum(1 for i in items if i.get('hallucination', False))
    
    total_stats['has_citation'] += has_cit
    total_stats['citation_correct'] += cit_corr
    total_stats['hallucination'] += halluc
    
    n = len(items)
    print(f'\n{domain} (n={n})')
    print(f'  Has citations: {has_cit}/{n} ({100*has_cit/n:.1f}%)')
    print(f'  Citations OK : {cit_corr}/{n} ({100*cit_corr/n:.1f}%)')
    print(f'  No halluc    : {n-halluc}/{n} ({100*(n-halluc)/n:.1f}%)')

# ===== OVERALL STATS =====
print('\n' + '='*60)
print('OVERALL STATISTICS (290 cases)')
print('='*60)
print(f'Has citations    : {total_stats["has_citation"]}/290 ({100*total_stats["has_citation"]/290:.1f}%)')
print(f'Citations correct: {total_stats["citation_correct"]}/290 ({100*total_stats["citation_correct"]/290:.1f}%)')
print(f'No hallucinations: {290-total_stats["hallucination"]}/290 ({100*(290-total_stats["hallucination"])/290:.1f}%)')

# ===== ANSWER MODES =====
print(f'\nAnswer modes distribution:')
modes = {}
for item in data:
    mode = item.get('pred_mode', 'unknown')
    modes[mode] = modes.get(mode, 0) + 1
for mode in sorted(modes.keys()):
    print(f'  {mode:10}: {modes[mode]:3} cases ({100*modes[mode]/290:.1f}%)')

# ===== ANSWER LENGTH =====
print('\n' + '='*60)
print('ANSWER LENGTH ANALYSIS')
print('='*60)
lengths_by_domain = {}
for item in data:
    domain = item['id'].split('-')[0]
    if domain not in lengths_by_domain:
        lengths_by_domain[domain] = []
    lengths_by_domain[domain].append(len(item.get('pred_answer', '')))

for domain in sorted(lengths_by_domain.keys()):
    lens = lengths_by_domain[domain]
    avg = sum(lens) / len(lens)
    print(f'{domain:15}: avg={avg:.0f} chars, min={min(lens)}, max={max(lens)}')

print('\n' + '='*60)
print('FILE SUMMARY')
print('='*60)
print(f'Total answers  : {len(data)}')
print(f'All domains    : {", ".join(sorted(domains.keys()))}')
print(f'Output file    : evaluation/results/qa_290_answers.jsonl')
print('='*60)
