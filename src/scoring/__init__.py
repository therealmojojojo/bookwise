"""
Scoring module for era-neutral book quality calculations.

This module implements an era-neutral scoring methodology designed to uncover
timeless masterpieces across all periods, not just contemporary bestsellers.

The scoring system corrects for temporal biases that favor recent publications
by providing canonical baselines, cross-era validation, and underrecognition
corrections for pre-1970 works.
"""

from .models import BookScore
from .calculator import BookScoreCalculator, create_calculator
from .data_loader import CanonicalWork, BookDataLoader
from .scoring_engine import ScoringEngine
from .constants import (
    TIER_BASELINES, TIER_MINIMUMS, METHODOLOGY_NAME,
    CROSS_ERA_3_DECADES_BONUS, CROSS_ERA_2_DECADES_BONUS
)

__all__ = [
    'BookScore',
    'BookScoreCalculator',
    'CanonicalWork',
    'BookDataLoader',
    'ScoringEngine',
    'create_calculator',
    'TIER_BASELINES',
    'TIER_MINIMUMS',
    'METHODOLOGY_NAME',
    'CROSS_ERA_3_DECADES_BONUS',
    'CROSS_ERA_2_DECADES_BONUS',
]

