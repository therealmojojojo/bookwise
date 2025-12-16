#!/usr/bin/env python3
"""
Generate Calibre Import Files
Creates CSV files for importing metadata and tags into Calibre
"""

import csv
import sqlite3
import json
from pathlib import Path
from datetime import datetime
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
                tags = []
                
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
                                tags.append(f"{list_name}")
                            except:
                                lists.append(part)
                                tags.append(part)
                        # Identify awards vs lists
                        elif any(word in part.lower() for word in ['prize', 'award', 'nobel', 'pulitzer', 'booker']):
                            awards.append(part)
                            tags.append(part)
                        else:
                            lists.append(part)
                            tags.append(part)
                
                books[key] = {
                    'title': title,
                    'author': author,
                    'score': score,
                    'recognition_full': recognition,
                    'awards': awards,
                    'lists': lists,
                    'list_ranks': list_ranks,
                    'tags': tags
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

def generate_score_category(score):
    """Generate score category tag"""
    if score >= 90:
        return "Score: Legendary (90+)"
    elif score >= 80:
        return "Score: Exceptional (80-89)"
    elif score >= 70:
        return "Score: Outstanding (70-79)"
    elif score >= 60:
        return "Score: Excellent (60-69)"
    elif score >= 50:
        return "Score: Very Good (50-59)"
    elif score >= 40:
        return "Score: Good (40-49)"
    elif score >= 30:
        return "Score: Solid (30-39)"
    elif score >= 20:
        return "Score: Notable (20-29)"
    elif score >= 10:
        return "Score: Recognized (10-19)"
    else:
        return "Score: Limited (0-9)"

def main():
    print("=" * 80)
    print("GENERATING CALIBRE IMPORT FILES")
    print("=" * 80)
    print()
    
    processing_date = datetime.now().strftime('%Y-%m-%d')
    scoring_version = "1.0"
    
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
    
    # Match books (with variant support)
    print("Matching books (with title variant support)...")
    matched = []
    variant_matches = 0
    
    for key, scored_book in scored_books.items():
        calibre_id = None
        matched_key = None
        matched_via = "direct"

        # Try direct match first
        if key in calibre_books:
            calibre_id = calibre_books[key]['id']
            matched_key = key
        else:
            # Try variant matching
            if key in variant_to_canonical:
                for canonical_key in variant_to_canonical[key]:
                    if canonical_key in calibre_books:
                        calibre_id = calibre_books[canonical_key]['id']
                        matched_key = canonical_key
                        matched_via = "variant"
                        variant_matches += 1
                        break

        if calibre_id:

            # Generate comprehensive tags
            all_tags = set()

            # Add score category
            score_category = generate_score_category(scored_book['score'])
            all_tags.add(score_category)

            # Add quality tier
            if scored_book['score'] >= 50:
                all_tags.add("Quality: Top Tier")
            elif scored_book['score'] >= 30:
                all_tags.add("Quality: High")
            elif scored_book['score'] >= 10:
                all_tags.add("Quality: Notable")

            # Add award/prize tags
            for award in scored_book['awards']:
                # Clean up award names for tags
                award_tag = award.split('(')[0].strip()  # Remove year
                all_tags.add(f"Award: {award_tag}")

            # Add list membership tags
            for list_name in scored_book['lists']:
                list_tag = list_name.split('#')[0].strip()  # Remove rank
                all_tags.add(f"List: {list_tag}")

            # Add processing status tag
            all_tags.add("Quality: Processed")

            matched.append({
                'calibre_id': calibre_id,
                'title': calibre_books[matched_key]['title'],
                'author': calibre_books[matched_key]['author'],
                'match_key': key,  # Normalized key for future matching
                'quality_score': scored_book['score'],
                'score_category': score_category,
                'processing_date': processing_date,
                'scoring_version': scoring_version,
                'awards': '; '.join(scored_book['awards']),
                'lists': '; '.join(scored_book['lists']),
                'list_ranks': json.dumps(scored_book['list_ranks']),
                'tags': ', '.join(sorted(all_tags)),
                'recognition_full': scored_book['recognition_full']
            })
    
    print(f"✓ Matched {len(matched):,} books ({variant_matches} via title variants)")
    print()
    
    # Generate outputs
    output_dir = Path(settings.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Main metadata update file (CSV for calibredb)
    metadata_file = output_dir / 'calibre_metadata_updates.csv'
    with open(metadata_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'calibre_id', 'title', 'author', 'match_key', 'quality_score', 
            'score_category', 'processing_date', 'scoring_version',
            'awards', 'lists', 'list_ranks', 'tags', 'recognition_full'
        ])
        writer.writeheader()
        for book in sorted(matched, key=lambda x: x['quality_score'], reverse=True):
            writer.writerow(book)
    
    print(f"✓ Created: {metadata_file}")
    print(f"  - {len(matched)} books with complete metadata")
    print()
    
    # 2. Tags-only file (easy import)
    tags_file = output_dir / 'calibre_tags_import.csv'
    with open(tags_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'tags'])
        for book in matched:
            writer.writerow([book['calibre_id'], book['tags']])
    
    print(f"✓ Created: {tags_file}")
    print(f"  - Simplified format for tag import")
    print()
    
    print("=" * 80)
    print("FILES GENERATED")
    print("=" * 80)
    print()
    print("1. calibre_metadata_updates.csv")
    print("   Complete metadata for all matched books")
    print("   Fields: calibre_id, title, author, quality_score, tags, etc.")
    print()
    print("2. calibre_tags_import.csv")
    print("   Simplified CSV with ID and tags (easy import)")
    print()
    print("=" * 80)
    print("USAGE INSTRUCTIONS")
    print("=" * 80)
    print()
    print("Option 1: Manual Import via Calibre GUI")
    print("  1. Open Calibre")
    print("  2. Select books to update")
    print("  3. Edit metadata → Add tags from calibre_tags_import.csv")
    print()
    print("Option 2: Create Custom Columns (RECOMMENDED)")
    print("  1. In Calibre: Preferences → Add your own columns")
    print("  2. Create these custom columns:")
    print("     - 'quality_score' (type: float, display as integer)")
    print("     - 'quality_processed_date' (type: text)")
    print("     - 'quality_match_key' (type: text)")
    print("     - 'quality_version' (type: text)")
    print("  3. Import data from calibre_metadata_updates.csv")
    print()
    print("=" * 80)
    print("WORKFLOW TIPS")
    print("=" * 80)
    print()
    print("After adding new books to Calibre:")
    print("  1. Re-run: python3 generate_calibre_imports.py")
    print("  2. New books will be identified and scored")
    print("  3. Import only new entries (compare processing_date)")
    print()
    print("Finding unprocessed books in Calibre:")
    print("  - Search: NOT tags:\"Quality: Processed\"")
    print("  - This shows books not yet scored")
    print()

if __name__ == '__main__':
    main()

