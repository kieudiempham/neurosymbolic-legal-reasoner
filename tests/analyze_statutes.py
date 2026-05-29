import json
import glob
from pathlib import Path

def analyze_statute_pack(filepath):
    """Analyze a statute pack file to count chapters, articles, and points"""
    chapters = set()
    articles = set()
    points = set()
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        rule = json.loads(line)
                        source_article = rule.get('source_article', '')
                        
                        # Parse the source_article field
                        if source_article:
                            parts = source_article.split('|')
                            for part in parts:
                                if part.startswith('chapter='):
                                    chapter = part.split('=')[1]
                                    if chapter:  # Only add non-empty
                                        chapters.add(chapter)
                                elif part.startswith('article='):
                                    article = part.split('=')[1]
                                    if article:
                                        articles.add(int(article))
                                elif part.startswith('point='):
                                    point = part.split('=')[1]
                                    if point:  # Only add non-empty
                                        points.add(point)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None
    
    return {
        'chapters': sorted(chapters),
        'articles': sorted(articles),
        'points': sorted(points),
        'num_chapters': len(chapters),
        'num_articles': len(articles),
        'num_points': len(points)
    }

# Get all statute packs from all domains
domains = ['labor', 'tax', 'enterprise']
results = {}

for domain in domains:
    statute_dir = f'data/processed/rulebase/{domain}/canonical/statute_packs/'
    statute_files = glob.glob(f'{statute_dir}*.jsonl')
    
    if statute_files:
        print(f"\n{'='*80}")
        print(f"DOMAIN: {domain.upper()}")
        print(f"{'='*80}")
        
        domain_results = {}
        for filepath in sorted(statute_files):
            filename = Path(filepath).name
            doc_code = filename.replace('statute_pack_', '').replace('.jsonl', '')
            
            analysis = analyze_statute_pack(filepath)
            if analysis:
                domain_results[doc_code] = analysis
                print(f"\n📄 {doc_code}")
                print(f"   Chương (Chapters): {analysis['num_chapters']} - {analysis['chapters']}")
                print(f"   Điều (Articles): {analysis['num_articles']} - {analysis['articles']}")
                print(f"   Điểm (Points): {analysis['num_points']} - {analysis['points']}")
        
        results[domain] = domain_results

print(f"\n\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")
for domain, docs in results.items():
    print(f"\n{domain.upper()}:")
    for doc, analysis in docs.items():
        print(f"  {doc}: {analysis['num_chapters']} chapters, {analysis['num_articles']} articles, {analysis['num_points']} points")
