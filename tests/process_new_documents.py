#!/usr/bin/env python
"""
Helper script to process new legal documents through the parsing pipeline.
"""

import argparse
import subprocess
import sys
from pathlib import Path
import glob
from collections import defaultdict

def find_new_documents():
    """Find .docx and .doc files in data/raw/legal_corpus/"""
    
    docs_by_domain = defaultdict(list)
    
    for domain in ['labor', 'tax', 'enterprise']:
        domain_path = f'data/raw/legal_corpus/{domain}'
        
        # Find all .doc and .docx files
        doc_files = glob.glob(f'{domain_path}/*.doc') + glob.glob(f'{domain_path}/*.docx')
        
        if doc_files:
            # Get just the filenames
            filenames = [Path(f).name for f in sorted(doc_files)]
            docs_by_domain[domain] = filenames
    
    return docs_by_domain

def update_config(domain, doc_files, config_path):
    """Update the pipeline configuration file with new documents"""
    
    import yaml
    
    # Map domain to config file
    if domain == 'enterprise':
        config_file = 'configs/law_rulebase_pipeline.yaml'
    elif domain == 'labor':
        config_file = 'configs/labor_rulebase_pipeline.yaml'
    elif domain == 'tax':
        config_file = 'configs/tax_rulebase_pipeline.yaml'
    else:
        raise ValueError(f"Unknown domain: {domain}")
    
    config_path = Path(config_file)
    
    # Read current config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Update doc_files
    config['doc_files'] = doc_files
    config['domain'] = domain
    
    # Write back
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"✓ Updated {config_file}")
    print(f"  Domain: {domain}")
    print(f"  Documents: {len(doc_files)}")
    for doc in doc_files:
        print(f"    - {doc}")
    
    return config_path

def run_pipeline(domain, config_path):
    """Run the law rulebase pipeline"""
    
    print(f"\n{'='*80}")
    print(f"Running pipeline for {domain}...")
    print(f"{'='*80}\n")
    
    cmd = [
        sys.executable,
        'src/pipelines/run_law_rulebase_pipeline.py',
        '--config', str(config_path),
        '--domain', domain
    ]
    
    try:
        result = subprocess.run(cmd, cwd=Path.cwd(), capture_output=False)
        if result.returncode != 0:
            print(f"❌ Pipeline failed with return code {result.returncode}")
            return False
        else:
            print(f"✓ Pipeline completed successfully")
            return True
    except Exception as e:
        print(f"❌ Error running pipeline: {e}")
        return False

def count_results():
    """Count the results after pipeline execution"""
    
    print(f"\n{'='*80}")
    print("Counting extracted components...")
    print(f"{'='*80}\n")
    
    import pandas as pd
    
    domains = ['labor', 'tax', 'enterprise']
    all_docs = set()
    all_chapters = set()
    all_articles = set()
    all_clauses = set()
    all_points = set()
    
    for domain in domains:
        base_path = f'data/interim/law_parsing/{domain}/'
        units_file = f'{base_path}legal_units_review.xlsx'
        
        try:
            df = pd.read_excel(units_file)
            
            all_docs.update(df['doc_id'].dropna().unique())
            all_chapters.update(df['chapter'].dropna().unique())
            all_articles.update(df['article'].dropna().unique())
            all_clauses.update(df['clause'].dropna().unique())
            all_points.update(df['point'].dropna().unique())
        except Exception as e:
            print(f"Warning: Could not read {units_file}: {e}")
    
    print(f"No. | Component Type              | Quantity")
    print("-" * 50)
    print(f"1   | Legal documents             | {len(all_docs)}")
    print(f"2   | Chapters                    | {len(all_chapters)}")
    print(f"3   | Articles                    | {len(all_articles)}")
    print(f"4   | Clauses (Khoản)             | {len(all_clauses)}")
    print(f"5   | Points (Điểm)               | {len(all_points)}")

def main():
    parser = argparse.ArgumentParser(description="Process new legal documents through the parsing pipeline.")
    parser.add_argument('--domain', type=str, default=None, help="Domain to process (labor, tax, enterprise)")
    parser.add_argument('--auto', action='store_true', help="Auto-process all domains without confirmation")
    
    args = parser.parse_args()
    
    # Find documents
    docs_by_domain = find_new_documents()
    
    if not any(docs_by_domain.values()):
        print("No documents found in data/raw/legal_corpus/")
        return
    
    print("="*80)
    print("DOCUMENT DISCOVERY")
    print("="*80)
    print("\nDocuments found by domain:\n")
    
    for domain in ['labor', 'tax', 'enterprise']:
        if domain in docs_by_domain:
            print(f"{domain.upper()}: {len(docs_by_domain[domain])} documents")
            for doc in docs_by_domain[domain]:
                print(f"  - {doc}")
        else:
            print(f"{domain.upper()}: No documents")
    
    # Process
    domains_to_process = []
    
    if args.domain:
        domains_to_process = [args.domain]
    elif args.auto:
        domains_to_process = [d for d in docs_by_domain if docs_by_domain[d]]
    else:
        print("\nWhich domains would you like to process?")
        for domain in ['labor', 'tax', 'enterprise']:
            if docs_by_domain.get(domain):
                response = input(f"Process {domain}? (y/n): ").lower().strip()
                if response == 'y':
                    domains_to_process.append(domain)
    
    # Run pipeline for each domain
    success = True
    for domain in domains_to_process:
        if not docs_by_domain.get(domain):
            print(f"Skipping {domain} - no documents found")
            continue
        
        doc_files = docs_by_domain[domain]
        config_path = update_config(domain, doc_files, None)
        
        if not run_pipeline(domain, config_path):
            success = False
    
    if success:
        count_results()
        print("\n✓ Processing completed successfully!")
    else:
        print("\n❌ Processing encountered errors")

if __name__ == '__main__':
    main()
