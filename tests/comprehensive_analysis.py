import json
import glob
from pathlib import Path
from collections import defaultdict

def analyze_all_statutes():
    """Comprehensive analysis of statute packs"""
    
    legal_docs = set()
    chapters = set()
    articles = set()
    clauses = set()  # khoản
    points = set()   # điểm
    relations = set()  # inter-section relations
    
    domains = ['labor', 'tax', 'enterprise']
    all_rules = []
    
    for domain in domains:
        statute_dir = f'data/processed/rulebase/{domain}/canonical/statute_packs/'
        statute_files = glob.glob(f'{statute_dir}*.jsonl')
        
        for filepath in sorted(statute_files):
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            rule = json.loads(line)
                            all_rules.append(rule)
                            
                            # Extract source document
                            doc = rule.get('source_doc', '')
                            if doc:
                                legal_docs.add(doc)
                            
                            # Parse source_article field
                            source_article = rule.get('source_article', '')
                            if source_article:
                                parts = source_article.split('|')
                                
                                current_chapter = None
                                current_article = None
                                current_clause = None
                                current_point = None
                                
                                for part in parts:
                                    if part.startswith('chapter='):
                                        current_chapter = part.split('=')[1]
                                        if current_chapter:
                                            chapters.add(f"{doc}|{current_chapter}")
                                    elif part.startswith('article='):
                                        current_article = part.split('=')[1]
                                        if current_article:
                                            articles.add(f"{doc}|{current_article}")
                                    elif part.startswith('clause='):
                                        current_clause = part.split('=')[1]
                                        if current_clause:
                                            clauses.add(f"{doc}|{current_article}|{current_clause}")
                                    elif part.startswith('point='):
                                        current_point = part.split('=')[1]
                                        if current_point:
                                            points.add(f"{doc}|{current_article}|{current_clause}|{current_point}")
                                
                                # Create inter-section relations (article -> clause -> point)
                                if current_article and current_clause:
                                    relations.add(f"{doc}|{current_article}|{current_clause}")
                                if current_clause and current_point:
                                    relations.add(f"{doc}|{current_clause}|{current_point}")
                        except json.JSONDecodeError:
                            continue
    
    print("="*80)
    print("STATUTE EXTRACTION ANALYSIS")
    print("="*80)
    print(f"\nNo. | Component Type              | Quantity")
    print("-" * 50)
    print(f"1   | Legal documents             | {len(legal_docs):,}")
    print(f"2   | Chapters                    | {len(chapters):,}")
    print(f"3   | Articles                    | {len(articles):,}")
    print(f"4   | Clauses (Khoản)             | {len(clauses):,}")
    print(f"5   | Points (Điểm)               | {len(points):,}")
    print(f"6   | Inter-section relations     | {len(relations):,}")
    print("-" * 50)
    
    print(f"\n\nDETAILED BREAKDOWN BY DOMAIN:")
    print("="*80)
    
    for domain in domains:
        statute_dir = f'data/processed/rulebase/{domain}/canonical/statute_packs/'
        statute_files = glob.glob(f'{statute_dir}*.jsonl')
        
        domain_docs = set()
        domain_chapters = set()
        domain_articles = set()
        domain_clauses = set()
        domain_points = set()
        
        for filepath in sorted(statute_files):
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            rule = json.loads(line)
                            doc = rule.get('source_doc', '')
                            if doc:
                                domain_docs.add(doc)
                            
                            source_article = rule.get('source_article', '')
                            if source_article:
                                parts = source_article.split('|')
                                current_article = None
                                current_clause = None
                                
                                for part in parts:
                                    if part.startswith('chapter='):
                                        ch = part.split('=')[1]
                                        if ch:
                                            domain_chapters.add(f"{doc}|{ch}")
                                    elif part.startswith('article='):
                                        current_article = part.split('=')[1]
                                        if current_article:
                                            domain_articles.add(f"{doc}|{current_article}")
                                    elif part.startswith('clause='):
                                        current_clause = part.split('=')[1]
                                        if current_clause:
                                            domain_clauses.add(f"{doc}|{current_article}|{current_clause}")
                                    elif part.startswith('point='):
                                        pt = part.split('=')[1]
                                        if pt:
                                            domain_points.add(f"{doc}|{current_article}|{current_clause}|{pt}")
                        except json.JSONDecodeError:
                            continue
        
        print(f"\n{domain.upper()}:")
        print(f"  Documents: {len(domain_docs):,}")
        print(f"  Chapters:  {len(domain_chapters):,}")
        print(f"  Articles:  {len(domain_articles):,}")
        print(f"  Clauses:   {len(domain_clauses):,}")
        print(f"  Points:    {len(domain_points):,}")
    
    # List unique legal documents
    print(f"\n\nUNIQUE LEGAL DOCUMENTS ({len(legal_docs)}):")
    print("="*80)
    for doc in sorted(legal_docs):
        print(f"  - {doc}")

if __name__ == '__main__':
    analyze_all_statutes()
