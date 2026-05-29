import pandas as pd
from pathlib import Path
import json

print('=== CHECKING DATA INTEGRITY ===\n')

# Check if same article appears in multiple documents/chapters
for domain in ['labor', 'tax', 'enterprise']:
    path = Path(f'data/interim/law_parsing/{domain}/legal_units_review.xlsx')
    if path.exists():
        df = pd.read_excel(path)
        print(f'\n{domain.upper()}:')
        
        # Get unique (doc_id, chapter, article) combinations
        unique_combos = df[['doc_id', 'chapter', 'article']].drop_duplicates()
        print(f'  Unique (doc, chapter, article) combos: {len(unique_combos)}')
        
        # Count how many times each unique article appears
        article_counts = df[df['article'].notna()].groupby('article')['doc_id'].nunique()
        multi_doc_articles = article_counts[article_counts > 1]
        
        print(f'  Articles appearing in multiple docs: {len(multi_doc_articles)}')
        if len(multi_doc_articles) > 0:
            print(f'    Examples: {multi_doc_articles.head().to_dict()}')
        
        # Check for duplicate rows with same doc_id + article + clause + point
        dup_check = df.groupby(['doc_id', 'article', 'clause', 'point']).size()
        duplicate_rows = (dup_check > 1).sum()
        print(f'  Duplicate (doc, article, clause, point) rows: {duplicate_rows}')
        
        # Check processed data
        processed_path = Path(f'data/processed/rulebase/{domain}/canonical_rules.jsonl')
        if processed_path.exists():
            with open(processed_path) as f:
                rules = [json.loads(line) for line in f]
            print(f'  Canonical rules extracted: {len(rules)}')
            
            # Sample a rule to see structure
            if rules:
                sample = rules[0]
                print(f'  Sample rule structure:')
                print(f'    Keys: {list(sample.keys())}')
                print(f'    Statute: {sample.get("statute_code", "N/A")}')
                print(f'    Subject: {sample.get("subject", "N/A")[:50] if sample.get("subject") else "N/A"}...')

# Check final_report.py calculation logic
print('\n\n=== CHECKING FINAL REPORT LOGIC ===\n')

# Replicate what final_report.py does
all_chapters = set()
all_articles = set()
all_clauses = set()
all_points = set()
all_docs = set()

for domain in ['labor', 'tax', 'enterprise']:
    path = Path(f'data/interim/law_parsing/{domain}/legal_units_review.xlsx')
    if path.exists():
        df = pd.read_excel(path)
        all_docs.update(df['doc_id'].unique())
        all_chapters.update(df['chapter'].dropna().unique())
        all_articles.update(df['article'].dropna().unique())
        all_clauses.update(df['clause'].dropna().unique())
        all_points.update(df['point'].dropna().unique())

print(f'Total unique documents: {len(all_docs)}')
print(f'Total unique chapters: {len(all_chapters)}')
print(f'Total unique articles: {len(all_articles)}')
print(f'Total unique clauses: {len(all_clauses)}')
print(f'Total unique points: {len(all_points)}')

print(f'\nChapters: {sorted(all_chapters)}')
print(f'Articles (first 20): {sorted([x for x in all_articles if isinstance(x, int)])[:20]}')
print(f'Clauses (first 20): {sorted([x for x in all_clauses if isinstance(x, float)])[:20]}')
print(f'Points (first 20): {sorted(list(all_points))[:20]}')
