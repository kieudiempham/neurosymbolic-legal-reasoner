import os
import glob
import json
from pathlib import Path
from collections import defaultdict, Counter
import re

def extract_from_raw_docs():
    """Extract structure information from raw document folders"""
    
    print("="*80)
    print("ANALYZING RAW DOCUMENTS AND INTERIM DATA")
    print("="*80)
    
    # Check what's in raw_legal_corpus
    raw_base = 'data/raw/legal_corpus/'
    
    domains = ['labor', 'tax', 'enterprise']
    
    all_docs = set()
    all_chapters_count = Counter()
    all_articles_count = Counter()
    all_clauses_count = Counter()
    all_points_count = Counter()
    
    # Count from interim data with more detail
    total_rows = 0
    doc_chapter_pairs = set()
    doc_article_pairs = set()
    doc_clause_pairs = set()
    doc_point_pairs = set()
    
    print("\nScanning INTERIM DATA (legal_units_review.xlsx):")
    print("-"*80)
    
    for domain in domains:
        interim_path = f'data/interim/law_parsing/{domain}/'
        units_file = f'{interim_path}legal_units_review.xlsx'
        
        if os.path.exists(units_file):
            import pandas as pd
            df = pd.read_excel(units_file)
            
            print(f"\n{domain.upper()}: {len(df)} rows")
            total_rows += len(df)
            
            for _, row in df.iterrows():
                doc = str(row['doc_id']) if pd.notna(row['doc_id']) else None
                ch = str(row['chapter']) if pd.notna(row['chapter']) else None
                ar = str(row['article']) if pd.notna(row['article']) else None
                cl = str(row['clause']) if pd.notna(row['clause']) else None
                pt = str(row['point']) if pd.notna(row['point']) else None
                
                if doc:
                    all_docs.add(doc)
                if ch:
                    all_chapters_count[ch] += 1
                if ar:
                    all_articles_count[ar] += 1
                if cl:
                    all_clauses_count[cl] += 1
                if pt:
                    all_points_count[pt] += 1
                
                if doc and ch:
                    doc_chapter_pairs.add((doc, ch))
                if doc and ar:
                    doc_article_pairs.add((doc, ar))
                if doc and cl:
                    doc_clause_pairs.add((doc, cl))
                if doc and pt:
                    doc_point_pairs.add((doc, pt))
    
    print(f"\n{'='*80}")
    print("SUMMARY OF EXTRACTED DATA:")
    print(f"{'='*80}")
    print(f"\nTotal rows processed: {total_rows:,}")
    print(f"Unique documents: {len(all_docs)}")
    
    print(f"\n{'COMPONENT':<25} {'Unique Values':<20} {'(doc, component) pairs':<25}")
    print("-"*70)
    print(f"{'Chapters':<25} {len(all_chapters_count):<20} {len(doc_chapter_pairs):<25}")
    print(f"{'Articles':<25} {len(all_articles_count):<20} {len(doc_article_pairs):<25}")
    print(f"{'Clauses (Khoản)':<25} {len(all_clauses_count):<20} {len(doc_clause_pairs):<25}")
    print(f"{'Points (Điểm)':<25} {len(all_points_count):<20} {len(doc_point_pairs):<25}")
    
    # Also count total occurrences
    total_chapters = sum(all_chapters_count.values())
    total_articles = sum(all_articles_count.values())
    total_clauses = sum(all_clauses_count.values())
    total_points = sum(all_points_count.values())
    
    print(f"\n{'COMPONENT':<25} {'Total Occurrences':<25}")
    print("-"*50)
    print(f"{'Chapters':<25} {total_chapters:,}")
    print(f"{'Articles':<25} {total_articles:,}")
    print(f"{'Clauses':<25} {total_clauses:,}")
    print(f"{'Points':<25} {total_points:,}")
    
    # List documents
    print(f"\n\nUNIQUE DOCUMENTS ({len(all_docs)}):")
    print("-"*80)
    for doc in sorted(all_docs):
        print(f"  {doc}")
    
    # Summary for paper
    print(f"\n\n{'='*80}")
    print("SUMMARY TABLE FOR YOUR PAPER:")
    print(f"{'='*80}")
    print(f"No. | Component Type              | Quantity")
    print("-"*50)
    print(f"1   | Legal documents             | {len(all_docs)}")
    print(f"2   | Chapters                    | {len(all_chapters_count)}")
    print(f"3   | Articles                    | {len(all_articles_count)}")
    print(f"4   | Clauses (Khoản)             | {len(all_clauses_count)}")
    print(f"5   | Points (Điểm)               | {len(all_points_count)}")
    
    # Inter-section relations
    inter_relations = len(doc_chapter_pairs) + len(doc_article_pairs) + len(doc_clause_pairs) + len(doc_point_pairs)
    print(f"6   | Inter-section relations     | {inter_relations}")
    
    return {
        'documents': len(all_docs),
        'chapters': len(all_chapters_count),
        'articles': len(all_articles_count),
        'clauses': len(all_clauses_count),
        'points': len(all_points_count),
        'relations': inter_relations
    }

if __name__ == '__main__':
    stats = extract_from_raw_docs()
