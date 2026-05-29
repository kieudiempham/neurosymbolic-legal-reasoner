#!/usr/bin/env python3
"""Convert qa_290 JSON to JSONL format."""

import json
import sys

# Read the JSON file
with open('evaluation/qa_290_exp_ask_only.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract and write as JSONL
cases = data.get('cases', [])
output_file = 'qa_141.jsonl'

with open(output_file, 'w', encoding='utf-8') as f:
    for i, case in enumerate(cases[:141], 1):  # First 141 cases
        line = {
            'id': i,
            'question': case.get('question', '')
        }
        f.write(json.dumps(line, ensure_ascii=False) + '\n')

print(f"Converted {len(cases[:141])} questions to {output_file}")
