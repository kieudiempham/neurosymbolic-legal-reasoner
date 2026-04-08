#!/usr/bin/env python
"""Smoke tests for /ask endpoint with Vietnamese legal questions."""

import json
import requests
import sys

BASE_URL = "http://localhost:8000"

test_cases = [
    {
        "name": "Enterprise Domain - Business Registration Documents",
        "domain": "enterprise",
        "question": "Doanh nghiệp phải chuẩn bị những tài liệu gì để đăng ký?",
    },
    {
        "name": "Tax Domain - Tax Obligations",
        "domain": "tax",
        "question": "Các doanh nghiệp có nghĩa vụ gì liên quan đến khai báo thuế?",
    },
    {
        "name": "Labor Domain - Worker Rights",
        "domain": "labor",
        "question": "Lao động có quyền gì khi làm việc theo hợp đồng?",
    },
]

print("=" * 90)
print("SMOKE TESTS: /ask ENDPOINT WITH VIETNAMESE LEGAL QUESTIONS")
print("=" * 90 + "\n")

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*90}")
    print(f"TEST {i}: {test['name']}")
    print(f"{'='*90}")
    print(f"Domain:   {test['domain']}")
    print(f"Question: {test['question']}")
    print()
    
    payload = {
        "question": test["question"],
        "domain": test["domain"],
        "use_router": False,
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/ask",
            json=payload,
            timeout=30,
        )
        
        if response.status_code != 200:
            print(f"❌ HTTP ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            continue
        
        data = response.json()
        
        # Parse response
        print(f"Response Status: ✅ 200 OK\n")
        
        # Question parse result
        if "layer2" in data and data["layer2"]:
            l2 = data["layer2"]
            print(f"Question Parse:")
            print(f"  - Parsed successfully")
            print(f"  - Goal: {l2.get('goal', {}).get('predicate', 'N/A')}")
        
        # Retrieved rules
        retrieved_rules = data.get("retrieved_rules", [])
        print(f"\nRetrieval Results:")
        print(f"  - retrieved_rules count: {len(retrieved_rules)}")
        if retrieved_rules:
            first_rule = retrieved_rules[0]
            print(f"  - first_rule_id: {first_rule.get('rule_id', 'N/A')}")
        
        # Reasoning results
        selected_rule = data.get("selected_rule")
        proof = data.get("proof")
        answer = data.get("answer")
        
        print(f"\nReasoning Results:")
        print(f"  - selected_rule: {selected_rule if selected_rule else 'EMPTY'}")
        print(f"  - proof: {'present' if proof else 'EMPTY'}")
        print(f"  - answer: {'present' if answer else 'EMPTY'}")
        
        if proof:
            if isinstance(proof, dict):
                print(f"    Proof type: {type(proof).__name__}")
            else:
                print(f"    Proof preview: {str(proof)[:80]}...")
        if answer:
            if isinstance(answer, dict):
                print(f"    Answer keys: {list(answer.keys())}")
            else:
                print(f"    Answer preview: {str(answer)[:80]}...")
        
        # Debug trace errors
        debug_trace = data.get("debug_trace", {})
        error = debug_trace.get("error")
        verification_diags = debug_trace.get("verification_diagnostics") or []
        verification_diags_after = debug_trace.get("verification_diagnostics_after_repair") or []
        retrieval_repair_summary = debug_trace.get("retrieval_ranking_repair_summary") or {}
        answer_repair = debug_trace.get("answer_repair") or []
        
        print(f"\nDebug Trace:")
        if error:
            print(f"  - Error: {error}")
        else:
            print(f"  - No errors")

        print(f"\nVerification Decisions:")
        if verification_diags:
            for diag in verification_diags[:5]:
                print(
                    f"  - {diag.get('rule_id', 'N/A')}: {diag.get('verification_level', diag.get('verification_decision', 'N/A'))}"
                    f" | reason={diag.get('rejection_reason', diag.get('reason', []))}"
                )
        else:
            print("  - No pre-repair verification diagnostics")

        if verification_diags_after:
            print("\nVerification Decisions After Repair:")
            for diag in verification_diags_after[:5]:
                print(
                    f"  - {diag.get('rule_id', 'N/A')}: {diag.get('verification_level', diag.get('verification_decision', 'N/A'))}"
                    f" | reason={diag.get('rejection_reason', diag.get('reason', []))}"
                )

        print("\nRepair Loop:")
        if retrieval_repair_summary:
            print(f"  - repair loop trigger stage: retrieval_ranking")
            print(f"  - repair_target: {retrieval_repair_summary.get('repair_target')}")
            print(f"  - decision after repair: {retrieval_repair_summary.get('decision')}")
            print(f"  - post_repair_gain: {retrieval_repair_summary.get('post_repair_gain')}")
        else:
            print("  - repair loop trigger stage: none logged at retrieval_ranking")

        if answer_repair:
            print(f"  - answer repair attempts: {answer_repair[-1].get('attempts_used', 0)}")
        
        # Clarification questions
        if data.get("clarification_questions"):
            print(f"  - Needs clarification: {len(data['clarification_questions'])} questions")
        
        # Summary
        print(f"\nStatus Summary:")
        retrieval_ok = len(retrieved_rules) > 0
        reasoning_ok = bool(answer)
        parse_ok = not data.get("debug_trace", {}).get("error", "").startswith("parse")
        
        if error:
            print(f"  ❌ Pipeline blocked: {error}")
        if retrieval_ok:
            print(f"  ✅ RETRIEVAL: Working ({len(retrieved_rules)} rules found)")
        else:
            print(f"  ❌ RETRIEVAL: No rules retrieved")
        if reasoning_ok:
            print(f"  ✅ REASONING: Working (answer generated)")
        elif retrieval_ok:
            print(f"  ⚠️  REASONING: Rules found but verification/reasoning failed")
        else:
            print(f"  ⚠️  REASONING: No input (no rules retrieved)")
        
        
        
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
        continue
    except Exception as e:
        print(f"❌ PARSE ERROR: {e}")
        continue

print(f"\n{'='*90}")
print("END OF SMOKE TESTS")
print(f"{'='*90}\n")
