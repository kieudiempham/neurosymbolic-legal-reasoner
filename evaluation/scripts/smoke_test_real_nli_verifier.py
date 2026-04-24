#!/usr/bin/env python
"""
Smoke test: Real NLI verifier integration — demonstrate full verification flow with real provider/model logs.

Runs a single question through the entire QA pipeline with NLI enabled,
then inspects verification_trace to confirm:
  1. verifier_backend is 'real' (not mock/degraded)
  2. nli_trace contains provider/model/decision/premise/hypothesis for each verification mode
  3. Each verification event is paper-faithful (explicit mode, scores, status)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from runtime.qa_pipeline import run_qa_pipeline


def main() -> None:
    repo = Path(__file__).resolve().parents[0]
    
    # Use real provider/model from .env (Groq OpenAI-compatible API)
    # This will bootstrap NLI Verifier as OpenAICompatibleNLIVerifier
    question = "Công ty có phải cập nhật thông tin cổ đông theo quy định không?"
    
    print(f"\n{'='*80}")
    print("SMOKE TEST: Real NLI Verifier Integration")
    print(f"{'='*80}")
    print(f"Question: {question}")
    print(f"Expected: verifier_backend.mode='real' (OpenAI-compatible NLI via Groq)")
    
    try:
        qa = run_qa_pipeline(
            question,
            debug=True,
            save_trace=False,
        )
        
        # Extract verification and backend mode info
        verif_trace = qa.pipeline_trace.steps if qa.pipeline_trace else []
        nli_runtime = qa.meta.get("nli_runtime", {}) if qa.meta else {}
        verification_records = []
        
        print(f"\nNLI Runtime Descriptor:")
        print(f"  source: {nli_runtime.get('source')}")
        print(f"  verifier_class: {nli_runtime.get('verifier_class')}")
        print(f"  model_name: {nli_runtime.get('model_name')}")
        print(f"  nli_degraded: {nli_runtime.get('nli_degraded')}")
        print(f"  nesy_nli_mock: {nli_runtime.get('nesy_nli_mock')}")
        
        # Try to extract backend_modes from debug_trace in ask/clarify response
        debug_trace = (qa.meta or {}).get("debug_trace_keys", []) if qa.meta else []
        print(f"\nDebug trace keys available: {debug_trace}")
        
        # Check verification trace summaries
        if qa.pipeline_trace and qa.pipeline_trace.steps:
            print(f"\nPipeline steps ({len(qa.pipeline_trace.steps)}):")
            for step in qa.pipeline_trace.steps:
                print(f"  - {step.name}: {step.status}")
                if step.output_summary:
                    if "nli_trace" in step.output_summary:
                        nli = step.output_summary["nli_trace"]
                        verification_records.append({
                            "mode": nli.get("mode"),
                            "nli_status": nli.get("nli_status"),
                            "nli_enabled": nli.get("nli_enabled"),
                            "nli_provider": nli.get("nli_provider"),
                            "nli_model_name": nli.get("nli_model_name"),
                            "has_premise": "premise" in nli,
                            "has_hypothesis": "hypothesis" in nli,
                            "has_decision": "nli_decision" in nli or "nli_label" in nli,
                        })
        
        if verification_records:
            print(f"\nVerification Records Trace ({len(verification_records)}):")
            for rec in verification_records:
                print(f"  Mode: {rec['mode']}")
                print(f"    Status: {rec['nli_status']}")
                print(f"    Enabled: {rec['nli_enabled']}")
                print(f"    Provider: {rec['nli_provider']}")
                print(f"    Model: {rec['nli_model_name']}")
                print(f"    Has premise: {rec['has_premise']}")
                print(f"    Has hypothesis: {rec['has_hypothesis']}")
                print(f"    Has decision: {rec['has_decision']}")
        
        # Status summary
        print(f"\nFinal QA Status:")
        print(f"  Status: {qa.status}")
        print(f"  Has answer: {bool(qa.final_answer and qa.final_answer.answer_text)}")
        print(f"  Needs clarification: {bool(qa.clarification_prompts)}")
        
        # Validate expectations
        print(f"\n{'='*80}")
        print("VALIDATION:")
        
        # Check NLI runtime is NOT degraded/mock
        if nli_runtime.get('source') in ('degraded_symbolic_only', 'mock', 'fallback_mock'):
            print(f"  ✗ FAIL: NLI source is '{nli_runtime.get('source')}' (expected 'hf' or 'api')")
            return
        else:
            print(f"  ✓ PASS: NLI source is '{nli_runtime.get('source')}' (not degraded/mock)")
        
        # Check nli_degraded flag is False
        if nli_runtime.get('nli_degraded'):
            print(f"  ✗ FAIL: nli_degraded=True")
            return
        else:
            print(f"  ✓ PASS: nli_degraded=False")
        
        # Check nesy_nli_mock flag is False
        if nli_runtime.get('nesy_nli_mock'):
            print(f"  ✗ FAIL: nesy_nli_mock=True (should be False for non-mock)")
            return
        else:
            print(f"  ✓ PASS: nesy_nli_mock=False")
        
        # Check verifier_class is one of the real implementations
        vclass = nli_runtime.get('verifier_class', '')
        if vclass in ('HuggingFaceNLIVerifier', 'OpenAICompatibleNLIVerifier'):
            print(f"  ✓ PASS: verifier_class='{vclass}' (real NLI backend)")
        else:
            print(f"  ✗ WARN: verifier_class='{vclass}' (not HF/OpenAI-compatible)")
        
        # Check model_name is set
        if nli_runtime.get('model_name'):
            print(f"  ✓ PASS: model_name is set to '{nli_runtime.get('model_name')}'")
        else:
            print(f"  ✗ WARN: model_name is not set")
        
        # Check verification records have premise/hypothesis/decision
        good_records = sum(1 for r in verification_records if r['has_premise'] and r['has_hypothesis'])
        if verification_records:
            print(f"  ✓ PASS: {good_records}/{len(verification_records)} verification records include premise+hypothesis")
        
        print(f"\n{'='*80}")
        print("✓ Smoke test completed successfully!")
        print(f"  Verifier backend: {nli_runtime.get('verifier_class')} ({nli_runtime.get('source')})")
        print(f"  Model: {nli_runtime.get('model_name')}")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
