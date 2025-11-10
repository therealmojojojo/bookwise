#!/usr/bin/env python3
"""
Analyze Calibre Awards - Detailed Breakdown
Creates detailed CSVs showing owned and missing books by award/list
"""

import csv
import sqlite3
import json
from pathlib import Path
from collections import defaultdict
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.normalizers import normalize_title, normalize_author
from src.utils.title_variants import get_all_title_variants
from src.config.settings import settings

def load_title_variants_from_json():
    """
    Load title variants from original JSON sources
    Returns dict: {normalized_key: [list of title variants]}
    """
    variants_map = {}
    datasources_dir = Path(settings.DATASOURCES_DIR)
    
    # Load all JSON award files
    for json_file in datasources_dir.glob('*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            items = data.get('items', [])
            for item in items:
                title = item.get('title', '')
                author = item.get('author', '')
                if not title or not author:
                    continue
                
                # Get all title variants
                variants = get_all_title_variants(
                    title=title,
                    alternate_titles=item.get('alternate_titles', []),
                    notes=item.get('notes', '')
                )
                
                # Store variants for each normalized key
                for variant in variants:
                    key = normalize_title(variant, author)
                    if key not in variants_map:
                        variants_map[key] = []
                    # Store original title and author for reference
                    if (title, author) not in variants_map[key]:
                        variants_map[key].append((title, author))
        except Exception as e:
            # Skip files that can't be parsed
            continue
    
    return variants_map

def load_scored_books_detailed():
    """Load all scored books with detailed recognition breakdown"""
    books = {}
    
    filepath = Path(settings.OUTPUT_DIR) / 'all_books_quality_scores.csv'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get('title', '')
            author = row.get('author', '')
            score = float(row.get('final_score', 0))
            recognition = row.get('awards_and_recognition', '')
            
            if title and author:
                key = normalize_title(title, author)
                
                # Parse recognition details
                awards = []
                lists = []
                list_ranks = {}
                
                if recognition:
                    parts = [p.strip() for p in recognition.split(';')]
                    for part in parts:
                        # Extract list rankings
                        if '#' in part:
                            list_name = part.split('#')[0].strip()
                            try:
                                rank = int(part.split('#')[1].strip().split()[0])
                                lists.append(list_name)
                                list_ranks[list_name] = rank
                            except:
                                lists.append(part)
                        # Identify awards vs lists
                        elif any(word in part.lower() for word in ['prize', 'award', 'nobel', 'pulitzer', 'booker']):
                            awards.append(part)
                        else:
                            lists.append(part)
                
                books[key] = {
                    'title': title,
                    'author': author,
                    'score': score,
                    'awards': awards,
                    'lists': lists,
                    'list_ranks': list_ranks
                }
    
    return books

def query_calibre_books():
    """Query Calibre library for all books"""
    db_path = settings.CALIBRE_DB_PATH
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all books with authors
    query = """
    SELECT 
        b.id,
        b.title,
        a.name as author
    FROM books b
    LEFT JOIN books_authors_link ba ON b.id = ba.book
    LEFT JOIN authors a ON ba.author = a.id
    ORDER BY b.id
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    calibre_books = {}
    
    for book_id, title, author in rows:
        if title and author:
            key = normalize_title(title, author)
            calibre_books[key] = {
                'id': book_id,
                'title': title,
                'author': author
            }
    
    conn.close()
    
    return calibre_books

def main():
    print("=" * 80)
    print("CALIBRE AWARDS ANALYSIS - DETAILED BREAKDOWN")
    print("=" * 80)
    print()
    
    print("Loading title variants from JSON sources...")
    title_variants = load_title_variants_from_json()
    print(f"✓ Loaded title variants for matching")
    print()
    
    print("Loading scored books with detailed recognition...")
    scored_books = load_scored_books_detailed()
    print(f"✓ Loaded {len(scored_books):,} scored books")
    print()
    
    print("Querying Calibre library...")
    calibre_books = query_calibre_books()
    print(f"✓ Found {len(calibre_books):,} books in Calibre")
    print()
    
    # Create reverse mapping for variant lookups
    print("Building variant matching index...")
    variant_to_canonical = {}
    for canonical_key, variant_list in title_variants.items():
        for variant_title, variant_author in variant_list:
            variant_key = normalize_title(variant_title, variant_author)
            if variant_key not in variant_to_canonical:
                variant_to_canonical[variant_key] = []
            variant_to_canonical[variant_key].append(canonical_key)
    print(f"✓ Built variant index with {len(variant_to_canonical):,} mappings")
    print()
    
    # Match books
    print("Matching books...")
    matched_keys = set()
    matched_books = []
    
    for key, scored_book in scored_books.items():
        calibre_id = None
        
        # Try direct match first
        if key in calibre_books:
            calibre_id = calibre_books[key]['id']
            matched_keys.add(key)
        else:
            # Try variant matching
            if key in variant_to_canonical:
                for canonical_key in variant_to_canonical[key]:
                    if canonical_key in calibre_books:
                        calibre_id = calibre_books[canonical_key]['id']
                        matched_keys.add(key)
                        break
        
        if calibre_id:
            matched_books.append({
                'match_key': key,
                'calibre_id': calibre_id,
                'title': calibre_books[key]['title'] if key in calibre_books else scored_book['title'],
                'author': calibre_books[key]['author'] if key in calibre_books else scored_book['author'],
                'quality_score': scored_book['score'],
                'awards': scored_book['awards'],
                'lists': scored_book['lists'],
                'list_ranks': scored_book['list_ranks']
            })
    
    print(f"✓ Matched {len(matched_books):,} books")
    print()
    
    output_dir = Path(settings.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. All awards and recognitions for OWNED books
    print("Generating owned books awards breakdown...")
    all_awards_file = output_dir / 'calibre_all_awards_recognitions.csv'
    
    awards_data = []
    for book in matched_books:
        # Add individual awards
        if book['awards']:
            for award in book['awards']:
                if award.strip():
                    awards_data.append({
                        'award_or_list': award.strip(),
                        'type': 'award',
                        'rank': None,
                        'calibre_id': book['calibre_id'],
                        'title': book['title'],
                        'author': book['author'],
                        'quality_score': book['quality_score']
                    })
        
        # Add list memberships (with or without rank)
        if book['list_ranks']:
            for list_name, rank in book['list_ranks'].items():
                awards_data.append({
                    'award_or_list': list_name,
                    'type': 'list',
                    'rank': rank,
                    'calibre_id': book['calibre_id'],
                    'title': book['title'],
                    'author': book['author'],
                    'quality_score': book['quality_score']
                })
        elif book['lists']:
            # Lists without explicit rankings
            for list_name in book['lists']:
                if list_name.strip() and list_name.strip() not in (book['list_ranks'].keys() if book['list_ranks'] else []):
                    awards_data.append({
                        'award_or_list': list_name.strip(),
                        'type': 'list',
                        'rank': None,
                        'calibre_id': book['calibre_id'],
                        'title': book['title'],
                        'author': book['author'],
                        'quality_score': book['quality_score']
                    })
    
    with open(all_awards_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'award_or_list', 'type', 'rank', 'calibre_id', 'title', 'author', 'quality_score'
        ])
        writer.writeheader()
        # Sort by award/list name, then by rank (if present), then by quality score
        for item in sorted(awards_data, key=lambda x: (x['award_or_list'], x['rank'] if x['rank'] else 999999, -x['quality_score'])):
            writer.writerow(item)
    
    print(f"✓ Created: {all_awards_file}")
    print(f"  - {len(awards_data)} entries from owned books")
    print()
    
    # 2. Missing books from awards list (same format)
    print("Generating missing books awards breakdown...")
    missing_books_file = output_dir / 'calibre_missing_awards_recognitions.csv'
    
    missing_awards_data = []
    missing_book_count = 0
    
    for key, scored_book in scored_books.items():
        if key not in matched_keys:
            # Try variant matching too
            found_via_variant = False
            if key in variant_to_canonical:
                for canonical_key in variant_to_canonical[key]:
                    if canonical_key in matched_keys:
                        found_via_variant = True
                        break
            
            if not found_via_variant:
                missing_book_count += 1
                
                # Add individual awards
                if scored_book['awards']:
                    for award in scored_book['awards']:
                        if award.strip():
                            missing_awards_data.append({
                                'award_or_list': award.strip(),
                                'type': 'award',
                                'rank': None,
                                'title': scored_book['title'],
                                'author': scored_book['author'],
                                'quality_score': scored_book['score']
                            })
                
                # Add list memberships (with or without rank)
                if scored_book['list_ranks']:
                    for list_name, rank in scored_book['list_ranks'].items():
                        missing_awards_data.append({
                            'award_or_list': list_name,
                            'type': 'list',
                            'rank': rank,
                            'title': scored_book['title'],
                            'author': scored_book['author'],
                            'quality_score': scored_book['score']
                        })
                elif scored_book['lists']:
                    # Lists without explicit rankings
                    for list_name in scored_book['lists']:
                        if list_name.strip():
                            missing_awards_data.append({
                                'award_or_list': list_name.strip(),
                                'type': 'list',
                                'rank': None,
                                'title': scored_book['title'],
                                'author': scored_book['author'],
                                'quality_score': scored_book['score']
                            })
    
    with open(missing_books_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'award_or_list', 'type', 'rank', 'title', 'author', 'quality_score'
        ])
        writer.writeheader()
        # Sort by award/list name, then by rank (if present), then by quality score
        for item in sorted(missing_awards_data, key=lambda x: (x['award_or_list'], x['rank'] if x['rank'] else 999999, -x['quality_score'])):
            writer.writerow(item)
    
    print(f"✓ Created: {missing_books_file}")
    print(f"  - {len(missing_awards_data)} entries from {missing_book_count} missing books")
    print()
    
    # 3. List rankings file (for owned books only, with rankings)
    print("Generating list rankings...")
    rankings_file = output_dir / 'calibre_list_rankings.csv'
    
    lists_data = defaultdict(list)
    for book in matched_books:
        if book['list_ranks']:
            for list_name, rank in book['list_ranks'].items():
                lists_data[list_name].append({
                    'calibre_id': book['calibre_id'],
                    'title': book['title'],
                    'author': book['author'],
                    'rank': rank,
                    'score': book['quality_score']
                })
    
    with open(rankings_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['list_name', 'rank', 'calibre_id', 'title', 'author', 'quality_score'])
        
        for list_name, books in sorted(lists_data.items()):
            for book in sorted(books, key=lambda x: x['rank']):
                writer.writerow([
                    list_name,
                    book['rank'],
                    book['calibre_id'],
                    book['title'],
                    book['author'],
                    book['score']
                ])
    
    print(f"✓ Created: {rankings_file}")
    print(f"  - List rankings for {len(lists_data)} different lists")
    print()
    
    # 4. Summary by list
    print("Generating list summary...")
    list_summary_file = output_dir / 'calibre_lists_summary.txt'
    with open(list_summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("CALIBRE LIBRARY - LIST MEMBERSHIP SUMMARY\n")
        f.write("=" * 80 + "\n\n")
        
        for list_name, books in sorted(lists_data.items(), key=lambda x: len(x[1]), reverse=True):
            f.write(f"\n{list_name}\n")
            f.write("-" * 80 + "\n")
            f.write(f"You own {len(books)} books from this list\n\n")
            
            for book in sorted(books, key=lambda x: x['rank'])[:10]:
                f.write(f"  #{book['rank']:3d}. {book['title']} by {book['author']} (Score: {book['score']:.0f})\n")
            
            if len(books) > 10:
                f.write(f"  ... and {len(books) - 10} more\n")
            f.write("\n")
    
    print(f"✓ Created: {list_summary_file}")
    print(f"  - Human-readable summary of list membership")
    print()
    
    print("=" * 80)
    print("FILES GENERATED")
    print("=" * 80)
    print()
    print("1. calibre_all_awards_recognitions.csv")
    print("   Awards and list memberships for books YOU OWN")
    print()
    print("2. calibre_missing_awards_recognitions.csv")
    print("   Awards and list memberships for books YOU DON'T OWN")
    print()
    print("3. calibre_list_rankings.csv")
    print("   Ranked lists (e.g., NYT #1, Modern Library #5) for owned books")
    print()
    print("4. calibre_lists_summary.txt")
    print("   Human-readable summary of list membership")
    print()
    print("=" * 80)
    print("ANALYSIS TIPS")
    print("=" * 80)
    print()
    print("Finding gaps in a specific list:")
    print("  - Compare ranks in owned vs missing files")
    print("  - Example: BBC #1 owned, BBC #3 missing, BBC #5 owned")
    print()
    print("Acquisition priorities:")
    print("  - Filter missing file by award type or list name")
    print("  - Sort by rank (for lists) or quality_score")
    print()

if __name__ == '__main__':
    main()

