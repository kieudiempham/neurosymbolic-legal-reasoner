import pandas as pd
import os
from datetime import datetime

def check_interim_details():
    """Check details of interim data"""
    
    print("="*80)
    print("DETAILED INTERIM DATA INSPECTION")
    print("="*80)
    
    domains = ['labor', 'tax', 'enterprise']
    
    for domain in domains:
        base_path = f'data/interim/law_parsing/{domain}/'
        units_file = f'{base_path}legal_units_review.xlsx'
        
        if os.path.exists(units_file):
            stat = os.stat(units_file)
            mod_time = datetime.fromtimestamp(stat.st_mtime)
            
            df = pd.read_excel(units_file)
            
            print(f"\n{domain.upper()}:")
            print(f"  File size: {stat.st_size:,} bytes")
            print(f"  Last modified: {mod_time}")
            print(f"  Total rows: {len(df):,}")
            
            # Count non-null values for each component column
            docs = df['doc_id'].notna().sum()
            chapters = df['chapter'].notna().sum()
            articles = df['article'].notna().sum()
            clauses = df['clause'].notna().sum()
            points = df['point'].notna().sum()
            
            print(f"  Rows with doc_id: {docs:,}")
            print(f"  Rows with chapter: {chapters:,}")
            print(f"  Rows with article: {articles:,}")
            print(f"  Rows with clause: {clauses:,}")
            print(f"  Rows with point: {points:,}")
            
            # Show sample rows
            print(f"\n  Sample rows:")
            print(df[['doc_id', 'chapter', 'article', 'clause', 'point', 'text']].head(3).to_string())
    
    print(f"\n{'='*80}")
    print("AGGREGATED STATISTICS:")
    print(f"{'='*80}")
    
    # Recalculate total statistics
    all_docs = set()
    all_chapters = set()
    all_articles = set()
    all_clauses = set()
    all_points = set()
    
    for domain in domains:
        base_path = f'data/interim/law_parsing/{domain}/'
        units_file = f'{base_path}legal_units_review.xlsx'
        
        if os.path.exists(units_file):
            df = pd.read_excel(units_file)
            all_docs.update(df['doc_id'].dropna().unique())
            all_chapters.update(df['chapter'].dropna().unique())
            all_articles.update(df['article'].dropna().unique())
            all_clauses.update(df['clause'].dropna().unique())
            all_points.update(df['point'].dropna().unique())
    
    print(f"\nTotal unique documents: {len(all_docs)}")
    print(f"Total unique chapters: {len(all_chapters)}")
    print(f"Total unique articles: {len(all_articles)}")
    print(f"Total unique clauses: {len(all_clauses)}")
    print(f"Total unique points: {len(all_points)}")
    
    print(f"\n\nUnique chapter values: {sorted(all_chapters)}")
    print(f"\nUnique article values (first 20): {sorted(all_articles)[:20]}")
    print(f"\nUnique clause values: {sorted(all_clauses)}")
    print(f"\nUnique point values: {sorted(all_points)}")

if __name__ == '__main__':
    check_interim_details()
