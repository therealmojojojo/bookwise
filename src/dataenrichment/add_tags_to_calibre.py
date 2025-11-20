#!/usr/bin/env python3
"""
Add Enrichment Tags to Calibre
Adds AI-generated tags and canonical award names to Calibre books as regular tags.
No custom columns needed - uses Calibre's built-in tags system.

Features:
- Smart tracking: Skip books that haven't changed
- Preserves user's manual tags
- Hash-based comparison for efficiency
- Logging for debugging
- Status reporting

Usage:
    python3 src/dataenrichment/add_tags_to_calibre.py --dry-run  # Preview
    python3 src/dataenrichment/add_tags_to_calibre.py --yes      # Apply
    python3 src/dataenrichment/add_tags_to_calibre.py --status   # Show status
    python3 src/dataenrichment/add_tags_to_calibre.py --force    # Re-import all
    python3 src/dataenrichment/add_tags_to_calibre.py --verify   # Verify setup
"""

import json
import subprocess
import sys
import hashlib
import logging
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config.settings import settings

# Setup logging
def setup_logging():
    """Configure logging based on environment settings"""
    log_level = getattr(settings, 'LOG_LEVEL', 'INFO')
    log_file = getattr(settings, 'LOG_FILE', None)

    # Create logger
    logger = logging.getLogger('calibre_import')
    logger.setLevel(getattr(logging, log_level))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (if configured)
    if log_file:
        log_file_path = Path(os.path.expanduser(log_file))
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger

logger = setup_logging()


# Load canonical authors once at module level
CANONICAL_AUTHORS_CACHE = {}

