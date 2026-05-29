#!/usr/bin/env python3
"""
Baseline generator for legal QA using OpenAI API.
Generates two baselines:
1. Direct: No context, pure legal expertise
2. RAG: With simulated legal context
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import tqdm
from openai import OpenAI, RateLimitError, APIError


def load_env_file(filepath: str = ".env") -> None:
    """Load environment variables from .env file."""
    if not os.path.exists(filepath):
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


# Load .env file at startup
load_env_file()


# Configuration
CONFIG = {
    "input_file": "evaluation/qa_290_exp_ask_only.json",  # JSON or JSONL file
    "output_direct": "baseline_direct.jsonl",
    "model": "llama-3.1-8b-instant",  # For Groq: "llama-3.1-8b-instant", "mixtral-8x7b-32768"
    "provider": "groq",  # "openai" or "groq" - auto-detect if not set
    "temperature": 0.2,
    "max_retries": 3,
    "retry_wait": 2.0,  # seconds
    "rate_limit_sleep": 0.5,  # seconds
}

# System prompts
SYSTEM_DIRECT = (
    "You are a Vietnamese legal expert. Answer clearly and concisely. "
    "Provide legal basis (Điều, Khoản) if possible. Do not hallucinate."
)

SYSTEM_RAG = (
    "You are a Vietnamese legal expert. Use the provided context to answer. "
    "Cite legal articles if possible. Do not make up laws."
)

# Simulated RAG context
RAG_CONTEXT = (
    "Các quy định pháp luật liên quan đến câu hỏi này bao gồm các điều khoản "
    "trong luật BHXH, Luật Doanh nghiệp và Luật Thuế hiện hành."
)


def load_jsonl(filepath: str) -> List[Dict[str, Any]]:
    """
    Load JSONL or JSON file.
    
    Args:
        filepath: Path to JSONL or JSON file
        
    Returns:
        List of parsed JSON objects with 'id' and 'question' fields
        
    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If line/file is not valid JSON
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    data = []
    
    # Check if it's a JSON file (from .json extension)
    if filepath.endswith('.json'):
        with open(filepath, 'r', encoding='utf-8') as f:
            obj = json.load(f)
            # Handle different JSON structures
            if isinstance(obj, dict):
                # Structure: {"cases": [...], "metadata": ...}
                if 'cases' in obj:
                    cases = obj['cases']
                    for idx, case in enumerate(cases, 1):
                        data.append({
                            'id': case.get('id', idx),
                            'question': case.get('question', '')
                        })
                # Structure: {"metadata": ..., "data": [...]}
                elif 'data' in obj:
                    for idx, item in enumerate(obj['data'], 1):
                        data.append({
                            'id': item.get('id', idx),
                            'question': item.get('question', '')
                        })
                else:
                    # Direct array of objects
                    raise ValueError("Unrecognized JSON structure")
            elif isinstance(obj, list):
                # Direct list of objects
                for idx, item in enumerate(obj, 1):
                    data.append({
                        'id': item.get('id', idx),
                        'question': item.get('question', '')
                    })
    else:
        # JSONL file
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                try:
                    obj = json.loads(line)
                    data.append(obj)
                except json.JSONDecodeError as e:
                    print(f"Error parsing line {line_num}: {e}", file=sys.stderr)
                    raise
    
    return data


def call_model(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    model: str = CONFIG["model"],
    temperature: float = CONFIG["temperature"],
    max_retries: int = CONFIG["max_retries"],
) -> str:
    """
    Call OpenAI API with retry logic.
    
    Args:
        client: OpenAI client instance
        system_prompt: System role message
        user_prompt: User message
        model: Model name
        temperature: Sampling temperature
        max_retries: Maximum number of retries
        
    Returns:
        Generated response text
        
    Raises:
        APIError: If all retries fail
    """
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
            )
            return response.choices[0].message.content
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = CONFIG["retry_wait"] * (2 ** attempt)
                print(f"Rate limited. Retrying in {wait_time}s...", file=sys.stderr)
                time.sleep(wait_time)
            else:
                raise
        except APIError as e:
            if attempt < max_retries - 1:
                print(f"API error: {e}. Retrying...", file=sys.stderr)
                time.sleep(CONFIG["retry_wait"])
            else:
                raise


def run_baseline(
    input_file: str,
    output_direct: str,
    model: str = CONFIG["model"],
) -> None:
    """
    Run baseline (direct only) and save results. Supports resume.
    
    Args:
        input_file: Input JSONL/JSON file path
        output_direct: Output file for direct baseline
        model: Model to use
    """
    # Detect and initialize client
    provider = CONFIG["provider"]
    
    # Auto-detect provider from environment variables
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        if os.getenv("GROQ_API_KEY"):
            provider = "groq"
    elif provider == "groq" and not os.getenv("GROQ_API_KEY"):
        if os.getenv("OPENAI_API_KEY"):
            provider = "openai"
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Please export OPENAI_API_KEY=your_key or set GROQ_API_KEY"
            )
        client = OpenAI(api_key=api_key)
        print(f"Using OpenAI API with model: {model}", file=sys.stderr)
    elif provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable not set. "
                "Please export GROQ_API_KEY=your_key"
            )
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        print(f"Using Groq API with model: {model}", file=sys.stderr)
    else:
        raise ValueError(f"Unknown provider: {provider}")
    
    # Load input data
    print(f"Loading {input_file}...", file=sys.stderr)
    data = load_jsonl(input_file)
    print(f"Loaded {len(data)} questions", file=sys.stderr)
    
    # Check if resuming
    start_idx = 0
    processed_ids = set()
    if os.path.exists(output_direct):
        with open(output_direct, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        obj = json.loads(line)
                        processed_ids.add(obj.get('id'))
                        start_idx += 1
                    except:
                        pass
        if start_idx > 0:
            print(f"Resuming from question {start_idx + 1}/{len(data)}", file=sys.stderr)
    
    # Open output file in append mode
    f_direct = open(output_direct, 'a', encoding='utf-8')
    
    try:
        # Process each question starting from start_idx
        for item in tqdm.tqdm(data[start_idx:], desc="Processing questions", initial=start_idx, total=len(data)):
            question_id = item["id"]
            question = item["question"]
            
            # Skip if already processed
            if question_id in processed_ids:
                continue
            
            # Baseline: Direct (no RAG)
            user_prompt_direct = f"Câu hỏi: {question}\nTrả lời:"
            try:
                answer_direct = call_model(
                    client,
                    SYSTEM_DIRECT,
                    user_prompt_direct,
                    model=model,
                )
            except Exception as e:
                print(
                    f"Error processing question {question_id} (direct): {e}",
                    file=sys.stderr,
                )
                answer_direct = ""
            
            result_direct = {
                "id": question_id,
                "question": question,
                "answer": answer_direct,
                "system": "gpt4_direct",
            }
            f_direct.write(json.dumps(result_direct, ensure_ascii=False) + "\n")
            f_direct.flush()
            
            # Rate limit
            time.sleep(CONFIG["rate_limit_sleep"])
        
        print(f"All questions completed! Results written to {output_direct}", file=sys.stderr)
    
    finally:
        f_direct.close()


def main():
    """Main entry point."""
    try:
        run_baseline(
            input_file=CONFIG["input_file"],
            output_direct=CONFIG["output_direct"],
            model=CONFIG["model"],
        )
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
