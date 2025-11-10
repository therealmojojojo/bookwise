"""
Book Quality Score Calculator - Era-Neutral Methodology (Refactored)

This is a refactored version of the calculator with improved separation of concerns,
better error handling, and elimination of code duplication.

See calculator.py docstring for complete methodology documentation.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from ..config import settings
from ..config.award_config import AWARD_FILES, LIST_FILES, CLASSIC_SERIES, EDUCATIONAL_CANON
from .models import BookScore
from .data_loader import BookDataLoader, CanonicalWork
from .scoring_engine import ScoringEngine
from .constants import METHODOLOGY_NAME


class BookScoreCalculator:
    """
    Calculates era-neutral quality scores for books.

    This refactored calculator uses composition to separate:
    - Data loading (BookDataLoader)
    - Scoring logic (ScoringEngine)
    - Configuration (constants module)
    """

    def __init__(self):
        """Initialize calculator with configured paths and load all award data"""
        self.calibre_db_path = settings.CALIBRE_DB_PATH
        self.datasources_dir = Path(settings.DATASOURCES_DIR)

        # Initialize data loader
        self.data_loader = BookDataLoader(self.datasources_dir)

        # Initialize scoring engine
        self.scoring_engine = ScoringEngine()

        # Load all data
        self._load_all_data()

    def _load_all_data(self) -> None:
        """Load all award, list, and canonical data"""
        # Map tier names to filenames from settings
        canonical_files = {
            settings.SIGNIFICANT_BOOKS: 'S',
            settings.SIGNIFICANT_BOOKS_SECONDTIER: 'A',
            settings.SIGNIFICANT_BOOKS_THIRDTIER: 'B'
        }

        self.data_loader.load_all(
            award_files=AWARD_FILES,
            list_files=LIST_FILES,
            classic_series_files=CLASSIC_SERIES,
            educational_canon_files=EDUCATIONAL_CANON,
            canonical_files=canonical_files
        )

    def calculate_score(
        self,
        book_id: int,
        title: str,
        author: str,
        publication_year: Optional[int] = None
    ) -> BookScore:
        """
        Calculate era-neutral quality score for a book.

        Args:
            book_id: Unique book identifier
            title: Book title
            author: Book author
            publication_year: Year of publication (optional)

        Returns:
            BookScore object with complete scoring details
        """
        return self.scoring_engine.calculate_score(
            book_id=book_id,
            title=title,
            author=author,
            publication_year=publication_year,
            book_awards=self.data_loader.book_awards,
            author_awards=self.data_loader.author_awards,
            book_lists=self.data_loader.book_lists,
            classic_series=self.data_loader.classic_series,
            educational_canon=self.data_loader.educational_canon,
            canonical_works=self.data_loader.canonical_works,
            major_award_winning_authors=self.data_loader.major_award_winning_authors
        )

    def get_methodology_name(self) -> str:
        """Return methodology name for reporting"""
        return METHODOLOGY_NAME

    # Properties for backward compatibility with tests
    @property
    def book_awards(self):
        return self.data_loader.book_awards

    @property
    def author_awards(self):
        return self.data_loader.author_awards

    @property
    def book_lists(self):
        return self.data_loader.book_lists

    @property
    def classic_series(self):
        return self.data_loader.classic_series

    @property
    def educational_canon(self):
        return self.data_loader.educational_canon

    @property
    def canonical_works(self):
        return self.data_loader.canonical_works

    @property
    def major_award_winning_authors(self):
        return self.data_loader.major_award_winning_authors

    @property
    def significant_authors(self):
        return self.data_loader.significant_authors

    @property
    def current_year(self):
        return self.scoring_engine.current_year

    def _parse_death_year(self, lived: str) -> Optional[int]:
        """For backward compatibility with tests"""
        return self.data_loader._parse_death_year(lived)

    def _calculate_cross_era_validation(self, list_names: list, awards: list) -> int:
        """For backward compatibility with tests"""
        return self.scoring_engine._calculate_cross_era_validation(awards)


# Convenience function to create calculator
def create_calculator() -> BookScoreCalculator:
    """Create an era-neutral book score calculator instance"""
    return BookScoreCalculator()
