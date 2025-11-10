"""
Scoring engine for era-neutral book quality scoring.

Handles all score calculation logic separately from data loading.
"""

import re
from typing import Dict, List, Optional, Set
from datetime import datetime

from .models import BookScore
from .constants import (
    TIER_BASELINES, TIER_MINIMUMS, MAX_UNDERRECOGNITION_CORRECTION,
    PRE_1970_CUTOFF_YEAR, CROSS_ERA_3_DECADES_BONUS,
    CROSS_ERA_2_DECADES_BONUS, CROSS_ERA_MIN_DECADES_FOR_BONUS,
    LIST_CREATION_YEARS, MIN_AWARDED_BOOKS_FOR_BONUS
)
from ..utils.normalizers import normalize_title, normalize_author


class ScoringEngine:
    """
    Calculates era-neutral quality scores for books.

    Separates scoring logic from data loading and management.
    """

    def __init__(self, current_year: Optional[int] = None):
        """
        Initialize scoring engine.

        Args:
            current_year: Current year for calculations (defaults to actual current year)
        """
        self.current_year = current_year or datetime.now().year

    def calculate_score(
        self,
        book_id: int,
        title: str,
        author: str,
        publication_year: Optional[int],
        book_awards: Dict,
        author_awards: Dict,
        book_lists: Dict,
        classic_series: Dict,
        educational_canon: Dict,
        canonical_works: Dict,
        major_award_winning_authors: Dict
    ) -> BookScore:
        """
        Calculate complete era-neutral score for a book.

        Args:
            book_id: Unique book identifier
            title: Book title
            author: Book author
            publication_year: Year of publication (optional)
            book_awards: Dictionary of book-level awards
            author_awards: Dictionary of author-level awards
            book_lists: Dictionary of best books lists
            classic_series: Dictionary of classic series inclusions
            educational_canon: Dictionary of educational canon inclusions
            canonical_works: Dictionary of canonical works
            major_award_winning_authors: Dictionary of award-winning authors

        Returns:
            BookScore object with complete scoring details
        """
        score = BookScore(book_id=book_id, title=title, author=author)
        key = (normalize_title(title, author), normalize_author(author))

        # 1. Book-level awards
        self._score_book_awards(score, key, book_awards)

        # 2. Author-level awards
        self._score_author_awards(score, author, author_awards)

        # 3. Best books lists
        self._score_book_lists(score, key, book_lists)

        # 4. Classic series
        self._score_classic_series(score, key, classic_series)

        # 5. Educational canon
        self._score_educational_canon(score, key, educational_canon)

        # 6. Author achievement bonus
        self._score_author_achievement(score, author, major_award_winning_authors)

        # 7. ERA-NEUTRAL COMPONENTS (no recency boost)
        score.recency_boost = 0  # Explicitly set to 0 for era-neutral

        # 8. Canonical baseline
        canonical_work = canonical_works.get(key)
        if canonical_work:
            self._apply_canonical_baseline(score, canonical_work)

            # 9. Cross-era validation
            self._apply_cross_era_validation(score)

            # 10. Underrecognition correction (pre-1970 only)
            if canonical_work.year and canonical_work.year < PRE_1970_CUTOFF_YEAR:
                self._apply_underrecognition_correction(score, canonical_work)

        # Calculate final score
        score.final_score = score.base_score + score.recency_boost

        return score

    def _score_book_awards(self, score: BookScore, key: tuple, book_awards: Dict) -> None:
        """Add points for book-level awards"""
        if key not in book_awards:
            return

        for award_entry in book_awards[key]:
            award_name = award_entry.get('award', '')
            points = award_entry.get('points', 0)
            year = award_entry.get('year', 0)

            score.base_score += points

            # Format award display string
            award_display = f"{award_name} ({year})" if year else award_name
            score.awards.append(award_display)

            # Track in scoring details
            detail_key = f"award_{award_name.replace(' ', '_').lower()}"
            score.scoring_details[detail_key] = points

    def _score_author_awards(self, score: BookScore, author: str, author_awards: Dict) -> None:
        """Add points for author-level (career) awards"""
        author_key = normalize_author(author)

        if author_key not in author_awards:
            return

        award_entry = author_awards[author_key]
        award_name = award_entry.get('award', '')
        points = award_entry.get('points', 0)
        year = award_entry.get('year', 0)

        score.base_score += points

        # Format award display string
        award_display = f"{award_name} ({year})" if year else award_name
        score.awards.append(award_display)

        # Track in scoring details
        detail_key = f"author_award_{award_name.replace(' ', '_').lower()}"
        score.scoring_details[detail_key] = points

    def _score_book_lists(self, score: BookScore, key: tuple, book_lists: Dict) -> None:
        """Add recognition for best books list appearances"""
        if key not in book_lists:
            return

        for list_entry in book_lists[key]:
            list_name = list_entry.get('list', '')
            rank = list_entry.get('rank', 0)

            # Format display string
            if rank:
                award_display = f"{list_name} #{rank}"
            else:
                award_display = list_name

            score.awards.append(award_display)

    def _score_classic_series(self, score: BookScore, key: tuple, classic_series: Dict) -> None:
        """Add points for classic series inclusion"""
        if key not in classic_series:
            return

        for series_entry in classic_series[key]:
            series_name = series_entry.get('series', '')
            points = series_entry.get('points', 0)

            score.base_score += points
            score.awards.append(f"{series_name}")

            # Track in scoring details
            detail_key = f"series_{series_name.replace(' ', '_').lower()}"
            score.scoring_details[detail_key] = points

    def _score_educational_canon(self, score: BookScore, key: tuple, educational_canon: Dict) -> None:
        """Add points for educational canon inclusion"""
        if key not in educational_canon:
            return

        for canon_entry in educational_canon[key]:
            canon_name = canon_entry.get('canon', '')
            points = canon_entry.get('points', 0)

            score.base_score += points
            score.awards.append(f"{canon_name}")

            # Track in scoring details
            detail_key = f"canon_{canon_name.replace(' ', '_').lower()}"
            score.scoring_details[detail_key] = points

    def _score_author_achievement(
        self,
        score: BookScore,
        author: str,
        major_award_winning_authors: Dict
    ) -> None:
        """Add bonus for authors with multiple major award-winning books"""
        author_key = normalize_author(author)

        if author_key not in major_award_winning_authors:
            return

        author_data = major_award_winning_authors[author_key]
        awarded_book_count = author_data.get('count', 0)

        if awarded_book_count >= MIN_AWARDED_BOOKS_FOR_BONUS:
            # Author has won major awards for multiple different books
            # This demonstrates consistent excellence
            from ..config import settings
            bonus = getattr(settings, 'SCORE_CRITICAL_ACCLAIM_MULTIPLE_AWARDS', 5)
            score.base_score += bonus
            score.scoring_details['author_achievement_bonus'] = bonus

    def _apply_canonical_baseline(self, score: BookScore, canonical_work) -> None:
        """Apply canonical baseline points for tier"""
        baseline = TIER_BASELINES.get(canonical_work.tier, 0)
        score.base_score += baseline
        score.scoring_details['canonical_baseline'] = baseline
        score.scoring_details['canonical_tier'] = canonical_work.tier

    def _apply_cross_era_validation(self, score: BookScore) -> None:
        """Apply cross-era validation bonus"""
        bonus = self._calculate_cross_era_validation(score.awards)
        if bonus > 0:
            score.base_score += bonus
            score.scoring_details['cross_era_validation'] = bonus

    def _apply_underrecognition_correction(self, score: BookScore, canonical_work) -> None:
        """Apply underrecognition correction for pre-1970 canonical works"""
        tier_minimum = TIER_MINIMUMS.get(canonical_work.tier, 0)

        if score.base_score < tier_minimum:
            correction = min(
                MAX_UNDERRECOGNITION_CORRECTION,
                tier_minimum - score.base_score
            )
            score.base_score += correction
            score.scoring_details['underrecognition_correction'] = correction

    def _calculate_cross_era_validation(self, awards: List[str]) -> int:
        """
        Calculate cross-era validation bonus.

        Books recognized across multiple decades demonstrate enduring quality.

        Args:
            awards: List of award/list strings

        Returns:
            Bonus points (0, 10, or 20)
        """
        decades = self._extract_decades_from_awards(awards)

        if len(decades) >= 3:
            return CROSS_ERA_3_DECADES_BONUS
        elif len(decades) >= CROSS_ERA_MIN_DECADES_FOR_BONUS:
            return CROSS_ERA_2_DECADES_BONUS

        return 0

    def _extract_decades_from_awards(self, awards: List[str]) -> Set[int]:
        """
        Extract unique decades from award/list strings.

        Args:
            awards: List of award/list strings (e.g., "Pulitzer Prize (1988)")

        Returns:
            Set of decades (e.g., {1980, 1990, 2000})
        """
        decades = set()

        for award in awards:
            # Extract year from parentheses like "Pulitzer Prize (1988)"
            year_match = re.search(r'\((\d{4})\)', award)
            if year_match:
                year = int(year_match.group(1))
                decade = (year // 10) * 10
                decades.add(decade)
                continue

            # Check if list name is in LIST_CREATION_YEARS
            for list_name, creation_year in LIST_CREATION_YEARS.items():
                if list_name in award:
                    decade = (creation_year // 10) * 10
                    decades.add(decade)
                    break

        return decades
