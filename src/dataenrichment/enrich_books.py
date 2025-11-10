#!/usr/bin/env python3
"""
Book Enrichment Pipeline
Processes books through Claude API → OpenAI Embeddings → ChromaDB
Tracks progress to avoid duplicate processing and API costs.

Usage:
    python3 src/dataenrichment/enrich_books.py
    python3 src/dataenrichment/enrich_books.py --resume
    python3 src/dataenrichment/enrich_books.py --batch-size 50
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config.settings import settings


class BookEnricher:
    """Enriches books with AI-generated metadata and embeddings"""
    
    def __init__(self, api_keys=None, input_file=None):
        self.enrichment_dir = Path(settings.OUTPUT_DIR) / 'enrichment'
        self.enrichment_dir.mkdir(exist_ok=True, parents=True)
        
        # Input/output files (allow custom input)
        self.input_file = self.enrichment_dir / (input_file or 'books_to_enrich.jsonl')
        self.output_file = self.enrichment_dir / 'enriched_books.jsonl'
        self.status_file = self.enrichment_dir / 'enrichment_status.json'
        self.progress_file = self.enrichment_dir / 'enrichment_progress.json'
        
        # API clients (lazy loaded)
        self._claude_client = None
        self._openai_client = None
        self._chroma_client = None
        self._chroma_collection = None
        
        # API keys
        self.api_keys = api_keys or {}
        
        # Statistics
        self.stats = {
            'total_books': 0,
            'processed': 0,
            'skipped': 0,
            'errors': 0,
            'claude_calls': 0,
            'openai_calls': 0,
            'start_time': None,
            'end_time': None
        }
    
    def init_claude(self):
        """Initialize Claude API client (lazy)"""
        if self._claude_client:
            return self._claude_client
        
        try:
            from anthropic import Anthropic
            
            # Try to get API key from multiple sources
            api_key = (
                self.api_keys.get('anthropic') or  # Passed in constructor
                settings.ANTHROPIC_API_KEY or       # From .env
                input("Enter Anthropic API key: ").strip()  # Prompt as last resort
            )
            
            if not api_key:
                raise ValueError("Anthropic API key not provided")
            
            self._claude_client = Anthropic(api_key=api_key)
            print("✓ Claude API initialized")
            return self._claude_client
        except ImportError:
            print("❌ Error: anthropic package not installed")
            print("   Install with: pip install anthropic")
            sys.exit(1)
    
    def init_openai(self):
        """Initialize OpenAI API client (lazy)"""
        if self._openai_client:
            return self._openai_client
        
        try:
            from openai import OpenAI
            
            # Try to get API key from multiple sources
            api_key = (
                self.api_keys.get('openai') or     # Passed in constructor
                settings.OPENAI_API_KEY or          # From .env
                input("Enter OpenAI API key: ").strip()  # Prompt as last resort
            )
            
            if not api_key:
                raise ValueError("OpenAI API key not provided")
            
            self._openai_client = OpenAI(api_key=api_key)
            print("✓ OpenAI API initialized")
            return self._openai_client
        except ImportError:
            print("❌ Error: openai package not installed")
            print("   Install with: pip install openai")
            sys.exit(1)
    
    def init_chromadb(self):
        """Initialize ChromaDB client and collection"""
        if self._chroma_collection:
            return self._chroma_collection
        
        try:
            import chromadb
            import os
            
            # Use configured path, expand ~ for home directory
            chroma_dir = Path(os.path.expanduser(settings.CHROMADB_PATH))
            chroma_dir.mkdir(exist_ok=True, parents=True)
            
            self._chroma_client = chromadb.PersistentClient(path=str(chroma_dir))
            
            # Get or create collection
            try:
                self._chroma_collection = self._chroma_client.get_collection(
                    "book_metadata_embeddings"
                )
                print("✓ ChromaDB collection found")
            except Exception:
                self._chroma_collection = self._chroma_client.create_collection(
                    name="book_metadata_embeddings",
                    metadata={"phase": "metadata_only", "hnsw:space": "cosine"}
                )
                print("✓ ChromaDB collection created")
            
            return self._chroma_collection
            
        except ImportError:
            print("❌ Error: chromadb package not installed")
            print("   Install with: pip install chromadb")
            sys.exit(1)
    
    def load_status(self):
        """Load enrichment status tracking"""
        if not self.status_file.exists():
            return {}
        
        with open(self.status_file, 'r') as f:
            return json.load(f)
    
    def save_status(self, status_data):
        """Save enrichment status tracking"""
        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
    
    def load_progress(self):
        """Load progress checkpoint"""
        if not self.progress_file.exists():
            return {'last_processed_index': -1}
        
        with open(self.progress_file, 'r') as f:
            return json.load(f)
    
    def save_progress(self, progress_data):
        """Save progress checkpoint"""
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
    
    def enrich_with_claude(self, book):
        """
        Call Claude API to generate enriched metadata.
        Returns dict with: tags, enhanced_description, themes, recommended_for, original_publication_year
        """
        claude = self.init_claude()
        
        prompt = f"""Generate enriched metadata for this book in JSON format.

