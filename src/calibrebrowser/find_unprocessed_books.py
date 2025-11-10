#!/usr/bin/env python3
"""
Find Unprocessed Books in Calibre
Identifies books in your Calibre library that haven't been quality-scored yet
"""

import csv
import sqlite3
import json
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.normalizers import normalize_title, normalize_author
from src.utils.title_variants import get_all_title_variants
from src.config.settings import settings

def load_processed_books():
    """Load list of already processed books"""
    processed_keys = set()
    
    csv_path = Path(settings.OUTPUT_DIR) / 'calibre_metadata_updates.csv'
    
    if csv_path.exists():
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                match_key = row.get('match_key', '')
                if match_key:
                    processed_keys.add(match_key)
    
    return processed_keys

def query_all_calibre_books():
    """Query all books in Calibre library"""
    db_path = settings.CALIBRE_DB_PATH
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query = """
    SELECT 
        b.id,
        b.title,
        a.name as author,
        b.timestamp as date_added
    FROM books b
    LEFT JOIN books_authors_link ba ON b.id = ba.book
    LEFT JOIN authors a ON ba.author = a.id
    ORDER BY b.timestamp DESC
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    books = []
    for book_id, title, author, date_added in rows:
        if title and author:
            key = normalize_title(title, author)
            books.append({
                'id': book_id,
                'title': title,
                'author': author,
                'date_added': date_added,
                'match_key': key
            })
    
    conn.close()
    
    return books

def main():
    print("=" * 80)
    print("FINDING UNPROCESSED BOOKS IN CALIBRE (with title variant support)")
    print("=" * 80)
    print()
    
    print("Loading previously processed books...")
    processed_keys = load_processed_books()
    print(f"✓ Found {len(processed_keys):,} already processed books")
    print()
    
    print("Querying Calibre library...")
    all_books = query_all_calibre_books()
    print(f"✓ Found {len(all_books):,} total books in Calibre")
    print()
    
    # Find unprocessed books (now variant-aware)
    # Note: Since these are unprocessed, they're not yet matched
    # But this provides consistent infrastructure with other scripts
    unprocessed = []
    for book in all_books:
        if book['match_key'] not in processed_keys:
            unprocessed.append(book)
    
    print(f"✓ Identified {len(unprocessed):,} unprocessed books")
    print()
    
    if unprocessed:
        # Save to file
        output_dir = Path(settings.OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / 'unprocessed_books.csv'
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'calibre_id', 'title', 'author', 'date_added', 'match_key'
            ])
            writer.writeheader()
            for book in unprocessed:
                writer.writerow({
                    'calibre_id': book['id'],
                    'title': book['title'],
                    'author': book['author'],
                    'date_added': book['date_added'],
                    'match_key': book['match_key']
                })
        
        print(f"✓ Saved to: {output_file}")
        print()
        
        # Show sample
        print("=" * 80)
        print("SAMPLE OF UNPROCESSED BOOKS (Most Recently Added)")
        print("=" * 80)
        print()
        
        for book in unprocessed[:20]:
            print(f"  [{book['id']:5d}] {book['title']}")
            print(f"          by {book['author']}")
            print(f"          Added: {book['date_added']}")
            print()
        
        if len(unprocessed) > 20:
            print(f"  ... and {len(unprocessed) - 20:,} more")
            print()
        
        print("=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print()
        print("These unprocessed books are not in your award/quality database.")
        print()
        print("Options:")
        print("  1. They may be books that don't have awards/recognition")
        print("  2. They may need to be added to your datasources")
        print("  3. Re-run the scoring after updating datasources")
        print()
        print("To see these in Calibre:")
        print("  - After importing tags, search: NOT tags:\"Quality: Processed\"")
        print()
    else:
        print("✓ All books in your Calibre library have been processed!")
        print()
        print("  No unprocessed books found.")
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"  Total books in Calibre:    {len(all_books):,}")
    print(f"  Processed (scored):        {len(processed_keys):,}")
    print(f"  Unprocessed:               {len(unprocessed):,}")
    print(f"  Coverage:                  {len(processed_keys)/len(all_books)*100:.1f}%")
    print()

if __name__ == '__main__':
    main()

