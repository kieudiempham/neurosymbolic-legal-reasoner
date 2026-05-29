import pandas as pd
from pathlib import Path

print('=== DETAILED COMPONENT ANALYSIS ===\n')

for domain in ['labor', 'tax', 'enterprise']:
    path = Path(f'data/interim/law_parsing/{domain}/legal_units_review.xlsx')
    if path.exists():
        df = pd.read_excel(path)
        print(f'{domain.upper()}:')
        print(f'  Total rows: {len(df)}')
        
        # Count non-null values
        chapters_count = df['chapter'].notna().sum()
        chapters_unique = df['chapter'].nunique()
        articles_count = df['article'].notna().sum()
        articles_unique = df['article'].nunique()
        clauses_count = df['clause'].notna().sum()
        clauses_unique = df['clause'].nunique()
        points_count = df['point'].notna().sum()
        points_unique = df['point'].nunique()
        
        print(f'  Chapters (non-null): {chapters_count}, Unique: {chapters_unique}')
        print(f'  Articles (non-null): {articles_count}, Unique: {articles_unique}')
        print(f'  Clauses (non-null): {clauses_count}, Unique: {clauses_unique}')
        print(f'  Points (non-null): {points_count}, Unique: {points_unique}')
        
        # Sample data
        ch_samples = df['chapter'].unique()[:5].tolist()
        art_df = df[df['article'].notna()]
        if len(art_df) > 0:
            art_samples = art_df['article'].unique()[:10].tolist()
            print(f'\n  Sample articles: {art_samples}')
        
        # Check structure of a few rows
        print(f'\n  Sample rows (first 3):')
        for idx, row in df.head(3).iterrows():
            ch = row['chapter']
            art = row['article']
            cl = row['clause']
            pt = row['point']
            ut = row['unit_type']
            print(f'    Row {idx}: chapter={ch}, article={art}, clause={cl}, point={pt}, unit_type={ut}')
        print()

# Check if extraction is working correctly
print('\n=== CHECKING EXTRACTION QUALITY ===\n')

for domain in ['labor', 'tax', 'enterprise']:
    path = Path(f'data/interim/law_parsing/{domain}/legal_units_review.xlsx')
    if path.exists():
        df = pd.read_excel(path)
        
        # Calculate coverage
        dieu_coverage = (df['article'].notna().sum() / len(df)) * 100
        khoan_coverage = (df['clause'].notna().sum() / len(df)) * 100
        diem_coverage = (df['point'].notna().sum() / len(df)) * 100
        
        print(f'{domain.upper()} Coverage:')
        print(f'  Articles extracted: {dieu_coverage:.1f}% of rows')
        print(f'  Clauses extracted: {khoan_coverage:.1f}% of rows')
        print(f'  Points extracted: {diem_coverage:.1f}% of rows')
        
        # Check unit types
        unit_types = df['unit_type'].value_counts()
        print(f'  Unit types distribution:')
        for ut, count in unit_types.items():
            print(f'    {ut}: {count}')
        print()
