"""
Data loader for book scoring system.

Handles loading and parsing of all award, list, and canonical author data
from JSON files.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..utils.normalizers import normalize_title, normalize_author


@dataclass
class CanonicalWork:
    """
    Information about a canonical work from the literary canon.

    Canonical works are historically significant books by major authors
    (Shakespeare, Cervantes, Austen, Joyce, etc.) that form the foundation
    of literary education and cultural heritage.
    """
    author: str
    title: str
    year: int
    tier: str  # S (Universal Giants), A (Essential Moderns), B (Important Regional)
    death_year: Optional[int] = None
    alternate_titles: Optional[List[str]] = None


class DataLoadingError(Exception):
    """Raised when data loading fails"""
    pass


class BookDataLoader:
    """Loads and manages all book award, list, and canonical data"""

    def __init__(self, datasources_dir: Path):
        """
        Initialize data loader.

        Args:
            datasources_dir: Path to directory containing JSON data files
        """
        self.datasources_dir = datasources_dir

        # Data storage
        self.book_awards: Dict = {}
        self.author_awards: Dict = {}
        self.book_lists: Dict = {}
        self.classic_series: Dict = {}
        self.educational_canon: Dict = {}
        self.major_award_winning_authors: Dict = {}
        self.significant_authors: Dict = {}
        self.canonical_works: Dict[str, CanonicalWork] = {}

    def load_all(self, award_files: Dict, list_files: Dict,
                 classic_series_files: Dict, educational_canon_files: Dict,
                 canonical_files: Dict[str, str]) -> None:
        """
        Load all data from configuration files.

        Args:
            award_files: Dict of award file paths and configurations
            list_files: Dict of list file paths and configurations
            classic_series_files: Dict of classic series file paths
            educational_canon_files: Dict of educational canon file paths
            canonical_files: Dict mapping filenames to tier names (e.g., {'file.json': 'S'})
        """
        print("=" * 80)
        print("Loading Award and List Data from Configuration")
        print("=" * 80)
        print()

        self._load_awards(award_files)
        self._load_lists(list_files)
        self._load_classic_series(classic_series_files)
        self._load_educational_canon(educational_canon_files)
        self._load_canonical_authors(canonical_files)

        self._print_summary()

    def _load_awards(self, award_files: Dict) -> None:
        """Load award data from JSON files"""
        print("Loading Award Files:")
        print("-" * 80)
        print()

        for filename, config in award_files.items():
            self._load_award_file(filename, config)

        print(f"\n  Total: {sum(len(v) for v in self.book_awards.values())} award entries loaded\n")

    def _load_lists(self, list_files: Dict) -> None:
        """Load book list data from JSON files"""
        print("Loading Best Books Lists:")
        print("-" * 80)
        print()

        for filename, config in list_files.items():
            self._load_list_file(filename, config)

        print(f"\n  Total: {sum(len(v) for v in self.book_lists.values())} list entries loaded\n")

    def _load_classic_series(self, classic_series_files: Dict) -> None:
        """Load classic series data from JSON files"""
        print("Loading Classic Series:")
        print("-" * 80)
        print()

        for filename, config in classic_series_files.items():
            self._load_classic_series_file(filename, config)

        print(f"\n  Total: {sum(len(v) for v in self.classic_series.values())} classic series entries loaded\n")

    def _load_educational_canon(self, educational_canon_files: Dict) -> None:
        """Load educational canon data from JSON files"""
        print("Loading Educational Canon Lists:")
        print("-" * 80)
        print()

        for filename, config in educational_canon_files.items():
            self._load_educational_canon_file(filename, config)

        print(f"\n  Total: {sum(len(v) for v in self.educational_canon.values())} educational canon entries loaded\n")

    def _load_award_file(self, filename: str, config: Dict) -> None:
        """Load a single award file"""
        filepath = self.datasources_dir / filename

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            award_name = config.get('name', filename)
            award_type = config.get('type', 'book')
            points = config.get('points', 0)

            # Handle both formats: direct array or wrapped in dict with 'items'/'entries' key
            if isinstance(data, dict):
                entries = data.get('items', data.get('entries', data.get('awards', [])))
            else:
                entries = data

            count = 0
            for entry in entries:
                if award_type == 'author':
                    count += self._process_author_award(entry, award_name, points)
                else:
                    count += self._process_book_award(entry, award_name, points)

            print(f"  ✓ {filename:<45} - {award_name}: {count} entries")

        except FileNotFoundError:
            print(f"  ✗ {filename:<45} - File not found")
        except json.JSONDecodeError as e:
            print(f"  ✗ {filename:<45} - Invalid JSON: {e}")
        except Exception as e:
            print(f"  ✗ {filename:<45} - Error: {e}")

    def _load_list_file(self, filename: str, config: Dict) -> None:
        """Load a single list file"""
        filepath = self.datasources_dir / filename

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            list_name = config.get('name', filename)

            # Handle both formats: direct array or wrapped in dict with 'items'/'entries'/'books' key
            if isinstance(data, dict):
                entries = data.get('items', data.get('entries', data.get('books', [])))
            else:
                entries = data

            count = 0

            for entry in entries:
                title = entry.get('title', '').strip()
                author = entry.get('author', '').strip()

                if not title or not author:
                    continue

                key = (normalize_title(title, author), normalize_author(author))

                if key not in self.book_lists:
                    self.book_lists[key] = []

                self.book_lists[key].append({
                    'title': title,
                    'author': author,
                    'list': list_name,
                    'rank': entry.get('rank', 0)
                })
                count += 1

            print(f"  ✓ {filename:<45} - {list_name}: {count} books")

        except FileNotFoundError:
            print(f"  ✗ {filename:<45} - File not found")
        except json.JSONDecodeError as e:
            print(f"  ✗ {filename:<45} - Invalid JSON: {e}")
        except Exception as e:
            print(f"  ✗ {filename:<45} - Error: {e}")

    def _load_classic_series_file(self, filename: str, config: Dict) -> None:
        """Load a single classic series file"""
        filepath = self.datasources_dir / filename

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            series_name = config.get('name', filename)
            points = config.get('points', 0)

            # Handle both formats: direct array or wrapped in dict
            if isinstance(data, dict):
                entries = data.get('items', data.get('entries', data.get('books', [])))
            else:
                entries = data

            count = 0

            for entry in entries:
                title = entry.get('title', '').strip()
                author = entry.get('author', '').strip()

                if not title or not author:
                    continue

                key = (normalize_title(title, author), normalize_author(author))

                if key not in self.classic_series:
                    self.classic_series[key] = []

                self.classic_series[key].append({
                    'title': title,
                    'author': author,
                    'series': series_name,
                    'points': points
                })
                count += 1

            print(f"  ✓ {filename:<45} - {series_name}: {count} books")

        except FileNotFoundError:
            print(f"  ✗ {filename:<45} - File not found")
        except json.JSONDecodeError as e:
            print(f"  ✗ {filename:<45} - Invalid JSON: {e}")
        except Exception as e:
            print(f"  ✗ {filename:<45} - Error: {e}")

    def _load_educational_canon_file(self, filename: str, config: Dict) -> None:
        """Load a single educational canon file"""
        filepath = self.datasources_dir / filename

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            canon_name = config.get('name', filename)
            points = config.get('points', 0)

            # Handle both formats: direct array or wrapped in dict
            if isinstance(data, dict):
                entries = data.get('items', data.get('entries', data.get('books', [])))
            else:
                entries = data

            count = 0

            for entry in entries:
                title = entry.get('title', '').strip()
                author = entry.get('author', '').strip()

                if not title or not author:
                    continue

                key = (normalize_title(title, author), normalize_author(author))

                if key not in self.educational_canon:
                    self.educational_canon[key] = []

                self.educational_canon[key].append({
                    'title': title,
                    'author': author,
                    'canon': canon_name,
                    'points': points
                })
                count += 1

            print(f"  ✓ {filename:<45} - {canon_name}: {count} books")

        except FileNotFoundError:
            print(f"  ✗ {filename:<45} - File not found")
        except json.JSONDecodeError as e:
            print(f"  ✗ {filename:<45} - Invalid JSON: {e}")
        except Exception as e:
            print(f"  ✗ {filename:<45} - Error: {e}")

    def _load_canonical_authors(self, canonical_files: Dict[str, str]) -> None:
        """Load canonical author data for era-neutral scoring"""
        print("Loading Canonical Authors (Era-Neutral Scoring):")
        print("-" * 80)
        print("Note: Canonical baseline corrects for pre-modern award gap")
        print()

        tier_counts = {'S': 0, 'A': 0, 'B': 0}

        for filename, tier in canonical_files.items():
            count = self._load_canonical_tier(filename, tier)
            tier_counts[tier] = count

        print()
        print(f"  Total Canonical Works Loaded: {sum(tier_counts.values())}")
        print(f"     - Tier S (Universal Giants):     {tier_counts['S']} works (+30 baseline, 80 min)")
        print(f"     - Tier A (Essential Moderns):    {tier_counts['A']} works (+20 baseline, 70 min)")
        print(f"     - Tier B (Important Regional):   {tier_counts['B']} works (+15 baseline, 60 min)")
        print()

    def _load_canonical_tier(self, filename: str, tier: str) -> int:
        """Load a single canonical tier file"""
        filepath = self.datasources_dir / filename
        tier_label = {'S': 'Universal Giants', 'A': 'Essential Moderns', 'B': 'Important Regional'}.get(tier, tier)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            count = 0

            # Handle both formats: direct array or wrapped in 'canonical_authors'/'authors' key
            if isinstance(data, dict):
                authors = data.get('canonical_authors', data.get('authors', []))
            else:
                authors = data

            for author_entry in authors:
                author_name = author_entry.get('author', '').strip()
                if not author_name:
                    continue

                lived = author_entry.get('lived', '')
                death_year = self._parse_death_year(lived)

                # Handle both 'books' and 'works' keys
                books_list = author_entry.get('books', author_entry.get('works', []))

                for book in books_list:
                    title = book.get('title', '').strip()
                    if not title:
                        continue

                    # Handle both 'year' and 'year_published' keys
                    year = book.get('year', book.get('year_published', 0))
                    alternates = book.get('alternate_titles', [])

                    key = (normalize_title(title, author_name), normalize_author(author_name))

                    self.canonical_works[key] = CanonicalWork(
                        author=author_name,
                        title=title,
                        year=year,
                        tier=tier,
                        death_year=death_year,
                        alternate_titles=alternates
                    )
                    count += 1

            print(f"  ✓ {filename:<45} - Tier {tier} ({tier_label}):   {count} works")
            return count

        except FileNotFoundError:
            print(f"  ✗ {filename:<45} - File not found")
            return 0
        except json.JSONDecodeError as e:
            print(f"  ✗ {filename:<45} - Invalid JSON: {e}")
            return 0
        except Exception as e:
            print(f"  ✗ {filename:<45} - Error: {e}")
            return 0

    def _process_book_award(self, entry: Dict, award_name: str, points: int) -> int:
        """Process a single book award entry"""
        title = entry.get('title', '').strip()
        author = entry.get('author', '').strip()
        year = entry.get('year', entry.get('year_awarded', 0))

        if not title or not author:
            return 0

        key = (normalize_title(title, author), normalize_author(author))

        if key not in self.book_awards:
            self.book_awards[key] = []

        self.book_awards[key].append({
            'title': title,
            'author': author,
            'award': award_name,
            'year': year,
            'points': points
        })

        # Track for major award winning authors
        self._track_major_award_author(author, title, award_name)

        return 1

    def _process_author_award(self, entry: Dict, award_name: str, points: int) -> int:
        """Process a single author (career) award entry"""
        author = entry.get('author', '').strip()
        year = entry.get('year', entry.get('year_awarded', 0))

        if not author:
            return 0

        author_key = normalize_author(author)
        self.author_awards[author_key] = {
            'author': author,
            'award': award_name,
            'year': year,
            'points': points
        }

        return 1

    def _track_major_award_author(self, author: str, title: str, award: str) -> None:
        """Track authors with multiple major award-winning books"""
        author_key = normalize_author(author)
        title_key = normalize_title(title, author)

        if author_key not in self.major_award_winning_authors:
            self.major_award_winning_authors[author_key] = {
                'author': author,
                'awarded_books': {},
                'count': 0
            }

        if title_key not in self.major_award_winning_authors[author_key]['awarded_books']:
            self.major_award_winning_authors[author_key]['awarded_books'][title_key] = {
                'title': title,
                'awards': []
            }
            self.major_award_winning_authors[author_key]['count'] += 1

        self.major_award_winning_authors[author_key]['awarded_books'][title_key]['awards'].append(award)

    def _parse_death_year(self, lived: str) -> Optional[int]:
        """Parse death year from lived string (e.g., '1882-1941')"""
        if not lived or '-' not in lived:
            return None

        try:
            parts = lived.split('-')
            if len(parts) >= 2 and parts[1].strip():
                return int(parts[1].strip())
        except (ValueError, IndexError):
            pass

        return None

    def _print_summary(self) -> None:
        """Print summary of loaded data"""
        print("=" * 80)
        print(f"Summary: {sum(len(v) for v in self.book_awards.values())} unique books with awards")
        print(f"         {len(self.author_awards)} authors with career awards")
        print(f"         {len(self.major_award_winning_authors)} authors who won major awards (qualify for author bonus)")
        print(f"         {len(self.significant_authors)} significant authors (Nobel/Canonical)")
        print(f"         {sum(len(v) for v in self.book_lists.values())} unique books on lists")
        print(f"         {sum(len(v) for v in self.classic_series.values())} unique books in classic series")
        print(f"         {sum(len(v) for v in self.educational_canon.values())} unique books in educational canons")
        print("=" * 80)
        print()
