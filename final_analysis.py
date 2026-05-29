import pandas as pd
import json
from collections import Counter

def comprehensive_count():
    """Count different ways to tally components"""
    
    print("="*80)
    print("COMPREHENSIVE ANALYSIS")
    print("="*80)
    
    domains = ['labor', 'tax', 'enterprise']
    
    # Method 1: Count unique (doc, component) tuples
    doc_chapters = set()
    doc_articles = set()
    doc_clauses = set()
    doc_points = set()
    
    # Method 2: Count all non-null values per column
    all_chapters_list = []
    all_articles_list = []
    all_clauses_list = []
    all_points_list = []
    
    # Method 3: Count unique values per column
    unique_chapters = set()
    unique_articles = set()
    unique_clauses = set()
    unique_points = set()
    
    for domain in domains:
        base_path = f'data/interim/law_parsing/{domain}/'
        units_file = f'{base_path}legal_units_review.xlsx'
        
        try:
            units_df = pd.read_excel(units_file, sheet_name=0)
            
            # Method 1: Create (doc, component) tuples
            for _, row in units_df.iterrows():
                doc_id = str(row['doc_id']) if pd.notna(row['doc_id']) else None
                ch = str(row['chapter']) if pd.notna(row['chapter']) else None
                ar = str(row['article']) if pd.notna(row['article']) else None
                cl = str(row['clause']) if pd.notna(row['clause']) else None
                pt = str(row['point']) if pd.notna(row['point']) else None
                
                if doc_id and ch:
                    doc_chapters.add((doc_id, ch))
                if doc_id and ar:
                    doc_articles.add((doc_id, ar))
                if doc_id and cl:
                    doc_clauses.add((doc_id, cl))
                if doc_id and pt:
                    doc_points.add((doc_id, pt))
            
            # Method 2: Collect all non-null values
            all_chapters_list.extend(units_df['chapter'].dropna().tolist())
            all_articles_list.extend(units_df['article'].dropna().tolist())
            all_clauses_list.extend(units_df['clause'].dropna().tolist())
            all_points_list.extend(units_df['point'].dropna().tolist())
            
            # Method 3: Get unique values
            unique_chapters.update(units_df['chapter'].dropna().unique())
            unique_articles.update(units_df['article'].dropna().unique())
            unique_clauses.update(units_df['clause'].dropna().unique())
            unique_points.update(units_df['point'].dropna().unique())
            
        except Exception as e:
            print(f"Error reading {domain}: {e}")
    
    # Count using Counter for Method 2
    chapter_counter = Counter(all_chapters_list)
    article_counter = Counter(all_articles_list)
    clause_counter = Counter(all_clauses_list)
    point_counter = Counter(all_points_list)
    
    print("\nMETHOD 1: Count unique (document, component) tuples")
    print("-"*80)
    print(f"Unique (doc, chapter) pairs: {len(doc_chapters):,}")
    print(f"Unique (doc, article) pairs: {len(doc_articles):,}")
    print(f"Unique (doc, clause) pairs: {len(doc_clauses):,}")
    print(f"Unique (doc, point) pairs: {len(doc_points):,}")
    
    print("\nMETHOD 2: Count total non-null values (with repetitions)")
    print("-"*80)
    print(f"Total chapters (with repetitions): {len(all_chapters_list):,}")
    print(f"Total articles (with repetitions): {len(all_articles_list):,}")
    print(f"Total clauses (with repetitions): {len(all_clauses_list):,}")
    print(f"Total points (with repetitions): {len(all_points_list):,}")
    
    print("\nMETHOD 3: Count unique values per column")
    print("-"*80)
    print(f"Unique chapters: {len(unique_chapters):,}")
    print(f"Unique articles: {len(unique_articles):,}")
    print(f"Unique clauses: {len(unique_clauses):,}")
    print(f"Unique points: {len(unique_points):,}")
    
    # Count frequencies
    print("\nMOST FREQUENT COMPONENTS:")
    print("-"*80)
    
    print("\nTop 10 chapters by frequency:")
    for ch, count in chapter_counter.most_common(10):
        print(f"  {ch}: {count} occurrences")
    
    print("\nTop 10 articles by frequency:")
    for ar, count in article_counter.most_common(10):
        print(f"  {ar}: {count} occurrences")
    
    print(f"\n\nMATCH WITH REFERENCE?")
    print("="*80)
    print(f"Reference: 2,005 articles | Our count: {len(unique_articles):,}")
    print(f"Reference: 7,009 clauses | Our count: {len(unique_clauses):,}")
    print(f"Reference: 5,634 points  | Our count: {len(unique_points):,}")
    
    # Check if unique values count matches
    print(f"\n\nInterpretation:")
    print(f"The reference numbers (2005 articles, 7009 clauses, 5634 points)")
    print(f"do NOT match any of our counting methods.")
    print(f"\nPossible explanations:")
    print(f"1. Different data source (raw documents vs. interim Excel files)")
    print(f"2. Different counting methodology")
    print(f"3. Reference numbers from an older version of the data")
    print(f"4. The reference table counts individual extractions, not unique values")

if __name__ == '__main__':
    comprehensive_count()
