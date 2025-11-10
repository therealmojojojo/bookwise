#!/usr/bin/env python3
"""
Analyze Calibre Library Coverage
Compare the final scored books list against your Calibre library
"""

import csv
import sqlite3
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.normalizers import normalize_title, normalize_author
from src.utils.title_variants import get_all_title_variants
from src.config.settings import settings

def get_quality_tier(score):
    """Map score to quality tier"""
    if score >= 90: return 'Legendary'
    if score >= 80: return 'Exceptional'
    if score >= 70: return 'Outstanding'
    if score >= 60: return 'Excellent'
    if score >= 50: return 'Very Good'
    if score >= 40: return 'Good'
    if score >= 30: return 'Solid'
    if score >= 20: return 'Notable'
    if score >= 10: return 'Recognized'
    return 'Limited'

def get_enrichment_priority(score):
    """Determine enrichment priority based on score"""
    if score >= 80: return 'high'
    if score >= 50: return 'medium'
    return 'low'

def load_title_variants_from_json():
    """Load title variants from original JSON sources"""
    variants_map = {}
    datasources_dir = Path(settings.DATASOURCES_DIR)
    
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
                
                variants = get_all_title_variants(
                    title=title,
                    alternate_titles=item.get('alternate_titles', []),
                    notes=item.get('notes', '')
                )
                
                for variant in variants:
                    key = normalize_title(variant, author)
                    if key not in variants_map:
                        variants_map[key] = []
                    if (title, author) not in variants_map[key]:
                        variants_map[key].append((title, author))
        except Exception:
            continue
    
    return variants_map

def load_scored_books():
    """Load all scored books from CSV"""
    books = {}
    authors = set()
    
    filepath = Path(settings.OUTPUT_DIR) / 'all_books_quality_scores.csv'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get('title', '')
            author = row.get('author', '')
            score = float(row.get('final_score', 0))
            
            if title and author:
                key = normalize_title(title, author)
                books[key] = {
                    'title': title,
                    'author': author,
                    'score': score,
                    'recognition': row.get('awards_and_recognition', '')
                }
                authors.add(normalize_author(author))
    
    return books, authors

def query_calibre_library():
    """Query Calibre library for all books and authors"""
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
    calibre_authors = set()
    
    for book_id, title, author in rows:
        if title and author:
            key = normalize_title(title, author)
            calibre_books[key] = {
                'id': book_id,
                'title': title,
                'author': author
            }
            calibre_authors.add(normalize_author(author))
    
    conn.close()

    return calibre_books, calibre_authors

def export_enrichment_jsonl(matched_books, output_dir):
    """
    Export enrichment-ready JSONL with complete metadata.
    This file contains all the information needed for the dataenrichment pipeline.
    """
    output_file = output_dir / 'calibre_enrichment_ready.jsonl'

    print("=" * 80)
    print("EXPORTING ENRICHMENT-READY JSONL")
    print("=" * 80)
    print()
    print(f"📝 Querying Calibre database for complete metadata...")

    conn = sqlite3.connect(settings.CALIBRE_DB_PATH)
    cursor = conn.cursor()

    exported_count = 0

    with open(output_file, 'w', encoding='utf-8') as f:
        for key, book_data in matched_books.items():
            calibre_id = book_data['calibre_id']

            # Get full metadata from Calibre
            cursor.execute("""
                SELECT
                    b.id,
                    b.title,
                    b.pubdate,
                    b.isbn,
                    b.path,
                    b.last_modified,
                    b.timestamp,
                    b.series_index,
                    (SELECT p.name FROM publishers p
                     JOIN books_publishers_link bpl ON p.id = bpl.publisher
                     WHERE bpl.book = b.id LIMIT 1) as publisher,
                    (SELECT c.text FROM comments c WHERE c.book = b.id) as description,
                    (SELECT l.lang_code FROM languages l
                     JOIN books_languages_link bll ON l.id = bll.lang_code
                     WHERE bll.book = b.id LIMIT 1) as language,
                    (SELECT s.name FROM series s
                     JOIN books_series_link bsl ON s.id = bsl.series
                     WHERE bsl.book = b.id LIMIT 1) as series
                FROM books b
                WHERE b.id = ?
            """, (calibre_id,))

            row = cursor.fetchone()

            if not row:
                continue

            # Build enrichment record
            # Row indices: 0=id, 1=title, 2=pubdate, 3=isbn, 4=path, 5=last_modified,
            #              6=timestamp, 7=series_index, 8=publisher, 9=description,
            #              10=language, 11=series
            record = {
                'calibre_id': calibre_id,
                'title': book_data['title'],
                'author': book_data['author'],
                'quality_score': float(book_data['score']),
                'quality_tier': get_quality_tier(book_data['score']),
                'awards_and_recognition': book_data.get('recognition', ''),
                'existing_description': row[9] if row[9] else '',
                'publication_date': row[2] if row[2] else None,
                'isbn': row[3] if row[3] else None,
                'publisher': row[8] if row[8] else None,
                'file_path': row[4] if row[4] else None,
                'language': row[10] if row[10] else 'eng',
                'series': row[11] if row[11] else None,
                'series_index': float(row[7]) if row[7] else None,
                'added_date': row[6] if row[6] else None,
                'modified_date': row[5] if row[5] else None,
                'score_metadata': {
                    'score_date': datetime.now().isoformat(),
                    'score_version': '1.0'
                },
                'enrichment_ready': True,
                'enrichment_priority': get_enrichment_priority(book_data['score'])
            }

            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            exported_count += 1

    conn.close()

    print(f"✓ Exported {exported_count:,} books to {output_file.name}")

    # Calculate file size
    file_size_kb = output_file.stat().st_size / 1024
    print(f"✓ File size: {file_size_kb:.1f} KB")
    print()

    return output_file

