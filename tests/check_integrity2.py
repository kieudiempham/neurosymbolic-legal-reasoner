import pandas as pd
from pathlib import Path

print('=== DATA INTEGRITY CHECK (PART 2) ===\n')

for domain in ['labor', 'tax', 'enterprise']:
    path = Path(f'data/interim/law_parsing/{domain}/legal_units_review.xlsx')
    if path.exists():
        df = pd.read_excel(path)
        print(f'\n{domain.upper()}:')
        
        # Check if same article appears in multiple documents
        unique_combos = df[['doc_id', 'chapter', 'article']].drop_duplicates()
        print(f'  Unique (doc, chapter, article) combos: {len(unique_combos)}')
        
        # Count how many times each unique article appears across documents
        article_doc_count = df[df['article'].notna()].groupby('article')['doc_id'].nunique()
        multi_doc_articles = article_doc_count[article_doc_count > 1]
        
        print(f'  Articles appearing in multiple documents: {len(multi_doc_articles)}')
        if len(multi_doc_articles) > 0:
            print(f'    Examples: {dict(multi_doc_articles.head(10))}')
        
        # Check actual text content
        print(f'\n  Sample text from different rows:')
        sample_df = df[df['article'].notna()].head(5)
        for idx, row in sample_df.iterrows():
            doc_id = row['doc_id']
            article = row['article']
            text = row['text'][:60] if pd.notna(row['text']) else 'N/A'
            print(f'    Doc {doc_id}, Article {article}: {text}...')

# Check the actual numbers
print('\n\n=== COMPARING INTERIM VS FINAL REPORT ===\n')

interim_stats = {}
for domain in ['labor', 'tax', 'enterprise']:
    path = Path(f'data/interim/law_parsing/{domain}/legal_units_review.xlsx')
    if path.exists():
        df = pd.read_excel(path)
        interim_stats[domain] = {
            'unique_articles': df['article'].nunique(),
            'unique_clauses': df['clause'].nunique(),
            'unique_points': df['point'].nunique(),
            'rows': len(df)
        }

print('Interim stats by domain:')
total_articles = 0
total_clauses = 0
total_points = 0

for domain, stats in interim_stats.items():
    print(f'\n{domain.upper()}:')
    print(f'  Unique articles: {stats["unique_articles"]}')
    print(f'  Unique clauses: {stats["unique_clauses"]}')
    print(f'  Unique points: {stats["unique_points"]}')
    print(f'  Total rows: {stats["rows"]}')
    
    total_articles += stats['unique_articles']
    total_clauses += stats['unique_clauses']
    total_points += stats['unique_points']

print(f'\n\nSum of unique per domain:')
print(f'  Articles: {total_articles} (but final report shows 282)')
print(f'  Clauses: {total_clauses} (but final report shows 40)')
print(f'  Points: {total_points} (but final report shows 21)')

print(f'\n⚠️ ISSUE: Adding unique articles from each domain: 220 + 62 + 218 = 500')
print(f'   But final report only shows 282 unique articles across all')
print(f'   This means many articles are REPEATED across domains!')