Book Information:
- Title: {book['title']}
- Author: {book['author']}
- Quality Score: {book['quality_score']}
- Awards/Recognition: {book.get('awards_and_recognition', 'None')}
- Existing Description: {book.get('existing_description') or 'Not available'}

Please return ONLY valid JSON (no other text) with these fields:
{{
  "tags": [5-10 relevant topic/subject tags],
  "enhanced_description": "2-3 sentence description capturing the essence",
  "themes": [3-5 major themes or topics],
  "recommended_for": "one sentence describing ideal readers",
  "original_publication_year": YYYY (original first publication year, not reprints)
}}

Focus on literary content, themes, and topics. Be specific and descriptive.
For original_publication_year, provide the year of FIRST publication, not modern editions."""

        response = claude.messages.create(
            model="claude-3-5-haiku-20241022",  # Cost-effective
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        self.stats['claude_calls'] += 1
        
        # Parse JSON response
        content = response.content[0].text
        enrichment = json.loads(content)
        
        return enrichment
    
    def get_publication_year_openlibrary(self, title, author):
        """
        Query OpenLibrary API to get original publication year.
        Returns year as integer or None if not found.
        """
        try:
            import urllib.parse
            import urllib.request
            
            # Build query
            query = urllib.parse.quote(f"{title} {author}")
            url = f"https://openlibrary.org/search.json?q={query}&limit=1"
            
            # Query API
            req = urllib.request.Request(url, headers={'User-Agent': 'BookWise/1.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
            
            # Extract first publication year
            if data.get('docs') and len(data['docs']) > 0:
                doc = data['docs'][0]
                year = doc.get('first_publish_year')
                if year:
                    return int(year)
            
            return None
            
        except Exception as e:
            print(f"   ⚠️  OpenLibrary lookup failed: {e}")
            return None
    
    def create_embedding(self, book, enrichment):
        """
        Create vector embedding from enriched metadata.
        Returns 1536-dimensional embedding array.
        """
        openai = self.init_openai()
        
        # Combine all metadata for embedding
        embedding_text = f"""
