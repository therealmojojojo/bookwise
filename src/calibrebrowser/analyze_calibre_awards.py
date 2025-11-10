#!/usr/bin/env python3
"""
Calibre Library Awards Analysis
Analyzes how many authors and books in your Calibre library are present in award files.
"""

import sqlite3
import json
import os
import re
import sys
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config.settings import settings
from src.utils.title_variants import get_all_title_variants
from src.utils.normalizers import normalize_title

# Configuration from .env
CALIBRE_DB = settings.CALIBRE_DB_PATH
DATASOURCES_DIR = settings.DATASOURCES_DIR


def normalize_string(s):
    """Normalize strings for comparison (lowercase, remove extra spaces, punctuation)."""
    if not s:
        return ""
    # Remove common punctuation, convert to lowercase
    s = s.lower().strip()
    # Remove articles at the beginning
    s = re.sub(r'^(the|a|an)\s+', '', s)
    # Remove extra whitespace
    s = re.sub(r'\s+', ' ', s)
    return s


def fuzzy_match(str1, str2, threshold=0.85):
    """Return True if strings match with similarity above threshold."""
    norm1 = normalize_string(str1)
    norm2 = normalize_string(str2)

    if norm1 == norm2:
        return True

    ratio = SequenceMatcher(None, norm1, norm2).ratio()
    return ratio >= threshold


def get_calibre_data():
    """Extract all authors and books from Calibre database."""
    conn = sqlite3.connect(CALIBRE_DB)
    cursor = conn.cursor()

    # Get all authors
    cursor.execute("SELECT DISTINCT name FROM authors ORDER BY name")
    authors = [row[0] for row in cursor.fetchall()]

    # Get all books with authors
    cursor.execute("""
        SELECT DISTINCT b.title, a.name, b.id
        FROM books b
        JOIN books_authors_link bal ON b.id = bal.book
        JOIN authors a ON bal.author = a.id
        ORDER BY b.title
    """)
    books = [(row[0], row[1], row[2]) for row in cursor.fetchall()]

    conn.close()

    return authors, books


def parse_json_awards(filepath):
    """Parse JSON award files."""
    authors_found = set()
    books_found = set()

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle different JSON structures
        entries = []

        if isinstance(data, dict):
            # Check for 'winners' array (Nobel, Pulitzer, etc.)
            if 'winners' in data:
                entries = data['winners']
            # Check for 'entries' array (Modern Library, etc.)
            elif 'entries' in data:
                entries = data['entries']
            # Check for 'books' array
            elif 'books' in data:
                entries = data['books']
        elif isinstance(data, list):
            entries = data

        # Extract authors and books from entries
        for entry in entries:
            if isinstance(entry, dict):
                # Extract author (multiple possible field names)
                author = (entry.get('author') or
                         entry.get('laureate') or
                         entry.get('winner') or
                         entry.get('name'))
                if author and author.strip():
                    authors_found.add(normalize_string(author))

                # Extract book title (multiple possible field names)
                book = (entry.get('title') or
                       entry.get('book') or
                       entry.get('work'))
                if book and book.strip():
                    books_found.add(normalize_string(book))

    except Exception as e:
        print(f"Warning: Could not parse {filepath}: {e}")

    return authors_found, books_found


