#!/usr/bin/env python3
"""
E2E Test for patch2: Fact-application mode with conditional reasoning
Validates that Q2 produces missing_facts and conditional answer
"""
import sys
import json
import time
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

BASE_URL = "http://localhost:8002"

# Test questions
TEST_CASES = [
    {
        "test_id": "Q1",
        "question": "Thời hạn thông báo thay đổi nội dung đăng ký doanh nghiệp là bao nhiêu ngày?",
        "expected_mode": "rule_reading",
        "expected_status": "none",
        "expect_missing_facts": False,
    },
    {
        "test_id": "Q2",
        "question": "Công ty tôi thay đổi nội dung đăng ký nhưng chưa rõ thời điểm gửi thông báo, vậy có bị quá hạn không?",
        "expected_mode": "fact_application",
        "expected_status": "conditional",
        "expect_missing_facts": True,
    },
]

def run_question(question: str):
    """Run a question through the QA pipeline"""
    url = f"{BASE_URL}/ask"
    payload = {
        "question": question,
        "session_id": f"test_{int(time.time())}",
        "user_id": "test_user"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"ERROR: Failed to query: {e}")
        return None

def extract_minimal_fields(result: dict) -> dict:
    """Extract minimal evaluation fields from result"""
    if not result:
        return {}
    
    # Handle answer field safely (might be string, dict, or list)
    answer_text = ""
    if isinstance(result.get("answer"), str):
        answer_text = result.get("answer", "")[:200]
    elif result.get("answer"):
        answer_text = str(result.get("answer", ""))[:200]
    
    # Map response fields
    extracted = {
        "test_id": result.get("session_id", "unknown"),
        "question": result.get("question", ""),
        "question_mode": result.get("question_mode", "unknown"),
        "application_status": result.get("application_status", "unknown"),
        "final_decision": result.get("final_decision", ""),
        "answer_text": answer_text,
        "selected_rule_id": result.get("selected_rule", {}).get("rule_id", "") if isinstance(result.get("selected_rule"), dict) else "",
        "legal_citations": result.get("legal_citations", []),
        "proof_present": bool(result.get("proof_trace")),
        "missing_facts": result.get("missing_facts", []),
        "needs_clarification": result.get("needs_clarification", False),
        "error_stage_final": result.get("error_stage", ""),
        "forward_failure_reason": result.get("forward_failure_reason", ""),
        "verification_summary": result.get("verification_summary", ""),
    }
    
    return extracted

def main():
    print("=" * 80)
    print("PATCH2 E2E TEST: Fact-Application with Conditional Reasoning")
    print("=" * 80)
    print()
    
    results = []
    
    for test_case in TEST_CASES:
        print(f"Running test {test_case['test_id']}: {test_case['question'][:60]}...")
        result = run_question(test_case["question"])
        
        if result:
            extracted = extract_minimal_fields(result)
            extracted["test_id"] = test_case["test_id"]
            extracted["question"] = test_case["question"]
            
            # Validation
            mode_ok = extracted.get("question_mode") == test_case["expected_mode"]
            status_ok = extracted.get("application_status") == test_case["expected_status"]
            facts_ok = (len(extracted.get("missing_facts", [])) > 0) == test_case["expect_missing_facts"]
            
            print(f"  Mode: {extracted.get('question_mode')} (expected {test_case['expected_mode']}) {'✓' if mode_ok else '✗'}")
            print(f"  Status: {extracted.get('application_status')} (expected {test_case['expected_status']}) {'✓' if status_ok else '✗'}")
            print(f"  Missing Facts: {len(extracted.get('missing_facts', []))} (expect {test_case['expect_missing_facts']}) {'✓' if facts_ok else '✗'}")
            
            if test_case["expect_missing_facts"] and extracted.get("missing_facts"):
                print(f"  Found missing facts: {extracted['missing_facts'][:2]}")
            
            results.append(extracted)
        else:
            print(f"  ERROR: Failed to get result")
            results.append({
                "test_id": test_case["test_id"],
                "question": test_case["question"],
                "error": "Request failed"
            })
        
        print()
    
    # Save to JSON
    output_file = Path(__file__).parent / "patch2_minimal_eval.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "tests": results,
            "summary": {
                "total": len(results),
                "timestamp": time.time()
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to {output_file}")
    
    # Summary
    all_pass = all(
        (r.get("question_mode") == TEST_CASES[i].get("expected_mode") and
         r.get("application_status") == TEST_CASES[i].get("expected_status") and
         (len(r.get("missing_facts", [])) > 0) == TEST_CASES[i].get("expect_missing_facts"))
        for i, r in enumerate(results) if i < len(TEST_CASES)
    )
    
    print()
    print(f"Overall: {'✓ ALL TESTS PASS' if all_pass else '✗ SOME TESTS FAILED'}")

if __name__ == "__main__":
    main()
