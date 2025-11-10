#!/usr/bin/env python3
"""
Detect Score Changes and Generate Selective Re-enrichment Input

Compares old vs. new quality scores to detect which books need re-enrichment.
This is useful after updating datasources (adding authors to canonical lists, etc.).

Workflow:
1. Update datasource files (e.g., add author to canonical_authors_tier_a.json)
2. Regenerate scores: python3 src/scripts/generate_unified_scores.py
3. Run this script to detect changes
4. Re-enrich only changed books
5. Re-import to Calibre

Usage:
    python3 src/dataenrichment/detect_score_changes.py
    python3 src/dataenrichment/detect_score_changes.py --threshold 10  # Only if score changed by 10+
"""

import csv
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config.settings import settings


def load_current_scores():
    """Load scores from enrichment-ready JSONL (new) or CSV (legacy)."""
    # Try JSONL first
    jsonl_file = Path(settings.OUTPUT_DIR) / 'calibre_enrichment_ready.jsonl'

    if jsonl_file.exists():
        print(f"📂 Loading current scores from {jsonl_file.name}...")
        scores = {}
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                book = json.loads(line)
                calibre_id = int(book['calibre_id'])
                scores[calibre_id] = {
                    'title': book['title'],
                    'author': book['author'],
                    'score': float(book['quality_score']),
                    'recognition': book.get('awards_and_recognition', '')
                }
        print(f"✓ Loaded {len(scores)} books from JSONL")
        return scores

    # Fall back to CSV
    scored_file = Path(settings.OUTPUT_DIR) / 'calibre_owned_scored_books.csv'

    if scored_file.exists():
        print(f"⚠️  Loading from legacy CSV format...")
        print("   Consider regenerating with: python3 src/calibrebrowser/analyze_library.py --coverage")
        scores = {}
        with open(scored_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                calibre_id = int(row['calibre_id'])
                scores[calibre_id] = {
                    'title': row['title'],
                    'author': row['author'],
                    'score': float(row['score']),
                    'recognition': row.get('recognition', '')
                }
        print(f"✓ Loaded {len(scores)} books from CSV")
        return scores

    # No file found
    print(f"❌ Current scores file not found!")
    print("   Run: python3 src/calibrebrowser/analyze_library.py --coverage")
    return {}


def load_enriched_scores():
    """Load scores from enriched books (ChromaDB primary, JSONL fallback)."""
    import chromadb
    import os
    
    # Try ChromaDB first
    try:
        chromadb_path = os.path.expanduser(settings.CHROMADB_PATH)
        client = chromadb.PersistentClient(path=chromadb_path)
        collection = client.get_collection("book_metadata_embeddings")
        
        results = collection.get(include=['metadatas'])
        
        scores = {}
        for i, calibre_id in enumerate(results['ids']):
            metadata = results['metadatas'][i]
            scores[int(calibre_id)] = {
                'title': metadata['title'],
                'author': metadata['author'],
                'score': float(metadata.get('quality_score', 0)),
                'recognition': metadata.get('awards', '')
            }
        
        return scores
        
    except Exception as e:
        print(f"⚠️  Could not load from ChromaDB: {e}")
        print("   Trying JSONL fallback...")
        
        # Fallback to JSONL
        enrichment_dir = Path(settings.OUTPUT_DIR) / 'enrichment'
        enriched_file = enrichment_dir / 'enriched_books.jsonl'
        
        if not enriched_file.exists():
            print(f"⚠️  No enriched books found in ChromaDB or JSONL")
            return {}
        
        scores = {}
        with open(enriched_file, 'r', encoding='utf-8') as f:
            for line in f:
                book = json.loads(line)
                calibre_id = book['calibre_id']
                scores[calibre_id] = {
                    'title': book['title'],
                    'author': book['author'],
                    'score': book['quality_score'],
                    'recognition': book.get('awards_and_recognition', '')
                }
        
        return scores


def detect_changes(old_scores, new_scores, threshold=0):
    """
    Detect books with score changes.
    
    Args:
        old_scores: Dict of {calibre_id: {title, author, score, recognition}}
        new_scores: Dict of {calibre_id: {title, author, score, recognition}}
        threshold: Only report changes >= this value (default: any change)
    
    Returns:
        List of changed books with details
    """
    changes = []
    
    for calibre_id, new_data in new_scores.items():
        if calibre_id not in old_scores:
            # New book in library
            changes.append({
                'calibre_id': calibre_id,
                'title': new_data['title'],
                'author': new_data['author'],
                'old_score': None,
                'new_score': new_data['score'],
                'change': new_data['score'],
                'recognition': new_data['recognition'],
                'change_type': 'NEW'
            })
        else:
            old_data = old_scores[calibre_id]
            score_diff = new_data['score'] - old_data['score']
            
            if abs(score_diff) >= threshold:
                changes.append({
                    'calibre_id': calibre_id,
                    'title': new_data['title'],
                    'author': new_data['author'],
                    'old_score': old_data['score'],
                    'new_score': new_data['score'],
                    'change': score_diff,
                    'recognition': new_data['recognition'],
                    'change_type': 'INCREASED' if score_diff > 0 else 'DECREASED'
                })
    
    return sorted(changes, key=lambda x: abs(x['change']), reverse=True)


def generate_enrichment_input(changed_books, current_scores):
    """Generate enrichment input file for changed books."""
    enrichment_dir = Path(settings.OUTPUT_DIR) / 'enrichment'
    enrichment_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = enrichment_dir / 'books_to_reenrich.jsonl'
    
    # Query Calibre for full book data
    import sqlite3
    conn = sqlite3.connect(settings.CALIBRE_DB_PATH)
    cursor = conn.cursor()
    
    books_data = []
    for change in changed_books:
        calibre_id = change['calibre_id']
        
        # Get book data from Calibre
        cursor.execute("""
            SELECT b.id, b.title, b.path, b.pubdate, 
                   (SELECT GROUP_CONCAT(a.name, ' & ') FROM authors a 
                    JOIN books_authors_link bal ON a.id = bal.author 
                    WHERE bal.book = b.id) as author,
                   (SELECT c.text FROM comments c WHERE c.book = b.id) as description
            FROM books b
            WHERE b.id = ?
        """, (calibre_id,))
        
        row = cursor.fetchone()
        if row:
            book_id, title, path, pubdate, author, description = row
            
            book_data = {
                'book_id': str(book_id),
                'calibre_id': book_id,
                'title': title,
                'author': author or 'Unknown',
                'quality_score': current_scores[calibre_id]['score'],
                'awards_and_recognition': current_scores[calibre_id]['recognition'],
                'existing_description': description or '',
                'publication_date': pubdate or '',
                'file_path': path or '',
                'reason': f"Score changed: {change['old_score']} → {change['new_score']}"
            }
            books_data.append(book_data)
    
    conn.close()
    
    # Write to JSONL
    with open(output_file, 'w', encoding='utf-8') as f:
        for book in books_data:
            f.write(json.dumps(book) + '\n')
    
    return output_file, len(books_data)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Detect score changes and generate selective re-enrichment input",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Detect all score changes
  python3 src/dataenrichment/detect_score_changes.py
  
  # Only detect significant changes (10+ points)
  python3 src/dataenrichment/detect_score_changes.py --threshold 10
  
  # Just show changes, don't generate input
  python3 src/dataenrichment/detect_score_changes.py --dry-run
  
Complete Workflow:
  1. Update datasource (e.g., add author to canonical_authors_tier_a.json)
  2. Regenerate scores:
     python3 src/scripts/generate_unified_scores.py
     python3 src/calibrebrowser/analyze_library.py --coverage
  3. Detect changes:
     python3 src/dataenrichment/detect_score_changes.py
  4. Re-enrich changed books:
     python3 src/dataenrichment/enrich_books.py --input books_to_reenrich.jsonl --yes
  5. Update Calibre:
     python3 src/dataenrichment/add_tags_to_calibre.py --yes --update-descriptions custom
        """
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=0,
        help='Minimum score change to report (default: any change)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show changes but do not generate re-enrichment input'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("SCORE CHANGE DETECTION")
    print("=" * 80)
    print()
    
    # Load scores
    print("Loading current scores from calibre_owned_scored_books.csv...")
    current_scores = load_current_scores()
    if not current_scores:
        return
    print(f"✓ Loaded {len(current_scores)} books")
    
    print("\nLoading enriched scores from enriched_books.jsonl...")
    enriched_scores = load_enriched_scores()
    print(f"✓ Loaded {len(enriched_scores)} enriched books")
    print()
    
    # Detect changes
    print(f"Detecting changes (threshold: {args.threshold:+.1f} points)...")
    changes = detect_changes(enriched_scores, current_scores, args.threshold)
    
    if not changes:
        print("✓ No score changes detected!")
        print()
        print("All enriched books have up-to-date scores.")
        return
    
    # Report changes
    print("\n" + "=" * 80)
    print("DETECTED CHANGES")
    print("=" * 80)
    print()
    
    new_books = [c for c in changes if c['change_type'] == 'NEW']
    increased = [c for c in changes if c['change_type'] == 'INCREASED']
    decreased = [c for c in changes if c['change_type'] == 'DECREASED']
    
    print(f"Total changes: {len(changes)}")
    print(f"  New books:           {len(new_books)}")
    print(f"  Score increased:     {len(increased)}")
    print(f"  Score decreased:     {len(decreased)}")
    print()
    
    # Show top changes
    print("TOP 20 CHANGES BY MAGNITUDE:")
    print("-" * 80)
    for change in changes[:20]:
        if change['change_type'] == 'NEW':
            print(f"  NEW: {change['title']}")
            print(f"       by {change['author']}")
            print(f"       Score: {change['new_score']:.1f}")
        else:
            sign = "+" if change['change'] > 0 else ""
            print(f"  {change['title']}")
            print(f"       by {change['author']}")
            print(f"       Score: {change['old_score']:.1f} → {change['new_score']:.1f} ({sign}{change['change']:.1f})")
        print()
    
    if len(changes) > 20:
        print(f"  ... and {len(changes) - 20} more")
        print()
    
    # Estimate cost
    estimated_cost = len(changes) * 0.021
    print("=" * 80)
    print("RE-ENRICHMENT ESTIMATE")
    print("=" * 80)
    print()
    print(f"Books to re-enrich:  {len(changes)}")
    print(f"Estimated cost:      ${estimated_cost:.2f}")
    print(f"Estimated time:      ~{len(changes) * 1.5:.0f} seconds ({len(changes) * 1.5 / 60:.1f} minutes)")
    print()
    
    if args.dry_run:
        print("⚠️  DRY RUN MODE - No files generated")
        print()
        return
    
    # Generate input file
    print("Generating re-enrichment input file...")
    output_file, count = generate_enrichment_input(changes, current_scores)
    print(f"✓ Created: {output_file}")
    print(f"  {count} books ready for re-enrichment")
    print()
    
    # Next steps
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print()
    print("1. Review the changes above")
    print()
    print("2. Re-enrich changed books:")
    print(f"   python3 src/dataenrichment/enrich_books.py --input {output_file.name} --yes")
    print()
    print("3. Update Calibre with new enrichment:")
    print("   python3 src/dataenrichment/add_tags_to_calibre.py --yes --update-descriptions custom")
    print()


if __name__ == '__main__':
    main()