def main():
    print("=" * 80)
    print("CALIBRE LIBRARY COVERAGE ANALYSIS")
    print("=" * 80)
    print()
    
    print("Loading title variants from JSON sources...")
    title_variants = load_title_variants_from_json()
    print(f"✓ Loaded title variants for matching")
    print()
    
    print("Loading scored books list...")
    scored_books, scored_authors = load_scored_books()
    print(f"✓ Loaded {len(scored_books):,} scored books by {len(scored_authors):,} authors")
    print()
    
    print("Querying Calibre library...")
    calibre_books, calibre_authors = query_calibre_library()
    print(f"✓ Found {len(calibre_books):,} books by {len(calibre_authors):,} authors in Calibre")
    print()
    
    # Build variant lookup
    print("Building variant matching index...")
    variant_to_canonical = {}
    for canonical_key, variant_list in title_variants.items():
        for variant_title, variant_author in variant_list:
            variant_key = normalize_title(variant_title, variant_author)
            if variant_key not in variant_to_canonical:
                variant_to_canonical[variant_key] = []
            variant_to_canonical[variant_key].append(canonical_key)
    print(f"✓ Built variant index")
    print()
    
    # Find matches (with variant support)
    print("=" * 80)
    print("MATCHING ANALYSIS (with title variant support)")
    print("=" * 80)
    print()
    
    # Books in both
    matched_books = {}
    variant_matches = 0
    
    for key, book in scored_books.items():
        calibre_id = None
        
        # Try direct match
        if key in calibre_books:
            calibre_id = calibre_books[key]['id']
        else:
            # Try variant matching
            if key in variant_to_canonical:
                for canonical_key in variant_to_canonical[key]:
                    if canonical_key in calibre_books:
                        calibre_id = calibre_books[canonical_key]['id']
                        variant_matches += 1
                        break
        
        if calibre_id:
            matched_books[key] = {
                **book,
                'calibre_id': calibre_id
            }
    
    # Authors in both
    matched_authors = scored_authors & calibre_authors
    
    # Books in scored list but not in Calibre
    missing_books = {}
    for key, book in scored_books.items():
        if key not in calibre_books:
            missing_books[key] = book
    
    # Authors in scored list but not in Calibre
    missing_authors = scored_authors - calibre_authors
    
    print(f"📚 BOOKS:")
    print(f"   • In scored list:           {len(scored_books):,}")
    print(f"   • In Calibre library:       {len(calibre_books):,}")
    print(f"   • Matched (you own):        {len(matched_books):,} ({len(matched_books)/len(scored_books)*100:.1f}%)")
    print(f"     - Via title variants:     {variant_matches}")
    print(f"   • Not in Calibre (missing): {len(missing_books):,} ({len(missing_books)/len(scored_books)*100:.1f}%)")
    print()
    
    print(f"👤 AUTHORS:")
    print(f"   • In scored list:           {len(scored_authors):,}")
    print(f"   • In Calibre library:       {len(calibre_authors):,}")
    print(f"   • Matched (you have books by): {len(matched_authors):,} ({len(matched_authors)/len(scored_authors)*100:.1f}%)")
    print(f"   • Not in Calibre (missing):    {len(missing_authors):,} ({len(missing_authors)/len(scored_authors)*100:.1f}%)")
    print()
    
    # Score distribution of owned books
    print("=" * 80)
    print("SCORE DISTRIBUTION OF OWNED BOOKS")
    print("=" * 80)
    print()
    
    score_ranges = {
        'Legendary (90+)': (90, 999),
        'Exceptional (80-89)': (80, 89),
        'Outstanding (70-79)': (70, 79),
        'Excellent (60-69)': (60, 69),
        'Very Good (50-59)': (50, 59),
        'Good (40-49)': (40, 49),
        'Solid (30-39)': (30, 39),
        'Notable (20-29)': (20, 29),
        'Recognized (10-19)': (10, 19),
        'Limited (0-9)': (0, 9),
    }
    
    for range_name, (min_score, max_score) in score_ranges.items():
        count = sum(1 for book in matched_books.values() 
                   if min_score <= book['score'] <= max_score)
        if count > 0:
            pct = count / len(matched_books) * 100
            bar = '█' * int(pct / 3)
            print(f"{range_name:25s}: {count:4d} books ({pct:5.1f}%) {bar}")
    
    print()
    
    # Top scored books you own
    print("=" * 80)
    print("TOP 20 HIGHEST-SCORED BOOKS YOU OWN")
    print("=" * 80)
    print()
    
    sorted_owned = sorted(matched_books.values(), key=lambda x: x['score'], reverse=True)
    
    for i, book in enumerate(sorted_owned[:20], 1):
        print(f"{i:2d}. {book['title']}")
        print(f"    Author: {book['author']}")
        print(f"    Score: {book['score']:.0f} points")
        print(f"    Calibre ID: {book['calibre_id']}")
        print()
    
    # Top scored books you DON'T own
    print("=" * 80)
    print("TOP 20 HIGHEST-SCORED BOOKS YOU DON'T OWN")
    print("=" * 80)
    print()
    
    sorted_missing = sorted(missing_books.values(), key=lambda x: x['score'], reverse=True)
    
    for i, book in enumerate(sorted_missing[:20], 1):
        print(f"{i:2d}. {book['title']}")
        print(f"    Author: {book['author']}")
        print(f"    Score: {book['score']:.0f} points")
        recognition_short = book['recognition'][:80] + '...' if len(book['recognition']) > 80 else book['recognition']
        print(f"    Recognition: {recognition_short}")
        print()
    
    # Authors with most books in scored list that you're missing
    print("=" * 80)
    print("AUTHORS WITH MOST HIGH-SCORING BOOKS YOU'RE MISSING")
    print("=" * 80)
    print()
    
    missing_by_author = defaultdict(list)
    for book in missing_books.values():
        if book['score'] >= 30:  # Only high-scoring books
            missing_by_author[book['author']].append(book)
    
    sorted_authors = sorted(missing_by_author.items(), 
                          key=lambda x: (len(x[1]), sum(b['score'] for b in x[1])), 
                          reverse=True)
    
    for i, (author, books) in enumerate(sorted_authors[:15], 1):
        total_score = sum(b['score'] for b in books)
        avg_score = total_score / len(books)
        print(f"{i:2d}. {author}")
        print(f"    Missing: {len(books)} books (avg score: {avg_score:.0f}, total: {total_score:.0f})")
        # Show top 3 books
        top_books = sorted(books, key=lambda x: x['score'], reverse=True)[:3]
        for book in top_books:
            print(f"      - {book['title']} ({book['score']:.0f} pts)")
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Coverage: You own {len(matched_books):,} out of {len(scored_books):,} high-quality books ({len(matched_books)/len(scored_books)*100:.1f}%)")
    print(f"Authors: You have books by {len(matched_authors):,} out of {len(scored_authors):,} authors ({len(matched_authors)/len(scored_authors)*100:.1f}%)")
    print()
    
    # Save enrichment-ready JSONL
    output_dir = Path(settings.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export JSONL with complete metadata for dataenrichment
    export_enrichment_jsonl(matched_books, output_dir)

if __name__ == '__main__':
    main()

