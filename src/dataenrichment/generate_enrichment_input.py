#!/usr/bin/env python3
"""
Generate Enrichment Input File
Creates JSONL file with only un-enriched books from your Calibre library.
Ensures no duplicate processing to avoid unnecessary API costs.

Usage:
    python3 src/dataenrichment/generate_enrichment_input.py
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config.settings import settings


class EnrichmentInputGenerator:
    """Generates input files for book enrichment, excluding already-processed books"""
    
    def __init__(self):
        self.calibre_db = settings.CALIBRE_DB_PATH
        self.output_dir = Path(settings.OUTPUT_DIR)
        self.enrichment_dir = Path(settings.OUTPUT_DIR) / 'enrichment'
        self.enrichment_dir.mkdir(exist_ok=True, parents=True)
        
        # Tracking files
        self.status_file = self.enrichment_dir / 'enrichment_status.json'
        self.input_file = self.enrichment_dir / 'books_to_enrich.jsonl'
        self.completed_file = self.enrichment_dir / 'enriched_books.jsonl'
    
    def load_enrichment_status(self):
        """
        Load tracking data for which books have been enriched.
        Returns dict: {calibre_id: status_info}
        """
        if not self.status_file.exists():
            return {}
        
        with open(self.status_file, 'r') as f:
            return json.load(f)
    
    def save_enrichment_status(self, status_data):
        """Save enrichment status tracking"""
        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
    
    def get_library_books_with_scores(self):
        """
        Load books from enrichment-ready JSONL (preferred) or
        query Calibre library directly (legacy).
        """
        print("Loading library books with metadata...")

        # Try to load from JSONL first (already has all metadata)
        jsonl_file = self.output_dir / 'calibre_enrichment_ready.jsonl'

        if jsonl_file.exists():
            print(f"📂 Loading from {jsonl_file.name}...")
            library_books = {}

            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    book = json.loads(line)
                    calibre_id = int(book['calibre_id'])
                    library_books[calibre_id] = book

            print(f"✓ Loaded {len(library_books):,} books from enrichment-ready JSONL")
            return library_books

        # Fall back to querying Calibre database (legacy)
        print("⚠️  JSONL not found, querying Calibre database directly...")
        print("   Consider regenerating with: python3 src/calibrebrowser/analyze_library.py --coverage")

        # Read-only connection to Calibre
        conn = sqlite3.connect(f'file:{self.calibre_db}?mode=ro', uri=True)
        cursor = conn.cursor()

        # Get all books with authors and metadata
        query = """
        SELECT
            b.id as calibre_id,
            b.title,
            a.name as author,
            c.text as description,
            b.pubdate,
            b.path,
            b.timestamp as date_added
        FROM books b
        LEFT JOIN books_authors_link ba ON b.id = ba.book
        LEFT JOIN authors a ON ba.author = a.id
        LEFT JOIN comments c ON b.id = c.book
        ORDER BY b.id
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        # Convert to dict
        library_books = {}
        for row in rows:
            calibre_id = row[0]
            library_books[calibre_id] = {
                'calibre_id': calibre_id,
                'title': row[1],
                'author': row[2],
                'existing_description': row[3] or None,
                'publication_date': row[4],
                'file_path': row[5],
                'date_added': row[6]
            }

        conn.close()

        print(f"✓ Found {len(library_books):,} books in Calibre library")
        return library_books
    
    def load_quality_scores(self):
        """
        Load quality scores from calibre_enrichment_ready.jsonl (new format)
        or calibre_owned_scored_books.csv (legacy format)
        Returns dict: {calibre_id: score_info}
        """
        print("\nLoading quality scores...")

        # Try new JSONL format first
        jsonl_file = self.output_dir / 'calibre_enrichment_ready.jsonl'

        if jsonl_file.exists():
            print(f"📂 Loading from {jsonl_file.name} (enrichment-ready format)...")
            scores = {}

            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    book = json.loads(line)
                    calibre_id = int(book['calibre_id'])
                    scores[calibre_id] = {
                        'quality_score': float(book['quality_score']),
                        'awards_and_recognition': book.get('awards_and_recognition', ''),
                        'quality_tier': book.get('quality_tier', ''),
                        'enrichment_priority': book.get('enrichment_priority', 'medium')
                    }

            print(f"✓ Loaded {len(scores):,} quality scores from JSONL")
            return scores

        # Fall back to legacy CSV format
        scored_file = self.output_dir / 'calibre_owned_scored_books.csv'

        if scored_file.exists():
            print(f"⚠️  Loading from {scored_file.name} (legacy format)")
            print("   Consider regenerating with: python3 src/calibrebrowser/analyze_library.py --coverage")

            import csv
            scores = {}

            with open(scored_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    calibre_id = int(row['calibre_id'])
                    scores[calibre_id] = {
                        'quality_score': float(row['score']),
                        'awards_and_recognition': row.get('recognition', '')
                    }

            print(f"✓ Loaded {len(scores):,} quality scores from CSV")
            return scores

        # No file found
        print("❌ No quality scores found!")
        print("   Run: python3 src/calibrebrowser/analyze_library.py --coverage")
        return {}
    
    def check_chromadb_status(self):
        """
        Check ChromaDB to see which books already have embeddings.
        Returns set of calibre_ids that are already embedded.
        """
        chroma_dir = Path('./book_vectors')
        
        if not chroma_dir.exists():
            print("\n✓ ChromaDB not initialized (will create on first run)")
            return set()
        
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(chroma_dir))
            
            # Try to get the collection
            try:
                collection = client.get_collection("book_metadata_embeddings")
                existing_ids = collection.get()['ids']
                
                # Convert to calibre_id integers
                embedded_ids = set()
                for id_str in existing_ids:
                    try:
                        # IDs are stored as "book_123" or just "123"
                        if id_str.startswith('book_'):
                            embedded_ids.add(int(id_str.split('_')[1]))
                        else:
                            embedded_ids.add(int(id_str))
                    except (ValueError, IndexError):
                        continue
                
                print(f"\n✓ Found {len(embedded_ids):,} books already in ChromaDB")
                return embedded_ids
            
            except Exception:
                print("\n✓ ChromaDB collection not found (will create on first run)")
                return set()
        
        except ImportError:
            print("\n⚠️  ChromaDB not installed (install with: pip install chromadb)")
            return set()
    
    def generate_input_file(self, min_quality_score=0, max_books=None):
        """
        Generate JSONL input file with only un-enriched books.
        
        Args:
            min_quality_score: Minimum quality score to include (default: 0 = all)
            max_books: Maximum books to include (for testing, default: None = all)
        """
        print("\n" + "=" * 80)
        print("GENERATING ENRICHMENT INPUT FILE")
        print("=" * 80)
        
        # Load all data sources
        library_books = self.get_library_books_with_scores()
        enrichment_status = self.load_enrichment_status()
        embedded_ids = self.check_chromadb_status()

        # Filter books that need enrichment
        print("\n" + "-" * 80)
        print("FILTERING BOOKS")
        print("-" * 80)

        books_to_enrich = []

        for calibre_id, book_info in library_books.items():
            # Check 1: Must have quality score
            if 'quality_score' not in book_info:
                continue

            # Check 2: Must meet minimum quality threshold
            if book_info['quality_score'] < min_quality_score:
                continue

            # Check 3: Must not be already enriched in tracking file
            if str(calibre_id) in enrichment_status:
                status = enrichment_status[str(calibre_id)]
                if status.get('status') == 'completed':
                    continue

            # Check 4: Must not be in ChromaDB already
            if calibre_id in embedded_ids:
                continue

            # This book needs enrichment!
            books_to_enrich.append(book_info)

        print(f"📊 Filtering Results:")
        print(f"   Books in library:           {len(library_books):>6,}")
        print(f"   Already enriched (tracked): {len(enrichment_status):>6,}")
        print(f"   Already in ChromaDB:        {len(embedded_ids):>6,}")
        print(f"   Score threshold (>= {min_quality_score}):     {len([b for b in books_to_enrich]):>6,}")
        print(f"   → Books to enrich:          {len(books_to_enrich):>6,}")
        
        if not books_to_enrich:
            print("\n✓ No books need enrichment - all caught up!")
            return 0
        
        # Sort by quality score (enrich highest quality first)
        books_to_enrich.sort(key=lambda x: x['quality_score'], reverse=True)
        
        # Limit if requested
        if max_books:
            books_to_enrich = books_to_enrich[:max_books]
            print(f"\n⚠️  Limited to {max_books} books for testing")
        
        # Write JSONL file
        print(f"\n📝 Writing input file: {self.input_file}")
        
        with open(self.input_file, 'w', encoding='utf-8') as f:
            for book in books_to_enrich:
                # Create enrichment input record
                record = {
                    'book_id': str(book['calibre_id']),
                    'calibre_id': book['calibre_id'],
                    'title': book['title'],
                    'author': book['author'],
                    'quality_score': book['quality_score'],
                    'awards_and_recognition': book['awards_and_recognition'],
                    'existing_description': book.get('existing_description'),
                    'publication_date': book.get('publication_date'),
                    'file_path': book.get('file_path')
                }
                f.write(json.dumps(record) + '\n')
        
        print(f"✓ Created: {self.input_file}")
        print(f"  {len(books_to_enrich)} books ready for enrichment")
        
        # Generate summary report
        self._generate_summary_report(books_to_enrich)
        
        return len(books_to_enrich)
    
    def _generate_summary_report(self, books_to_enrich):
        """Generate human-readable summary report"""
        report_file = self.enrichment_dir / 'enrichment_plan.txt'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("ENRICHMENT PLAN\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total books to enrich: {len(books_to_enrich)}\n")
            f.write("\n")
            
            # Cost estimate
            claude_cost = len(books_to_enrich) * 0.008  # ~$0.008 per book with Haiku
            openai_cost = len(books_to_enrich) * 0.013  # ~$0.013 per book for embedding
            total_cost = claude_cost + openai_cost
            
            f.write("ESTIMATED COSTS:\n")
            f.write("-" * 80 + "\n")
            f.write(f"Claude API (Haiku):      ${claude_cost:>8.2f}\n")
            f.write(f"OpenAI Embeddings:       ${openai_cost:>8.2f}\n")
            f.write(f"Total estimated cost:    ${total_cost:>8.2f}\n")
            f.write("\n")
            
            # Quality distribution
            f.write("QUALITY SCORE DISTRIBUTION:\n")
            f.write("-" * 80 + "\n")
            score_ranges = {
                '90+  (Legendary)': 0,
                '80-89 (Exceptional)': 0,
                '70-79 (Outstanding)': 0,
                '60-69 (Excellent)': 0,
                '50-59 (Very Good)': 0,
                '40-49 (Good)': 0,
                '30-39 (Solid)': 0,
                '<30  (Other)': 0
            }
            
            for book in books_to_enrich:
                score = book['quality_score']
                if score >= 90:
                    score_ranges['90+  (Legendary)'] += 1
                elif score >= 80:
                    score_ranges['80-89 (Exceptional)'] += 1
                elif score >= 70:
                    score_ranges['70-79 (Outstanding)'] += 1
                elif score >= 60:
                    score_ranges['60-69 (Excellent)'] += 1
                elif score >= 50:
                    score_ranges['50-59 (Very Good)'] += 1
                elif score >= 40:
                    score_ranges['40-49 (Good)'] += 1
                elif score >= 30:
                    score_ranges['30-39 (Solid)'] += 1
                else:
                    score_ranges['<30  (Other)'] += 1
            
            for range_name, count in score_ranges.items():
                if count > 0:
                    f.write(f"{range_name}: {count:>6} books\n")
            
            f.write("\n")
            
            # Top 20 books
            f.write("TOP 20 BOOKS TO ENRICH (by quality score):\n")
            f.write("-" * 80 + "\n")
            for i, book in enumerate(books_to_enrich[:20], 1):
                f.write(f"{i:>3}. [{book['quality_score']:>5.1f}] {book['title']}\n")
                f.write(f"      by {book['author']}\n")
            
            if len(books_to_enrich) > 20:
                f.write(f"\n... and {len(books_to_enrich) - 20} more books\n")
        
        print(f"✓ Created: {report_file}")
        print()
        print("=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print()
        print(f"1. Review the plan: cat {report_file}")
        print(f"2. Run enrichment:  python3 src/dataenrichment/enrich_books.py")
        print(f"3. Embeddings will be stored in: ./book_vectors/")
        print(f"4. Status tracked in: {self.status_file}")
        print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate input file for book enrichment (Claude + OpenAI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate input for all unprocessed books
  python3 src/dataenrichment/generate_enrichment_input.py
  
  # Only enrich high-quality books (score >= 70)
  python3 src/dataenrichment/generate_enrichment_input.py --min-score 70
  
  # Test with just 10 books
  python3 src/dataenrichment/generate_enrichment_input.py --max-books 10
  
  # Top tier only (score >= 50)
  python3 src/dataenrichment/generate_enrichment_input.py --min-score 50
        """
    )
    
    parser.add_argument(
        '--min-score',
        type=float,
        default=0,
        help='Minimum quality score to include (default: 0 = all scored books)'
    )
    
    parser.add_argument(
        '--max-books',
        type=int,
        default=None,
        help='Maximum number of books to include (for testing)'
    )
    
    parser.add_argument(
        '--force-regenerate',
        action='store_true',
        help='Regenerate input even if already exists'
    )
    
    args = parser.parse_args()
    
    try:
        generator = EnrichmentInputGenerator()
        
        # Check if input file already exists
        if generator.input_file.exists() and not args.force_regenerate:
            print(f"⚠️  Input file already exists: {generator.input_file}")
            print(f"   Use --force-regenerate to recreate it")
            print(f"   Or run enrichment with existing file:")
            print(f"   python3 src/dataenrichment/enrich_books.py")
            return
        
        count = generator.generate_input_file(
            min_quality_score=args.min_score,
            max_books=args.max_books
        )
        
        if count == 0:
            print("✓ All books are already enriched!")
            print("  Nothing to do.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