def load_canonical_authors():
    """Load canonical authors from datasources"""
    if CANONICAL_AUTHORS_CACHE:
        return CANONICAL_AUTHORS_CACHE
    
    datasources_dir = Path(settings.DATASOURCES_DIR)
    
    for tier in ['s', 'a', 'b']:
        tier_file = datasources_dir / f'canonical_authors_tier_{tier}.json'
        if tier_file.exists():
            with open(tier_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for author_entry in data.get('canonical_authors', []):
                    author_name = author_entry['author'].lower()
                    CANONICAL_AUTHORS_CACHE[author_name] = tier.upper()
    
    return CANONICAL_AUTHORS_CACHE

def get_canonical_tier_tag(author_name):
    """Get canonical tier tag for an author if they're in a tier"""
    if not author_name:
        return None
    
    canonical_authors = load_canonical_authors()
    
    # Normalize author name (handle "Last, First" format and multiple authors)
    author_parts = author_name.split('&')[0].strip()  # Take first author if multiple
    author_lower = author_parts.lower()
    
    # Check exact match first
    if author_lower in canonical_authors:
        tier = canonical_authors[author_lower]
        return f"Canon: Tier {tier}"
    
    # Check if any canonical author name is in this author string
    for canon_name, tier in canonical_authors.items():
        if canon_name in author_lower or author_lower in canon_name:
            return f"Canon: Tier {tier}"
    
    return None


# =============================================================================
# STATUS TRACKING FUNCTIONS
# =============================================================================

def get_status_file_path():
    """Get path to status file, expanding ~ to home directory"""
    status_file = getattr(settings, 'CALIBRE_IMPORT_STATUS_FILE',
                         '~/Library/Application Support/bookwise/calibre_import_status.json')
    return Path(os.path.expanduser(status_file))


def load_status_file():
    """Load import status tracking file"""
    status_file = get_status_file_path()

    if not status_file.exists():
        logger.debug(f"Status file not found: {status_file}")
        return {
            "version": "1.0",
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "books": {}
        }

    try:
        with open(status_file, 'r') as f:
            data = json.load(f)
            logger.debug(f"Loaded status file with {len(data.get('books', {}))} books")
            return data
    except Exception as e:
        logger.warning(f"Failed to load status file: {e}. Starting fresh.")
        return {
            "version": "1.0",
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "books": {}
        }


def save_status_file(status_data):
    """Save import status tracking file"""
    status_file = get_status_file_path()

    # Create directory if it doesn't exist
    status_file.parent.mkdir(parents=True, exist_ok=True)

    # Update timestamp
    status_data["last_updated"] = datetime.utcnow().isoformat() + "Z"

    try:
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
        logger.debug(f"Saved status file: {status_file}")
    except Exception as e:
        logger.error(f"Failed to save status file: {e}")


def calculate_hash(data):
    """Calculate SHA256 hash of data for comparison"""
    if data is None:
        return None

    if isinstance(data, list):
        # Sort list for consistent hashing
        data = sorted(str(item) for item in data)
        data_str = ','.join(data)
    else:
        data_str = str(data)

    return hashlib.sha256(data_str.encode('utf-8')).hexdigest()


def is_bookwise_tag(tag):
    """Check if tag is a BookWise-generated tag"""
    bookwise_prefixes = ('Award:', 'List:', 'Canon:', 'Topic:', 'Series:')
    return tag.startswith(bookwise_prefixes)


def update_book_status(status_data, calibre_id, tags_hash, desc_hash, enriched_at=None):
    """Update status for a single book"""
    book_id = str(calibre_id)
    now = datetime.utcnow().isoformat() + "Z"

    if book_id not in status_data["books"]:
        status_data["books"][book_id] = {}

    status_data["books"][book_id].update({
        "last_checked": now,
        "last_imported": now,
        "tags_hash": tags_hash,
        "description_hash": desc_hash
    })

    if enriched_at:
        status_data["books"][book_id]["enriched_at"] = enriched_at


def show_import_status(status_data, chromadb_collection):
    """Display import status report"""
    print("\n" + "="*60)
    print("CALIBRE IMPORT STATUS REPORT")
    print("="*60)

    # Get total books in ChromaDB
    chroma_count = chromadb_collection.count()
    tracked_count = len(status_data.get("books", {}))

    print(f"\nBooks in ChromaDB: {chroma_count}")
    print(f"Books tracked in status file: {tracked_count}")
    print(f"Last updated: {status_data.get('last_updated', 'Unknown')}")

    if tracked_count > 0:
        # Show recent imports
        books = status_data.get("books", {})
        recent = sorted(
            [(book_id, info) for book_id, info in books.items()],
            key=lambda x: x[1].get('last_imported', ''),
            reverse=True
        )[:10]

        print(f"\nMost recent imports (last 10):")
        for book_id, info in recent:
            last_import = info.get('last_imported', 'Unknown')
            print(f"  Book {book_id}: {last_import}")

    print("\n" + "="*60)


# Canonical tag mapping for all awards, lists, and series
CANONICAL_TAG_NAMES = {
    # CAREER AWARDS
    'nobel prize in literature': 'Award: Nobel Prize in Literature',
    'miguel de cervantes prize': 'Award: Miguel de Cervantes Prize',
    'georg büchner prize': 'Award: Georg Büchner Prize',
    
    # MAJOR FICTION AWARDS
    'pulitzer prize for fiction': 'Award: Pulitzer Prize - Fiction',
    'booker prize': 'Award: Booker Prize',
    'man booker prize': 'Award: Booker Prize',  # Same prize, name changed
    
    # SIGNIFICANT FICTION AWARDS
    'national book award - fiction': 'Award: National Book Award - Fiction',
    'women\'s prize for fiction': 'Award: Women\'s Prize for Fiction',
    'nbcc award - fiction': 'Award: NBCC Award - Fiction',
    'dublin literary award': 'Award: Dublin Literary Award',
    'pen/faulkner award': 'Award: PEN/Faulkner Award',
    'prix goncourt': 'Award: Prix Goncourt',
    
    # NOTABLE FICTION AWARDS
    'los angeles times book prize - fiction': 'Award: LA Times Book Prize - Fiction',
    'kirkus prize - fiction': 'Award: Kirkus Prize - Fiction',
    'kirkus prize - yrl': 'Award: Kirkus Prize - Young Readers',
    
    # GENRE AWARDS
    'hugo award': 'Award: Hugo Award',
    'nebula award': 'Award: Nebula Award',
    
    # NONFICTION AWARDS
    'pulitzer prize for biography': 'Award: Pulitzer Prize - Biography',
    'pulitzer prize for history': 'Award: Pulitzer Prize - History',
    'pulitzer prize for general nonfiction': 'Award: Pulitzer Prize - General Nonfiction',
    'national book award - nonfiction': 'Award: National Book Award - Nonfiction',
    'nbcc award - biography': 'Award: NBCC Award - Biography',
    'nbcc award - history': 'Award: NBCC Award - History',
    'nbcc award - general nonfiction': 'Award: NBCC Award - General Nonfiction',
    'los angeles times book prize - nonfiction': 'Award: LA Times Book Prize - Nonfiction',
    
    # BEST-OF LISTS
    'modern library 100 best novels': 'List: Modern Library 100 Best Novels',
    'modern library 100 best nonfiction': 'List: Modern Library 100 Best Nonfiction',
    'nytimes 100 best novels': 'List: NYTimes 100 Best Novels',
    'the guardian best novels': 'List: The Guardian Best Novels',
    'time magazine 100 best novels': 'List: Time Magazine 100 Best Novels',
    'bbc 100 best novels': 'List: BBC 100 Best Novels',
    'le monde 100 best novels': 'List: Le Monde 100 Best Novels',
    'norwegian book club 100 best books': 'List: Norwegian Book Club 100 Best',
    'harold bloom western canon': 'List: Harold Bloom Western Canon',
    'the telegraph 100 novels everyone should read': 'List: The Telegraph 100 Novels',
    'the observer 100 greatest novels': 'List: The Observer 100 Greatest Novels',
    'goodreads choice awards': 'List: Goodreads Choice Awards',
    'goodreads choice fiction': 'List: Goodreads Choice Awards - Fiction',
    
    # CLASSIC SERIES
    'penguin classics': 'Series: Penguin Classics',
    
    # EDUCATIONAL CANON
    'st. john\'s college great books program': 'Canon: St. John\'s College Great Books',
    'st. johns college great books': 'Canon: St. John\'s College Great Books',
    'columbia core curriculum': 'Canon: Columbia Core Curriculum',
    'columbia literature humanities': 'Canon: Columbia Core Curriculum',
    'university of chicago common core reading list': 'Canon: University of Chicago Common Core',
    'uchicago common core': 'Canon: University of Chicago Common Core',
    'national endowment for the arts - big read library': 'List: NEA Big Read Library',
    'nea big read library': 'List: NEA Big Read Library',
}


def extract_canonical_tags(recognition_string):
    """
    Extract canonical tag names from recognition string.
    Handles awards, lists, series, and educational canon.
    Includes year for awards and ranking for lists.
    
    Examples:
        "Nobel Prize in Literature 1962" -> "Award: Nobel Prize in Literature (1962)"
        "Modern Library 100 Best Novels #10" -> "List: Modern Library 100 Best Novels #10"
    """
    if not recognition_string:
        return []
    
    import re
    
    canonical_tags = []
    parts = recognition_string.split(';')
    
    for part in parts:
        original_part = part.strip()
        part_lower = original_part.lower()
        
        # Extract year (4-digit number at the end)
        year_match = re.search(r'\b(19\d{2}|20\d{2})$', original_part)
        year = year_match.group(1) if year_match else None
        
        # Extract ranking (e.g., "#10", "#None")
        ranking_match = re.search(r'#(\d+|None)$', original_part)
        ranking = ranking_match.group(1) if ranking_match else None
        
        # Clean part for matching (remove year and ranking)
        part_clean = part_lower
        if year:
            part_clean = re.sub(r'\b(19\d{2}|20\d{2})$', '', part_clean).strip()
        if ranking:
            part_clean = re.sub(r'#(\d+|None)$', '', part_clean).strip()
        
        # Check against known recognition
        matched = False
        for pattern, canonical in CANONICAL_TAG_NAMES.items():
            if pattern in part_clean:
                # Build enhanced tag with year/ranking
                enhanced_tag = canonical
                
                if canonical.startswith('Award:') and year:
                    # Add year to awards: "Award: Nobel Prize in Literature (1962)"
                    enhanced_tag = f"{canonical} ({year})"
                elif canonical.startswith('List:') and ranking and ranking != 'None':
                    # Add ranking to lists: "List: Modern Library 100 Best Novels #10"
                    enhanced_tag = f"{canonical} #{ranking}"
                
                if enhanced_tag not in canonical_tags:
                    canonical_tags.append(enhanced_tag)
                matched = True
                break
        
        # If no match but contains "list" or "best", create generic list tag
        if not matched and any(word in part_clean for word in ['list', 'best', '100']):
            # Clean up the part and create a tag
            clean_part = original_part.split('#')[0].strip()
            if clean_part and len(clean_part) > 5:  # Avoid very short strings
                generic_tag = f"List: {clean_part}"
                if ranking and ranking != 'None':
                    generic_tag = f"{generic_tag} #{ranking}"
                if generic_tag not in canonical_tags:
                    canonical_tags.append(generic_tag)
    
    return canonical_tags


def load_enriched_books(input_file=None, calibre_ids=None):
    """Load enriched books from ChromaDB (primary) or JSONL file (fallback)
    
    Args:
        input_file: Optional custom JSONL input file (for backward compatibility)
        calibre_ids: Optional list of specific calibre IDs to load
    
    Returns:
        List of enriched book dictionaries
    """
    import chromadb
    from pathlib import Path
    import os
    
    # If input_file specified, use legacy JSONL loading
    if input_file:
        enrichment_dir = Path(settings.OUTPUT_DIR) / 'enrichment'
        enriched_file = enrichment_dir / input_file
        
        if not enriched_file.exists():
            print(f"❌ Enriched books file not found: {enriched_file}")
            return []
        
        books = []
        with open(enriched_file, 'r', encoding='utf-8') as f:
            for line in f:
                books.append(json.loads(line))
        return books
    
    # Primary: Load from ChromaDB
    try:
        chromadb_path = os.path.expanduser(settings.CHROMADB_PATH)
        client = chromadb.PersistentClient(path=chromadb_path)
        collection = client.get_collection("book_metadata_embeddings")
        
        # Get embeddings and metadata
        if calibre_ids:
            results = collection.get(
                ids=[str(id) for id in calibre_ids],
                include=['metadatas']
            )
        else:
            results = collection.get(include=['metadatas'])
        
        # Convert ChromaDB format to book dictionary format
        books = []
        for i, calibre_id in enumerate(results['ids']):
            metadata = results['metadatas'][i]
            
            # Parse pipe-separated tags and themes
            tags = metadata.get('tags', '').split('|') if metadata.get('tags') else []
            themes = metadata.get('themes', '').split('|') if metadata.get('themes') else []
            
            book = {
                'calibre_id': int(calibre_id),
                'title': metadata['title'],
                'author': metadata['author'],
                'quality_score': float(metadata.get('quality_score', 0)),
                'tags': [t for t in tags if t],  # Filter empty strings
                'themes': [t for t in themes if t],
                'enhanced_description': metadata.get('description', ''),
                'original_publication_year': metadata.get('publication_year'),
                'awards_and_recognition': metadata.get('awards', ''),
                'enriched_at': metadata.get('enriched_at', '')
            }
            books.append(book)
        
        return books
        
    except Exception as e:
        print(f"⚠️  Could not load from ChromaDB: {e}")
        print("   Falling back to JSONL file...")
        
        # Fallback: Try to load from enriched_books.jsonl
        enrichment_dir = Path(settings.OUTPUT_DIR) / 'enrichment'
        enriched_file = enrichment_dir / 'enriched_books.jsonl'
        
        if enriched_file.exists():
            books = []
            with open(enriched_file, 'r', encoding='utf-8') as f:
                for line in f:
                    books.append(json.loads(line))
            return books
        else:
            print(f"❌ No enriched data found in ChromaDB or JSONL")
            print("   Run enrichment first: python3 src/dataenrichment/enrich_books.py")
            return []


def get_existing_tags(calibre_id, library_path):
    """Get existing tags for a book."""
    try:
        cmd = [
            settings.CALIBREDB_PATH, 'list',
            '--fields', 'tags',
            '--for-machine',
            f'--library-path={library_path}',
            '--search', f'id:{calibre_id}'
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        import json
        books = json.loads(result.stdout)
        
        if books and len(books) > 0:
            existing = books[0].get('tags', [])
            # Tags come back as a list or comma-separated string
            if isinstance(existing, str):
                return [t.strip() for t in existing.split(',') if t.strip()]
            elif isinstance(existing, list):
                return existing
        
        return []
        
    except Exception as e:
        logger.warning(f"Could not read existing tags for book {calibre_id}: {e}")
        return []


def add_tags_to_book(calibre_id, tags, library_path, dry_run=False, force=False, status_data=None):
    """
    Add tags to a Calibre book using calibredb with smart comparison.

    Smart logic:
    1. Read existing tags from Calibre
    2. Separate BookWise tags (Award:, List:, Canon:, Topic:, Series:) from user tags
    3. Compare BookWise tags with expected tags
    4. If identical → SKIP (no update needed)
    5. If different or missing → UPDATE (replace BookWise tags, preserve user tags)

    Args:
        calibre_id: Calibre book ID
        tags: List of expected BookWise tags
        library_path: Path to Calibre library
        dry_run: If True, only show what would be done
        force: If True, always update regardless of comparison
        status_data: Status tracking dictionary

    Returns:
        tuple: (action_taken, success) where action_taken is 'skip', 'add', or 'update'
    """
    if not tags:
        return ('skip', True)

    # Get existing tags from Calibre
    existing_tags = get_existing_tags(calibre_id, library_path)

    # Separate BookWise tags from user tags
    existing_bookwise = [t for t in existing_tags if is_bookwise_tag(t)]
    user_tags = [t for t in existing_tags if not is_bookwise_tag(t)]

    # Calculate hashes for comparison (normalize to lowercase to ignore Calibre's capitalization)
    expected_hash = calculate_hash(sorted([t.lower() for t in tags]))
    existing_hash = calculate_hash(sorted([t.lower() for t in existing_bookwise]))

    # Decide action
    action = 'skip'
    if force:
        action = 'update'
        logger.debug(f"Book {calibre_id}: Force mode - updating")
    elif not existing_bookwise:
        action = 'add'
        logger.debug(f"Book {calibre_id}: No BookWise tags found - adding")
    elif expected_hash != existing_hash:
        action = 'update'
        logger.debug(f"Book {calibre_id}: Tags changed - updating")
    else:
        logger.debug(f"Book {calibre_id}: Tags identical - skipping")

    # Update status tracking
    if status_data is not None:
        update_book_status(status_data, calibre_id, expected_hash, None)

    if action == 'skip':
        return ('skip', True)

    if dry_run:
        return (action, True)

    # Merge: user tags + expected BookWise tags
    all_tags = list(set(user_tags + tags))
    tags_str = ','.join(all_tags)

    try:
        cmd = [
            settings.CALIBREDB_PATH, 'set_metadata',
            str(calibre_id),
            '--field', f'tags:{tags_str}',
            f'--library-path={library_path}'
        ]

        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.debug(f"Book {calibre_id}: Tags updated successfully")
        return (action, True)

    except subprocess.CalledProcessError as e:
        logger.error(f"Book {calibre_id}: Error adding tags - {e.stderr}")
        return (action, False)


def update_publication_date(calibre_id, year, library_path, dry_run=False):
    """
    Update publication date in Calibre to original publication year.
    
    Args:
        calibre_id: Calibre book ID
        year: Publication year (integer)
        library_path: Path to Calibre library
        dry_run: If True, only show what would be done
    """
    if not year:
        return True
    
    if dry_run:
        return True
    
    # Format: YYYY-01-01 (use January 1st as placeholder)
    date_str = f"{year}-01-01"
    
    try:
        cmd = [
            settings.CALIBREDB_PATH, 'set_metadata',
            str(calibre_id),
            '--field', f'pubdate:{date_str}',
            f'--library-path={library_path}'
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  Error updating date: {e.stderr}")
        return False


def update_description(calibre_id, ai_description, existing_description, mode, library_path, dry_run=False):
    """
    Update book description in Calibre.
    
    Args:
        calibre_id: Calibre book ID
        ai_description: AI-generated description
        existing_description: Current Calibre description
        mode: 'replace', 'prepend', 'custom', or 'skip'
        library_path: Path to Calibre library
        dry_run: If True, only show what would be done
    """
    if mode == 'skip' or not ai_description:
        return True
    
    if dry_run:
        return True
    
    try:
        if mode == 'replace':
            # Replace existing with AI description
            new_description = ai_description
            field = 'comments'
            
        elif mode == 'prepend':
            # Check if AI summary already exists (prevent duplication)
            if existing_description and "**AI Summary:**" in existing_description:
                logger.info(f"  ⏭️  AI summary already in description (skipped)")
                return True
            # Prepend AI description to existing
            new_description = f"**AI Summary:**\n\n{ai_description}\n\n---\n\n{existing_description or ''}"
            field = 'comments'
            
        elif mode == 'custom':
            # Use custom column #ai_summary
            new_description = ai_description
            field = '#ai_summary'
        
        else:
            return True
        
        cmd = [
            settings.CALIBREDB_PATH, 'set_metadata',
            str(calibre_id),
            '--field', f'{field}:{new_description}',
            f'--library-path={library_path}'
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
        
    except subprocess.CalledProcessError as e:
        # If custom column doesn't exist, provide helpful error
        if mode == 'custom' and 'unknown field' in e.stderr.lower():
            print(f"  ⚠️  Custom column #ai_summary doesn't exist. Create it in Calibre first:")
            print(f"      Preferences → Add your own columns → Column: Long text (not searchable only)")
            print(f"      Lookup name: #ai_summary, Column heading: AI Summary")
        else:
            print(f"  ⚠️  Error updating description: {e.stderr}")
        return False


def verify_calibre_setup():
    """Verify Calibre setup - check if custom columns exist."""
    import sqlite3
    
    print("=" * 80)
    print("CALIBRE SETUP VERIFICATION")
    print("=" * 80)
    print()
    
    db_path = settings.CALIBRE_DB_PATH
    print(f"Checking database: {db_path}")
    print()
    
    try:
        conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT id, label, name, datatype FROM custom_columns")
        custom_columns = cursor.fetchall()
        
        print("📚 CUSTOM COLUMNS")
        print("-" * 80)
        if not custom_columns:
            print("  (No custom columns found)")
        else:
            for col in custom_columns:
                col_id, label, name, datatype = col
                print(f"  #{label:20} - {name:30} ({datatype})")
        
        print()
        has_ai_summary = any(col[1] == 'ai_summary' for col in custom_columns)
        
        if has_ai_summary:
            print("✅ #ai_summary exists - Ready for AI description import!")
        else:
            print("⚠️  #ai_summary NOT found")
            print("   To add AI descriptions, create this custom column in Calibre:")
            print("   Preferences → Add your own columns")
            print("   Lookup name: #ai_summary")
            print("   Column type: Long text, like comments, not searchable")
        
        conn.close()
        print()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Add AI-generated tags and canonical award names to Calibre",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview what would be added
  python3 src/dataenrichment/add_tags_to_calibre.py --dry-run

  # Actually add tags to Calibre
  python3 src/dataenrichment/add_tags_to_calibre.py --yes

  # Show import status and history
  python3 src/dataenrichment/add_tags_to_calibre.py --status

  # Force re-import all books (ignore status tracking)
  python3 src/dataenrichment/add_tags_to_calibre.py --force --yes

  # Use AI descriptions in custom column (recommended)
  python3 src/dataenrichment/add_tags_to_calibre.py --update-descriptions custom --yes

After import, search in Calibre:
  tags:"Award: Nobel Prize in Literature (1962)"
  tags:"Award: Pulitzer Prize - Fiction (1940)"
  tags:"List: Modern Library 100 Best Novels #10"
  tags:"List: BBC 100 Best Novels"
  tags:"Series: Penguin Classics"
  tags:"Topic: Great Depression"
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    parser.add_argument(
        '--awards-only',
        action='store_true',
        help='Only add canonical award names (skip AI tags)'
    )
    
    parser.add_argument(
        '--ai-only',
        action='store_true',
        help='Only add AI-generated tags (skip awards)'
    )
    
    parser.add_argument(
        '--update-descriptions',
        choices=['replace', 'prepend', 'custom', 'skip'],
        default='skip',
        help='How to handle AI descriptions: replace existing, prepend to existing, use custom column #ai_summary, or skip (default: skip)'
    )
    
    parser.add_argument(
        '--yes',
        action='store_true',
        help='Skip confirmation prompt'
    )
    
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify Calibre setup (check for custom columns)'
    )
    
    parser.add_argument(
        '--input',
        type=str,
        help='Custom input file for selective updates (default: enriched_books.jsonl)'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show import status report and exit'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-import all books (ignore status tracking)'
    )

    args = parser.parse_args()

    # Handle status mode
    if args.status:
        from chromadb import PersistentClient
        client = PersistentClient(path=settings.CHROMADB_PATH)
        collection = client.get_collection(name="book_metadata_embeddings")
        status_data = load_status_file()
        show_import_status(status_data, collection)
        return

    # Handle verify mode
    if args.verify:
        verify_calibre_setup()
        return
    
    try:
        print("=" * 80)
        print("ADD ENRICHMENT TAGS TO CALIBRE")
        print("=" * 80)
        print()
        
        if args.dry_run:
            print("⚠️  DRY RUN MODE - No changes will be made")
            print()
        
        # Get library path
        library_path = settings.CALIBRE_DB_PATH.replace('/metadata.db', '')
        print(f"Calibre Library: {library_path}")
        print()
        
        # Load enriched books
        if args.input:
            print(f"Loading enriched books from: {args.input}")
        else:
            print("Loading enriched books...")
        books = load_enriched_books(input_file=args.input)
        
        if not books:
            return
        
        print(f"✓ Loaded {len(books)} enriched books")
        print()

        # Load status tracking file
        logger.info("Loading import status file...")
        status_data = load_status_file()
        if args.force:
            print("⚠️  FORCE MODE - Will re-import all books regardless of previous imports")
            print()

        # Confirm before proceeding
        if not args.dry_run and not args.yes:
            print(f"⚠️  This will add tags to {len(books)} books in Calibre")
            response = input("Continue? (yes/no): ").lower().strip()
            if response not in ['yes', 'y']:
                print("❌ Cancelled")
                return
        elif not args.dry_run and args.yes:
            print(f"✓ Auto-confirmed (--yes flag)")
            print(f"  Processing {len(books)} books...")
            print()

        # Process each book
        print("\n" + "=" * 80)
        print("PROCESSING BOOKS")
        print("=" * 80)

        success_count = 0
        skip_count = 0
        add_count = 0
        update_count = 0
        error_count = 0
        total_books = len(books)

        start_time = datetime.now()
        
        for idx, book in enumerate(books, 1):
            calibre_id = book['calibre_id']
            title = book['title']
            author = book['author']
            
            # Progress indicator
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = idx / elapsed if elapsed > 0 else 0
            remaining = (total_books - idx) / rate if rate > 0 else 0
            
            print(f"\n[{idx}/{total_books}] {'[DRY RUN] ' if args.dry_run else ''}{title}")
            print(f"  by {author} (ID: {calibre_id})")
            if not args.dry_run and idx > 1:
                print(f"  Progress: {idx/total_books*100:.1f}% | Elapsed: {int(elapsed)}s | ETA: {int(remaining)}s | Rate: {rate:.1f} books/s")
            
            # Get original publication year
            pub_year = book.get('original_publication_year')
            if pub_year:
                print(f"  Original publication: {pub_year}")
            
            # Prepare tags
            tags_to_add = []
            
            # Add canonical recognition tags (awards, lists, series, canon)
            if not args.ai_only:
                canonical_tags = extract_canonical_tags(
                    book.get('awards_and_recognition', '')
                )
                tags_to_add.extend(canonical_tags)
                
                # Add canonical tier tag if author is in a tier
                tier_tag = get_canonical_tier_tag(book.get('author', ''))
                if tier_tag:
                    tags_to_add.append(tier_tag)
                
                if canonical_tags:
                    # Separate awards from lists for display
                    awards = [t for t in canonical_tags if t.startswith('Award:')]
                    lists = [t for t in canonical_tags if t.startswith(('List:', 'Series:', 'Canon:'))]
                    
                    if awards:
                        print(f"  Awards: {', '.join(awards)}")
                    if lists:
                        print(f"  Lists/Series: {', '.join(lists)}")
            
            # Add AI-generated tags
            if not args.awards_only:
                ai_tags = book.get('tags', [])
                # Prefix AI tags to distinguish from awards
                ai_tags_prefixed = [f"Topic: {tag}" for tag in ai_tags]
                tags_to_add.extend(ai_tags_prefixed)
                
                if ai_tags:
                    print(f"  AI Tags: {', '.join(ai_tags[:5])}{'...' if len(ai_tags) > 5 else ''}")
            
            if not tags_to_add and not pub_year:
                print(f"  (Nothing to add)")
                continue
            
            if tags_to_add:
                print(f"  Total tags to add: {len(tags_to_add)}")
            
            # Update publication date if available
            date_success = True
            if pub_year:
                date_success = update_publication_date(calibre_id, pub_year, library_path, args.dry_run)
                if date_success and not args.dry_run:
                    print(f"  ✓ Publication date updated to {pub_year}")
            
            # Update description if requested
            desc_success = True
            if args.update_descriptions != 'skip':
                ai_desc = book.get('enhanced_description')
                existing_desc = book.get('existing_description')
                desc_success = update_description(
                    calibre_id, ai_desc, existing_desc, 
                    args.update_descriptions, library_path, args.dry_run
                )
                if desc_success and not args.dry_run:
                    if args.update_descriptions == 'custom':
                        print(f"  ✓ AI summary added to custom column")
                    elif args.update_descriptions == 'replace':
                        print(f"  ✓ Description replaced with AI version")
                    elif args.update_descriptions == 'prepend':
                        print(f"  ✓ AI summary prepended to description")
            
            # Add tags
            action = 'skip'
            tags_success = True
            if tags_to_add:
                action, tags_success = add_tags_to_book(
                    calibre_id, tags_to_add, library_path,
                    args.dry_run, args.force, status_data
                )
                if tags_success and not args.dry_run:
                    if action == 'skip':
                        print(f"  ⏭️  Tags unchanged (skipped)")
                        skip_count += 1
                    elif action == 'add':
                        print(f"  ✓ Tags added")
                        add_count += 1
                    elif action == 'update':
                        print(f"  ✓ Tags updated")
                        update_count += 1

            if date_success and tags_success and desc_success:
                success_count += 1
            else:
                error_count += 1
            
            # Periodic status update every 50 books
            if not args.dry_run and idx % 50 == 0:
                elapsed_total = (datetime.now() - start_time).total_seconds()
                print(f"\n  ⏱️  Checkpoint: {idx}/{total_books} books processed ({success_count} success, {error_count} errors) - {int(elapsed_total)}s elapsed")
        
        # Save status tracking file
        if not args.dry_run:
            logger.info("Saving import status file...")
            save_status_file(status_data)

        # Summary
        print("\n" + "=" * 80)
        print("IMPORT COMPLETE")
        print("=" * 80)
        print()
        print(f"✓ Successfully processed: {success_count} books")
        if skip_count > 0:
            print(f"⏭️  Skipped (unchanged): {skip_count} books")
        if add_count > 0:
            print(f"➕ Added: {add_count} books")
        if update_count > 0:
            print(f"🔄 Updated: {update_count} books")
        if error_count > 0:
            print(f"⚠️  Errors: {error_count} books")
        print()
        
        if not args.dry_run:
            print("📚 In Calibre, you can now search:")
            print('   tags:"Award: Nobel Prize in Literature (1962)"')
            print('   tags:"Award: Pulitzer Prize - Fiction (1940)"')
            print('   tags:"List: Modern Library 100 Best Novels #10"')
            print('   tags:"Series: Penguin Classics"')
            print('   tags:"Topic: Great Depression"')
            print()
            print("💡 Search tips:")
            print('   - Use wildcards: tags:"Award: Nobel Prize*" (all Nobel winners)')
            print('   - Use wildcards: tags:"List: Modern Library*" (all on this list)')
            print('   - Use Tag Browser to see all tags with their hierarchies')
            print()
        
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

