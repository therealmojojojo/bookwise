#!/usr/bin/env python3
"""
Check Enrichment Status
Quick summary of enrichment progress and cost tracking.

Usage:
    python3 src/dataenrichment/check_enrichment_status.py
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config.settings import settings


def main():
    print("=" * 80)
    print("ENRICHMENT STATUS REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    enrichment_dir = Path(settings.OUTPUT_DIR) / 'enrichment'
    status_file = enrichment_dir / 'enrichment_status.json'
    output_file = enrichment_dir / 'enriched_books.jsonl'
    
    # 1. Check Calibre library size
    try:
        conn = sqlite3.connect(f'file:{settings.CALIBRE_DB_PATH}?mode=ro', uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM books")
        total_library_books = cursor.fetchone()[0]
        conn.close()
    except Exception as e:
        print(f"⚠️  Could not query Calibre: {e}")
        total_library_books = "Unknown"
    
    # 2. Check scored books (try JSONL first, then CSV)
    jsonl_file = Path(settings.OUTPUT_DIR) / 'calibre_enrichment_ready.jsonl'
    scored_file = Path(settings.OUTPUT_DIR) / 'calibre_owned_scored_books.csv'

    if jsonl_file.exists():
        with open(jsonl_file, 'r') as f:
            scored_books = sum(1 for _ in f)
    elif scored_file.exists():
        with open(scored_file, 'r') as f:
            scored_books = sum(1 for _ in f) - 1  # Subtract header
    else:
        scored_books = 0
    
    # 3. Check enrichment status
    if status_file.exists():
        with open(status_file, 'r') as f:
            status_data = json.load(f)
        
        completed = sum(1 for v in status_data.values() if v.get('status') == 'completed')
        errors = sum(1 for v in status_data.values() if v.get('status') == 'error')
    else:
        status_data = {}
        completed = 0
        errors = 0
    
    # 4. Check ChromaDB
    try:
        import chromadb
        chroma_dir = Path('./book_vectors')
        if chroma_dir.exists():
            client = chromadb.PersistentClient(path=str(chroma_dir))
            try:
                collection = client.get_collection("book_metadata_embeddings")
                chromadb_count = collection.count()
            except:
                chromadb_count = 0
        else:
            chromadb_count = 0
    except ImportError:
        chromadb_count = "Not installed"
    
    # 5. Check enriched output file
    if output_file.exists():
        with open(output_file, 'r') as f:
            enriched_count = sum(1 for _ in f)
    else:
        enriched_count = 0
    
    # Print report
    print("📚 LIBRARY STATUS")
    print("-" * 80)
    print(f"Total books in Calibre:        {total_library_books:>10}")
    print(f"Books with quality scores:     {scored_books:>10}")
    if scored_books > 0:
        print(f"Coverage:                      {scored_books/total_library_books*100:>9.1f}%")
    print()
    
    print("🎨 ENRICHMENT STATUS")
    print("-" * 80)
    print(f"Books enriched (completed):    {completed:>10}")
    print(f"Books with errors:             {errors:>10}")
    print(f"Entries in ChromaDB:           {chromadb_count:>10}")
    print(f"Records in output file:        {enriched_count:>10}")
    
    if scored_books > 0:
        remaining = scored_books - completed
        print(f"Books remaining to enrich:     {remaining:>10}")
        
        if remaining > 0:
            estimated_cost = remaining * 0.021
            print(f"Estimated remaining cost:      ${estimated_cost:>9.2f}")
    print()
    
    # Calculate actual cost so far
    if completed > 0:
        actual_cost = completed * 0.021
        print("💰 COST TRACKING")
        print("-" * 80)
        print(f"Books processed:               {completed:>10}")
        print(f"Estimated cost incurred:       ${actual_cost:>9.2f}")
        print()
    
    # Show recent activity
    if status_data:
        print("📅 RECENT ACTIVITY (Last 10)")
        print("-" * 80)
        
        # Sort by date
        recent = sorted(
            [(k, v) for k, v in status_data.items() if v.get('status') == 'completed'],
            key=lambda x: x[1].get('processed_date', ''),
            reverse=True
        )[:10]
        
        for calibre_id, info in recent:
            date = info.get('processed_date', 'Unknown')[:19]  # Trim milliseconds
            title = info.get('title', 'Unknown')[:50]
            author = info.get('author', 'Unknown')[:30]
            print(f"{date}  {title:<50}  {author}")
        
        if not recent:
            print("   (No enriched books yet)")
        print()
    
    # Show errors if any
    if errors > 0:
        print("⚠️  ERRORS")
        print("-" * 80)
        error_books = [
            (k, v) for k, v in status_data.items() 
            if v.get('status') == 'error'
        ]
        for calibre_id, info in error_books[:5]:
            print(f"   Book ID {calibre_id}: {info.get('title', 'Unknown')}")
        
        if len(error_books) > 5:
            print(f"   ... and {len(error_books) - 5} more")
        print()
        print("   To retry errors, regenerate input with --force-regenerate")
        print()
    
    # Next steps
    print("📋 NEXT STEPS")
    print("-" * 80)
    
    if completed == 0:
        print("1. Generate input file:")
        print("   python3 src/dataenrichment/generate_enrichment_input.py")
        print()
        print("2. Run enrichment:")
        print("   python3 src/dataenrichment/enrich_books.py --batch-size 10  # Test first")
    elif remaining > 0:
        print("1. Generate updated input (includes new books):")
        print("   python3 src/dataenrichment/generate_enrichment_input.py")
        print()
        print("2. Continue enrichment:")
        print("   python3 src/dataenrichment/enrich_books.py --resume")
    else:
        print("✅ All scored books are enriched!")
        print()
        print("   To enrich new books:")
        print("   1. Add books to Calibre")
        print("   2. Run: python3 src/calibrebrowser/analyze_library.py --coverage")
        print("   3. Run: python3 src/dataenrichment/generate_enrichment_input.py")
        print("   4. Run: python3 src/dataenrichment/enrich_books.py")
    
    print()
    print("=" * 80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

