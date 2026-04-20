#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Export one /ask response to a case-style JSON file with UTF-8 preservation."""

from __future__ import annotations

import json
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "tests" / "output" / "case_tax_delay_after_layer1_prompt_patch.json"

payload = {
    "question": "Nếu nộp tiền thuế trễ hạn thì doanh nghiệp có thể bị áp dụng những hậu quả pháp lý gì?",
    "session_id": "case_tax_delay_after_layer1_prompt_patch_r3",
    "domain": "tax",
    "user_facts": [],
}

resp = requests.post("http://localhost:8000/ask", json=payload, timeout=120)
resp.raise_for_status()
obj = resp.json()

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUT_PATH.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"Saved: {OUT_PATH}")
print(f"Status: {resp.status_code}")
print(f"needs_clarification: {obj.get('needs_clarification')}")
print(f"answer_present: {bool((obj.get('answer') or {}).get('answer_text'))}")
