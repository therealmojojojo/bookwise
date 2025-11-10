"""
Data models for book scoring
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class BookScore:
    """Container for book scoring information"""
    book_id: int
    title: str
    author: str
    base_score: float = 0.0
    recency_boost: float = 0.0
    final_score: float = 0.0
    awards: List[str] = field(default_factory=list)
    scoring_details: Dict[str, float] = field(default_factory=dict)
    most_recent_award_year: Optional[int] = None

