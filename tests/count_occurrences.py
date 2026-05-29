import pandas as pd
import json
from pathlib import Path
from collections import Counter

def count_all_occurrences():
    """Count all occurrences of each component (not just unique)"""
    
    print("="*80)
    print("COUNTING ALL OCCURRENCES (Including duplicates)")
    print("="*80)
    
    domains = ['labor', 'tax', 'enterprise']
    
    total_all_chapters = 0
    total_all_articles = 0
    total_all_clauses = 0
    total_all_points = 0
    
    total_unique_docs = set()
    
    for domain in domains:
        base_path = f'data/interim/law_parsing/{domain}/'
        units_file = f'{base_path}legal_units_review.xlsx'
        
        try:
            units_df = pd.read_excel(units_file, sheet_name=0)
            
            # Count all occurrences (including NaN will reduce count)
            chapters_count = units_df['chapter'].notna().sum()
            articles_count = units_df['article'].notna().sum()
            clauses_count = units_df['clause'].notna().sum()
            points_count = units_df['point'].notna().sum()
            
            # Also count unique docs
            docs = set(units_df['doc_id'].dropna().unique())
            total_unique_docs.update(docs)
            
            total_all_chapters += chapters_count
            total_all_articles += articles_count
            total_all_clauses += clauses_count
            total_all_points += points_count
            
            print(f"\n{domain.upper()}:")
            print(f"  Documents: {len(docs)}")
            print(f"  Total chapter occurrences: {chapters_count}")
            print(f"  Total article occurrences: {articles_count}")
            print(f"  Total clause occurrences: {clauses_count}")
            print(f"  Total point occurrences: {points_count}")
            
        except Exception as e:
            print(f"Error reading {domain}: {e}")
    
    print(f"\n{'='*80}")
    print("TOTAL (ALL OCCURRENCES):")
    print(f"{'='*80}")
    print(f"Unique documents: {len(total_unique_docs)}")
    print(f"Total chapter occurrences: {total_all_chapters:,}")
    print(f"Total article occurrences: {total_all_articles:,}")
    print(f"Total clause occurrences: {total_all_clauses:,}")
    print(f"Total point occurrences: {total_all_points:,}")
    
    print(f"\n{'='*80}")
    print("COMPARISON WITH REFERENCE:")
    print(f"{'='*80}")
    print(f"{'Component':<30} {'Reference':<15} {'Our Count':<15} {'Ratio':<15}")
    print("-"*80)
    
    ref_docs = 13
    ref_chapters = 125
    ref_articles = 2005
    ref_clauses = 7009
    ref_points = 5634
    
    print(f"{'Documents':<30} {ref_docs:<15} {len(total_unique_docs):<15} {len(total_unique_docs)/ref_docs:.1%}")
    print(f"{'Chapters':<30} {ref_chapters:<15} {total_all_chapters:<15} {total_all_chapters/ref_chapters:.1%}")
    print(f"{'Articles':<30} {ref_articles:<15} {total_all_articles:<15} {total_all_articles/ref_articles:.1%}")
    print(f"{'Clauses':<30} {ref_clauses:<15} {total_all_clauses:<15} {total_all_clauses/ref_clauses:.1%}")
    print(f"{'Points':<30} {ref_points:<15} {total_all_points:<15} {total_all_points/ref_points:.1%}")
    
    # Maybe the reference counts are from raw documents?
    print(f"\n\nLet's check raw document files...")
    
    raw_files = []
    import glob
    raw_labor = glob.glob('data/raw/legal_corpus/labor/*.pdf')
    raw_tax = glob.glob('data/raw/legal_corpus/tax/*.pdf')
    raw_enterprise = glob.glob('data/raw/legal_corpus/enterprise/*.pdf')
    
    print(f"\nRaw files found:")
    print(f"  Labor: {len(raw_labor)} PDFs")
    print(f"  Tax: {len(raw_tax)} PDFs")
    print(f"  Enterprise: {len(raw_enterprise)} PDFs")
    print(f"  Total: {len(raw_labor) + len(raw_tax) + len(raw_enterprise)} documents")

if __name__ == '__main__':
    count_all_occurrences()