Title: {book['title']}
Author: {book['author']}
Published: {enrichment.get('original_publication_year', 'Unknown')}
Description: {enrichment['enhanced_description']}
Tags: {', '.join(enrichment['tags'])}
Themes: {', '.join(enrichment['themes'])}
Quality Score: {book['quality_score']}
Awards: {book.get('awards_and_recognition', '')}
"""
        
        response = openai.embeddings.create(
            model="text-embedding-3-large",  # 1536 dimensions
            input=embedding_text.strip()
        )
        
        self.stats['openai_calls'] += 1
        
        return response.data[0].embedding
    
    def store_in_chromadb(self, book, enrichment, embedding):
        """Store enriched book with embedding in ChromaDB"""
        collection = self.init_chromadb()
        
        book_id = f"book_{book['calibre_id']}"
        
        collection.add(
            ids=[str(book['calibre_id'])],  # Use calibre_id directly
            embeddings=[embedding],
            metadatas=[{
                'title': book['title'],
                'author': book['author'],
                'quality_score': float(book['quality_score']),
                'tags': '|'.join(enrichment['tags']),  # Pipe-separated for easy parsing
                'themes': '|'.join(enrichment['themes']),
                'description': enrichment['enhanced_description'],
                'publication_year': enrichment.get('original_publication_year'),
                'awards': book.get('awards_and_recognition', ''),
                'enriched_at': datetime.now().isoformat()
            }]
        )
    
    def process_book(self, book):
        """
        Full pipeline for one book:
        1. Claude enrichment (with publication year)
        2. OpenLibrary fallback for publication year
        3. OpenAI embedding
        4. Store in ChromaDB
        5. Save to JSONL
        """
        try:
            print(f"\n📖 Processing: {book['title']}")
            print(f"   by {book['author']} (Score: {book['quality_score']})")
            
            # Step 1: Claude enrichment
            print("   → Calling Claude API...", end='', flush=True)
            enrichment = self.enrich_with_claude(book)
            print(" ✓")
            
            # Step 2: Validate/get publication year
            pub_year = enrichment.get('original_publication_year')
            if not pub_year or not isinstance(pub_year, int):
                print("   → Querying OpenLibrary for publication year...", end='', flush=True)
                pub_year = self.get_publication_year_openlibrary(book['title'], book['author'])
                if pub_year:
                    enrichment['original_publication_year'] = pub_year
                    print(f" ✓ {pub_year}")
                else:
                    print(" (not found)")
            else:
                print(f"   → Original publication year: {pub_year}")
            
            # Step 3: Create embedding
            print("   → Creating embedding...", end='', flush=True)
            embedding = self.create_embedding(book, enrichment)
            print(" ✓")
            
            # Step 4: Store in ChromaDB
            print("   → Storing in ChromaDB...", end='', flush=True)
            self.store_in_chromadb(book, enrichment, embedding)
            print(" ✓")
            
            # Step 5: Save enriched data
            enriched_book = {
                **book,
                **enrichment,
                'embedding_created': True,
                'processing_date': datetime.now().isoformat()
            }
            
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(enriched_book) + '\n')
            
            print("   ✓ Complete!")
            return True
            
        except Exception as e:
            print(f"\n   ❌ Error: {e}")
            return False
    
    def run(self, resume=False, batch_size=None, rate_limit_delay=1.0, skip_confirmation=False, force=False):
        """
        Run the enrichment pipeline.
        
        Args:
            resume: Continue from last checkpoint
            force: Re-enrich books even if already completed (for re-enrichment after score changes)
            batch_size: Process only N books (for testing)
            rate_limit_delay: Seconds to wait between API calls
            skip_confirmation: Skip confirmation prompt (for automation)
        """
        print("=" * 80)
        print("BOOK ENRICHMENT PIPELINE")
        print("=" * 80)
        
        # Check input file exists
        if not self.input_file.exists():
            print(f"\n❌ Input file not found: {self.input_file}")
            print("   Run: python3 src/dataenrichment/generate_enrichment_input.py")
            return
        
        # Load books to process
        print(f"\n📂 Loading books from: {self.input_file}")
        books = []
        with open(self.input_file, 'r', encoding='utf-8') as f:
            for line in f:
                books.append(json.loads(line))
        
        self.stats['total_books'] = len(books)
        print(f"✓ Loaded {len(books)} books")
        
        # Load status and progress
        status = self.load_status()
        progress = self.load_progress() if resume else {'last_processed_index': -1}
        
        start_index = progress['last_processed_index'] + 1
        
        if resume and start_index > 0:
            print(f"📍 Resuming from book #{start_index + 1}")
        
        # Limit batch if requested
        if batch_size:
            books = books[start_index:start_index + batch_size]
            print(f"⚠️  Limited to {batch_size} books for testing")
        else:
            books = books[start_index:]
        
        if not books:
            print("✓ No books to process!")
            return
        
        # Cost estimate
        estimated_cost = len(books) * 0.021  # $0.008 Claude + $0.013 OpenAI
        print(f"\n💰 Estimated cost: ${estimated_cost:.2f}")
        
        # Confirm before proceeding (skip if --yes flag)
        if not skip_confirmation:
            response = input(f"\nProcess {len(books)} books? (yes/no): ").lower().strip()
            if response not in ['yes', 'y']:
                print("❌ Cancelled")
                return
        else:
            print(f"\n✓ Auto-confirmed (--yes flag)")
            print(f"  Processing {len(books)} books...")
        
        # Process books
        print("\n" + "=" * 80)
        print("PROCESSING BOOKS")
        print("=" * 80)
        
        self.stats['start_time'] = datetime.now()
        
        for i, book in enumerate(books, start=start_index):
            calibre_id = str(book['calibre_id'])
            
            # Skip if already processed (unless force flag is set)
            if not force and calibre_id in status and status[calibre_id].get('status') == 'completed':
                print(f"\n⏭️  Skipping {book['title']} (already completed)")
                self.stats['skipped'] += 1
                continue
            
            # Process book
            success = self.process_book(book)
            
            if success:
                # Update status
                status[calibre_id] = {
                    'status': 'completed',
                    'processed_date': datetime.now().isoformat(),
                    'title': book['title'],
                    'author': book['author']
                }
                self.stats['processed'] += 1
            else:
                # Mark as error
                status[calibre_id] = {
                    'status': 'error',
                    'error_date': datetime.now().isoformat(),
                    'title': book['title'],
                    'author': book['author']
                }
                self.stats['errors'] += 1
            
            # Save progress checkpoint
            self.save_progress({'last_processed_index': i})
            self.save_status(status)
            
            # Rate limiting
            if i < len(books) - 1:
                time.sleep(rate_limit_delay)
        
        self.stats['end_time'] = datetime.now()
        
        # Final report
        self._print_summary()
    
    def _print_summary(self):
        """Print processing summary"""
        print("\n" + "=" * 80)
        print("ENRICHMENT COMPLETE")
        print("=" * 80)
        
        elapsed = self.stats['end_time'] - self.stats['start_time']
        
        print(f"\n📊 Statistics:")
        print(f"   Total books:        {self.stats['total_books']}")
        print(f"   Successfully processed: {self.stats['processed']}")
        print(f"   Skipped (already done): {self.stats['skipped']}")
        print(f"   Errors:            {self.stats['errors']}")
        print(f"   Claude API calls:  {self.stats['claude_calls']}")
        print(f"   OpenAI API calls:  {self.stats['openai_calls']}")
        print(f"   Time elapsed:      {elapsed}")
        
        actual_cost = (self.stats['claude_calls'] * 0.008 + 
                      self.stats['openai_calls'] * 0.013)
        print(f"   Estimated cost:    ${actual_cost:.2f}")
        
        print(f"\n📁 Output files:")
        print(f"   Enriched data:  {self.output_file}")
        print(f"   Status tracking: {self.status_file}")
        print(f"   ChromaDB:       ./book_vectors/")
        
        print("\n✅ Next steps:")
        print("   1. Verify results: cat output/enrichment/enriched_books.jsonl")
        print("   2. Test semantic search (example script coming soon)")
        print("   3. Generate Calibre import with enriched tags")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enrich books with AI-generated metadata and embeddings",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from last checkpoint'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=None,
        help='Process only N books (for testing)'
    )
    
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=1.0,
        help='Delay between API calls in seconds (default: 1.0)'
    )
    
    parser.add_argument(
        '--yes',
        action='store_true',
        help='Skip confirmation prompt (for automation)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show enrichment status and exit'
    )
    
    parser.add_argument(
        '--input',
        type=str,
        help='Custom input file (default: books_to_enrich.jsonl)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-enrichment even if books are already completed'
    )
    
    args = parser.parse_args()
    
    # Handle status mode
    if args.status:
        show_status()
        return
    
    try:
        enricher = BookEnricher(input_file=args.input)
        enricher.run(
            resume=args.resume,
            batch_size=args.batch_size,
            rate_limit_delay=args.rate_limit,
            skip_confirmation=args.yes,
            force=bool(args.input)  # Force re-enrichment when using custom input file
        )
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        print("   Progress saved. Run with --resume to continue.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

