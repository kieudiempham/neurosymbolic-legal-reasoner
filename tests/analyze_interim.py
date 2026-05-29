import pandas as pd
import glob
from pathlib import Path
from collections import defaultdict

def count_legal_components():
    """Count legal components from interim Excel files"""
    
    print("="*80)
    print("COUNTING LEGAL COMPONENTS FROM INTERIM LAW PARSING")
    print("="*80)
    
    domains = ['labor', 'tax', 'enterprise']
    all_documents = set()
    all_chapters = set()
    all_articles = set()
    all_clauses = set()
    all_points = set()
    all_relations = set()
    
    domain_stats = {}
    
    for domain in domains:
        base_path = f'data/interim/law_parsing/{domain}/'
        
        # Read legal_units_review.xlsx to get document structure
        units_file = f'{base_path}legal_units_review.xlsx'
        
        try:
            units_df = pd.read_excel(units_file, sheet_name=0)
            
            domain_docs = set()
            domain_chapters = set()
            domain_articles = set()
            domain_clauses = set()
            domain_points = set()
            
            print(f"\n{domain.upper()}:")
            print(f"  legal_units_review.xlsx shape: {units_df.shape}")
            
            # Analyze columns
            if 'document' in units_df.columns or 'doc_id' in units_df.columns or 'Document' in units_df.columns:
                doc_col = next((col for col in units_df.columns if 'doc' in col.lower()), None)
                if doc_col:
                    domain_docs.update(units_df[doc_col].dropna().unique())
                    all_documents.update(domain_docs)
            
            if 'chapter' in units_df.columns or 'Chapter' in units_df.columns:
                chapter_col = next((col for col in units_df.columns if 'chapter' in col.lower()), None)
                if chapter_col:
                    domain_chapters.update(units_df[chapter_col].dropna().unique())
                    all_chapters.update(domain_chapters)
            
            if 'article' in units_df.columns or 'Article' in units_df.columns:
                article_col = next((col for col in units_df.columns if 'article' in col.lower()), None)
                if article_col:
                    domain_articles.update(units_df[article_col].dropna().unique())
                    all_articles.update(domain_articles)
            
            if 'clause' in units_df.columns or 'Clause' in units_df.columns or 'khoản' in units_df.columns:
                clause_col = next((col for col in units_df.columns if 'clause' in col.lower() or 'khoản' in col.lower()), None)
                if clause_col:
                    domain_clauses.update(units_df[clause_col].dropna().unique())
                    all_clauses.update(domain_clauses)
            
            if 'point' in units_df.columns or 'Point' in units_df.columns or 'điểm' in units_df.columns:
                point_col = next((col for col in units_df.columns if 'point' in col.lower() or 'điểm' in col.lower()), None)
                if point_col:
                    domain_points.update(units_df[point_col].dropna().unique())
                    all_points.update(domain_points)
            
            print(f"  Columns: {list(units_df.columns)}")
            print(f"  Documents: {len(domain_docs)}")
            print(f"  Chapters: {len(domain_chapters)}")
            print(f"  Articles: {len(domain_articles)}")
            print(f"  Clauses: {len(domain_clauses)}")
            print(f"  Points: {len(domain_points)}")
            
            domain_stats[domain] = {
                'docs': len(domain_docs),
                'chapters': len(domain_chapters),
                'articles': len(domain_articles),
                'clauses': len(domain_clauses),
                'points': len(domain_points),
                'rows': len(units_df)
            }
            
        except Exception as e:
            print(f"  Error reading {units_file}: {e}")
    
    print(f"\n{'='*80}")
    print("TOTAL FROM INTERIM DATA:")
    print(f"{'='*80}")
    print(f"Documents: {len(all_documents)}")
    print(f"Chapters: {len(all_chapters)}")
    print(f"Articles: {len(all_articles)}")
    print(f"Clauses: {len(all_clauses)}")
    print(f"Points: {len(all_points)}")
    
    return domain_stats

if __name__ == '__main__':
    count_legal_components()
