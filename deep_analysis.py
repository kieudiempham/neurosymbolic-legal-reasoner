import pandas as pd
import json
from pathlib import Path
from collections import Counter, defaultdict

def deep_analysis():
    """Deep analysis counting all components"""
    
    print("="*80)
    print("COMPREHENSIVE COMPONENT COUNTING")
    print("="*80)
    
    domains = ['labor', 'tax', 'enterprise']
    
    # Count from interim legal_units_review
    print("\n1. FROM INTERIM DATA (legal_units_review.xlsx)")
    print("-"*80)
    
    total_rows = 0
    total_unique_docs = set()
    total_unique_chapters = set()
    total_unique_articles = set()
    total_unique_clauses = set()
    total_unique_points = set()
    
    all_chapter_article_pairs = set()
    all_article_clause_pairs = set()
    all_clause_point_pairs = set()
    
    for domain in domains:
        base_path = f'data/interim/law_parsing/{domain}/'
        units_file = f'{base_path}legal_units_review.xlsx'
        
        try:
            units_df = pd.read_excel(units_file, sheet_name=0)
            
            # Count rows
            num_rows = len(units_df)
            total_rows += num_rows
            
            # Extract unique values
            docs = set(units_df['doc_id'].dropna().unique())
            chapters = set(units_df['chapter'].dropna().unique())
            articles = set(units_df['article'].dropna().unique())
            clauses = set(units_df['clause'].dropna().unique())
            points = set(units_df['point'].dropna().unique())
            
            total_unique_docs.update(docs)
            total_unique_chapters.update(chapters)
            total_unique_articles.update(articles)
            total_unique_clauses.update(clauses)
            total_unique_points.update(points)
            
            # Count pairs for inter-section relations
            for _, row in units_df.iterrows():
                doc = str(row['doc_id']) if pd.notna(row['doc_id']) else None
                ch = str(row['chapter']) if pd.notna(row['chapter']) else None
                ar = str(row['article']) if pd.notna(row['article']) else None
                cl = str(row['clause']) if pd.notna(row['clause']) else None
                pt = str(row['point']) if pd.notna(row['point']) else None
                
                if doc and ch and ar:
                    all_chapter_article_pairs.add((doc, ch, ar))
                if doc and ar and cl:
                    all_article_clause_pairs.add((doc, ar, cl))
                if doc and cl and pt:
                    all_clause_point_pairs.add((doc, cl, pt))
            
            print(f"\n{domain.upper()}:")
            print(f"  Rows: {num_rows}")
            print(f"  Unique documents: {len(docs)}")
            print(f"  Unique chapters: {len(chapters)}")
            print(f"  Unique articles: {len(articles)}")
            print(f"  Unique clauses: {len(clauses)}")
            print(f"  Unique points: {len(points)}")
            
        except Exception as e:
            print(f"\nError reading {domain}: {e}")
    
    print(f"\n\nTOTAL FROM INTERIM DATA:")
    print(f"  Total rows processed: {total_rows}")
    print(f"  Unique documents: {len(total_unique_docs)}")
    print(f"  Unique chapters: {len(total_unique_chapters)}")
    print(f"  Unique articles: {len(total_unique_articles)}")
    print(f"  Unique clauses: {len(total_unique_clauses)}")
    print(f"  Unique points: {len(total_unique_points)}")
    print(f"  Chapter-Article relations: {len(all_chapter_article_pairs)}")
    print(f"  Article-Clause relations: {len(all_article_clause_pairs)}")
    print(f"  Clause-Point relations: {len(all_clause_point_pairs)}")
    
    # Now load processed statute packs
    print(f"\n\n2. FROM PROCESSED DATA (statute_packs/*.jsonl)")
    print("-"*80)
    
    import glob
    
    processed_docs = set()
    processed_chapters = set()
    processed_articles = set()
    processed_clauses = set()
    processed_points = set()
    processed_relations = set()
    
    statute_files = glob.glob('data/processed/rulebase/*/canonical/statute_packs/*.jsonl')
    
    for filepath in statute_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        rule = json.loads(line)
                        doc = rule.get('source_doc', '')
                        if doc:
                            processed_docs.add(doc)
                        
                        source_article = rule.get('source_article', '')
                        if source_article:
                            parts = source_article.split('|')
                            cur_doc = doc
                            cur_ch = None
                            cur_ar = None
                            cur_cl = None
                            cur_pt = None
                            
                            for part in parts:
                                if part.startswith('chapter='):
                                    cur_ch = part.split('=')[1]
                                    if cur_ch:
                                        processed_chapters.add(cur_ch)
                                elif part.startswith('article='):
                                    cur_ar = part.split('=')[1]
                                    if cur_ar:
                                        processed_articles.add(cur_ar)
                                elif part.startswith('clause='):
                                    cur_cl = part.split('=')[1]
                                    if cur_cl:
                                        processed_clauses.add(cur_cl)
                                elif part.startswith('point='):
                                    cur_pt = part.split('=')[1]
                                    if cur_pt:
                                        processed_points.add(cur_pt)
                            
                            if cur_ch and cur_ar:
                                processed_relations.add(f"{cur_doc}|{cur_ch}|{cur_ar}")
                            if cur_ar and cur_cl:
                                processed_relations.add(f"{cur_ar}|{cur_cl}")
                            if cur_cl and cur_pt:
                                processed_relations.add(f"{cur_cl}|{cur_pt}")
                    
                    except json.JSONDecodeError:
                        continue
    
    print(f"  Documents: {len(processed_docs)}")
    print(f"  Chapters: {len(processed_chapters)}")
    print(f"  Articles: {len(processed_articles)}")
    print(f"  Clauses: {len(processed_clauses)}")
    print(f"  Points: {len(processed_points)}")
    print(f"  Inter-section relations: {len(processed_relations)}")
    
    # Summary comparison
    print(f"\n\nCOMPARISON:")
    print("="*80)
    print(f"{'Component':<30} {'Reference':<20} {'Interim':<15} {'Processed':<15}")
    print("-"*80)
    print(f"{'Legal documents':<30} {'13':<20} {len(total_unique_docs):<15} {len(processed_docs):<15}")
    print(f"{'Chapters':<30} {'125':<20} {len(total_unique_chapters):<15} {len(processed_chapters):<15}")
    print(f"{'Articles':<30} {'2,005':<20} {len(total_unique_articles):<15} {len(processed_articles):<15}")
    print(f"{'Clauses (Khoản)':<30} {'7,009':<20} {len(total_unique_clauses):<15} {len(processed_clauses):<15}")
    print(f"{'Points (Điểm)':<30} {'5,634':<20} {len(total_unique_points):<15} {len(processed_points):<15}")
    print(f"{'Inter-section relations':<30} {'2,031':<20} {'N/A':<15} {len(processed_relations):<15}")

if __name__ == '__main__':
    deep_analysis()
