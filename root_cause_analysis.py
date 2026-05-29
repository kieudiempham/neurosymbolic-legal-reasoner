import pandas as pd
from pathlib import Path

print('=== ROOT CAUSE ANALYSIS ===\n')

for domain in ['labor', 'tax', 'enterprise']:
    path = Path(f'data/interim/law_parsing/{domain}/legal_units_review.xlsx')
    if path.exists():
        df = pd.read_excel(path)
        print(f'\n{domain.upper()}:')
        
        # KEY INSIGHT: Count (doc, article, clause) TRIPLES not just (doc, clause) pairs
        df_clause = df[df['clause'].notna()].copy()
        
        # Count unique (doc, article, clause) triples
        triple_clause = df_clause[['doc_id', 'article', 'clause']].drop_duplicates()
        print(f'  (Doc, Article, Clause) TRIPLES: {len(triple_clause)}')
        
        # Count unique (doc, article, clause, point) quads
        df_point = df[df['point'].notna()].copy()
        quad_point = df_point[['doc_id', 'article', 'clause', 'point']].drop_duplicates()
        print(f'  (Doc, Article, Clause, Point) QUADS: {len(quad_point)}')
        
        # Check rows with same (doc, article, clause) but different text
        # This indicates duplicate segmentation
        duplicate_triples = df_clause.groupby(['doc_id', 'article', 'clause']).size()
        dup_count = (duplicate_triples > 1).sum()
        print(f'\n  (Doc, Article, Clause) with MULTIPLE ROWS: {dup_count}')
        if dup_count > 0:
            print(f'    Max rows per triple: {duplicate_triples.max()}')
            print(f'    Total extra rows (duplicates): {(duplicate_triples - 1).sum()}')
        
        # Same for points
        if len(df_point) > 0:
            duplicate_quads = df_point.groupby(['doc_id', 'article', 'clause', 'point']).size()
            dup_count_point = (duplicate_quads > 1).sum()
            print(f'\n  (Doc, Article, Clause, Point) with MULTIPLE ROWS: {dup_count_point}')
            if dup_count_point > 0:
                print(f'    Max rows per quad: {duplicate_quads.max()}')
                print(f'    Total extra rows (duplicates): {(duplicate_quads - 1).sum()}')
        
        # Check if there are clauses WITHOUT articles (should not happen)
        df_clause_only = df_clause[df_clause['article'].isna()]
        print(f'\n  Clauses WITHOUT articles: {len(df_clause_only)} rows')
        
        # Sample: show if multiple rows have same (doc, article, clause) but different text
        print(f'\n  Checking for actual duplicate clause content:')
        sample_dup = df_clause.groupby(['doc_id', 'article', 'clause']).filter(lambda x: len(x) > 1).head(10)
        if len(sample_dup) > 0:
            for idx, row in sample_dup.iterrows():
                doc = row['doc_id']
                art = row['article']
                cl = row['clause']
                text = row['text'][:50] if pd.notna(row['text']) else 'N/A'
                print(f'    {doc}, Article {art}, Clause {cl}: {text}...')
        else:
            print(f'    No duplicate (doc, article, clause) found')

print('\n\n=== ISSUE SUMMARY ===')
print('Current count (1160 articles, 341 clauses, 236 points) uses:')
print('  - (doc, article) pairs for articles')
print('  - (doc, clause) pairs for clauses')
print('  - (doc, point) pairs for points')
print('\nBUT this is WRONG because:')
print('  - Article 2 can appear in multiple documents')
print('  - Clause 1 can appear in MULTIPLE articles of the SAME document')
print('  - Example: Doc A, Article 2, Clause 1 vs Doc A, Article 3, Clause 1')
print('  - These are DIFFERENT but both have (doc="DocA", clause=1)')
print('\nWe should count:')
print('  - (doc, article, clause) TRIPLES for clauses')
print('  - (doc, article, clause, point) QUADS for points')