def parse_markdown_awards(filepath):
    """Parse Markdown award files."""
    authors_found = set()
    books_found = set()

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for patterns like "Title by Author" or "**Title** by Author"
        # Common patterns in markdown award lists
        patterns = [
            r'\*\*([^*]+)\*\*\s+by\s+([^(\n]+)',  # **Title** by Author
            r'([^-\n]+)\s+by\s+([^(\n]+)',          # Title by Author
            r'[•\-]\s*([^,\n]+),\s+([^(\n]+)',      # - Title, Author
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                if len(match) >= 2:
                    title, author = match[0].strip(), match[1].strip()
                    # Clean up
                    title = re.sub(r'\([^)]*\)', '', title).strip()  # Remove parentheses
                    author = re.sub(r'\([^)]*\)', '', author).strip()

                    if title and len(title) > 2:
                        books_found.add(normalize_string(title))
                    if author and len(author) > 2:
                        authors_found.add(normalize_string(author))

    except Exception as e:
        print(f"Warning: Could not parse {filepath}: {e}")

    return authors_found, books_found


def parse_all_awards():
    """Parse all award files in datasources directory."""
    all_authors = set()
    all_books = set()

    datasources_path = Path(DATASOURCES_DIR)

    if not datasources_path.exists():
        print(f"Error: Datasources directory not found: {DATASOURCES_DIR}")
        return all_authors, all_books

    for filepath in datasources_path.glob("*"):
        if filepath.is_file():
            # Try JSON parsing first (works for .json and .md files that are actually JSON)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    json.load(f)
                # If successful, parse as JSON
                authors, books = parse_json_awards(filepath)
                all_authors.update(authors)
                all_books.update(books)
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If JSON parsing fails, try markdown parsing
                if filepath.suffix in ['.md', '.txt']:
                    authors, books = parse_markdown_awards(filepath)
                    all_authors.update(authors)
                    all_books.update(books)

    return all_authors, all_books


def match_authors(calibre_authors, award_authors, threshold=0.85):
    """Match Calibre authors with award authors using fast exact matching."""
    matched = []
    matched_details = {}  # Store original names

    # Create a dict mapping normalized names to original award names
    award_authors_normalized = {normalize_string(a): a for a in award_authors if a}

    for cal_author in calibre_authors:
        cal_norm = normalize_string(cal_author)
        # Fast exact match after normalization
        if cal_norm in award_authors_normalized:
            matched.append(cal_author)
            matched_details[cal_author] = award_authors_normalized[cal_norm]

    return matched


def match_books(calibre_books, award_books, threshold=0.85):
    """Match Calibre books with award books using fast exact matching."""
    matched = []

    # Create a set of normalized award book titles for O(1) lookup
    award_books_normalized = {normalize_string(b) for b in award_books if b}

    for book_title, author, book_id in calibre_books:
        book_norm = normalize_string(book_title)
        # Fast exact match after normalization
        if book_norm in award_books_normalized:
            matched.append((book_title, author, book_id))

    return matched


def generate_report():
    """Generate comprehensive analysis report."""
    print("=" * 80)
    print("CALIBRE LIBRARY AWARDS ANALYSIS")
    print("=" * 80)
    print()

    # Step 1: Get Calibre data
    print("📚 Reading Calibre database...")
    calibre_authors, calibre_books = get_calibre_data()
    print(f"   Found {len(calibre_authors):,} unique authors")
    print(f"   Found {len(calibre_books):,} books")
    print()

    # Step 2: Parse award files
    print("🏆 Parsing award files...")
    award_authors, award_books = parse_all_awards()
    print(f"   Found {len(award_authors):,} unique authors in award files")
    print(f"   Found {len(award_books):,} books in award files")
    print()

    # Step 3: Match authors
    print("🔍 Matching authors (this may take a moment)...")
    matched_authors = match_authors(calibre_authors, award_authors, threshold=0.85)
    print(f"   ✓ Matched {len(matched_authors):,} authors")
    print()

    # Step 4: Match books
    print("🔍 Matching books (this may take a moment)...")
    matched_books = match_books(calibre_books, award_books, threshold=0.85)
    print(f"   ✓ Matched {len(matched_books):,} books")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Total authors in Calibre:        {len(calibre_authors):,}")
    print(f"Award-winning authors matched:   {len(matched_authors):,} ({len(matched_authors)/len(calibre_authors)*100:.1f}%)")
    print()
    print(f"Total books in Calibre:          {len(calibre_books):,}")
    print(f"Award-winning books matched:     {len(matched_books):,} ({len(matched_books)/len(calibre_books)*100:.1f}%)")
    print()

    # Top matched authors (sample)
    if matched_authors:
        print("=" * 80)
        print("SAMPLE: AWARD-WINNING AUTHORS IN YOUR LIBRARY (first 20)")
        print("=" * 80)
        for i, author in enumerate(sorted(matched_authors)[:20], 1):
            print(f"{i:2d}. {author}")
        if len(matched_authors) > 20:
            print(f"    ... and {len(matched_authors) - 20} more")
        print()

    # Top matched books (sample)
    if matched_books:
        print("=" * 80)
        print("SAMPLE: AWARD-WINNING BOOKS IN YOUR LIBRARY (first 20)")
        print("=" * 80)
        for i, (title, author, book_id) in enumerate(sorted(matched_books)[:20], 1):
            print(f"{i:2d}. \"{title}\" by {author}")
        if len(matched_books) > 20:
            print(f"    ... and {len(matched_books) - 20} more")
        print()

    # Save detailed results to files
    print("=" * 80)
    print("SAVING DETAILED RESULTS")
    print("=" * 80)

    # Save matched authors
    output_dir = Path(settings.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    authors_file = output_dir / "matched_authors.txt"
    with open(authors_file, 'w', encoding='utf-8') as f:
        f.write("Award-Winning Authors in Your Calibre Library\n")
        f.write("=" * 80 + "\n\n")
        for author in sorted(matched_authors):
            f.write(f"{author}\n")
    print(f"✓ Saved matched authors to: {authors_file}")

    # Save matched books
    books_file = output_dir / "matched_books.txt"
    with open(books_file, 'w', encoding='utf-8') as f:
        f.write("Award-Winning Books in Your Calibre Library\n")
        f.write("=" * 80 + "\n\n")
        for title, author, book_id in sorted(matched_books):
            f.write(f'"{title}" by {author} [ID: {book_id}]\n')
    print(f"✓ Saved matched books to: {books_file}")
    print()

    return {
        'total_authors': len(calibre_authors),
        'matched_authors': len(matched_authors),
        'total_books': len(calibre_books),
        'matched_books': len(matched_books)
    }


def main():
    """Main entry point for awards analysis."""
    try:
        results = generate_report()
        print("✅ Analysis complete!")
        return results
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
