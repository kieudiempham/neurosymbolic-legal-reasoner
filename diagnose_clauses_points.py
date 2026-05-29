import pandas as pd
from pathlib import Path

print('=== DIAGNOSTIC: CLAUSES AND POINTS EXTRACTION ===\n')

for domain in ['labor', 'tax', 'enterprise']:
    path = Path(f'data/interim/law_parsing/{domain}/legal_units_review.xlsx')
    if path.exists():
        df = pd.read_excel(path)
        print(f'\n{domain.upper()}:')
        print(f'  Total rows: {len(df)}')
        
        # Check distribution
        print(f'\n  Unit type distribution:')
        unit_type_dist = df['unit_type'].value_counts()
        for ut, count in unit_type_dist.items():
            print(f'    {ut}: {count}')
        
        # Check if articles have clauses
        articles_with_clauses = df[df['clause'].notna()].groupby('article').size()
        articles_total = df['article'].nunique()
        print(f'\n  Articles with clauses: {len(articles_with_clauses)} out of {articles_total}')
        print(f'    Articles WITHOUT clauses: {articles_total - len(articles_with_clauses)}')
        
        # Check if clauses have points
        clauses_with_points = df[df['point'].notna()].groupby('clause').size()
        clauses_total = df['clause'].nunique()
        print(f'\n  Clauses with points: {len(clauses_with_points)} out of {clauses_total}')
        print(f'    Clauses WITHOUT points: {clauses_total - len(clauses_with_points)}')
        
        # Check average clauses per article
        df_with_article = df[df['article'].notna()].copy()
        df_with_article['has_clause'] = df_with_article['clause'].notna()
        avg_clauses_per_article = df_with_article.groupby('article')['has_clause'].sum() / articles_total
        print(f'\n  Average clauses per article: {avg_clauses_per_article.mean():.2f}')
        
        # Check average points per clause
        df_with_clause = df[df['clause'].notna()].copy()
        df_with_clause['has_point'] = df_with_clause['point'].notna()
        if clauses_total > 0:
            avg_points_per_clause = df_with_clause.groupby('clause')['has_point'].sum() / clauses_total
            print(f'  Average points per clause: {avg_points_per_clause.mean():.2f}')
        
        # Sample data
        print(f'\n  Sample rows with clause/point:')
        sample = df[df['clause'].notna()].head(5)
        for idx, row in sample.iterrows():
            print(f'    Doc: {row["doc_id"]}, Article: {row["article"]}, Clause: {row["clause"]}, Point: {row["point"]}, Type: {row["unit_type"]}')
        
        # Check for missing articles
        print(f'\n  Null value counts:')
        print(f'    Article: {df["article"].isna().sum()}')
        print(f'    Clause: {df["clause"].isna().sum()}')
        print(f'    Point: {df["point"].isna().sum()}')

print('\n\n=== EXPECTED RATIO CHECK ===')
print('If extraction is correct:')
print('  - Not all articles have clauses (some are simple paragraphs)')
print('  - Not all clauses have points (some are simple items)')
print('  - Expected ratio might be: 1 article : 0.3-0.5 clauses : 0.2-0.4 points')
print('\nActual ratio in dataset:')
print(f'  - Articles: 1160')
print(f'  - Clauses: 341 (ratio: {341/1160:.2%})')
print(f'  - Points: 236 (ratio: {236/1160:.2%})')
