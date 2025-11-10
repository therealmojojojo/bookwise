"""
Constants for book scoring system.

This module defines all magic numbers, thresholds, and configuration values
used in the era-neutral scoring methodology.
"""

# =============================================================================
# CANONICAL TIER BASELINES
# =============================================================================
# Era-neutral baseline points given to canonical works to correct for
# pre-modern award gaps (Nobel 1901+, Pulitzer 1917+, Booker 1969+)

TIER_S_BASELINE = 30  # Universal Giants (Shakespeare, Dante, Cervantes, etc.)
TIER_A_BASELINE = 20  # Essential Moderns (Joyce, Woolf, Faulkner, etc.)
TIER_B_BASELINE = 15  # Important Regional (significant national authors)

# Tier baseline mapping for easy lookup
TIER_BASELINES = {
    'S': TIER_S_BASELINE,
    'A': TIER_A_BASELINE,
    'B': TIER_B_BASELINE
}

# =============================================================================
# TIER MINIMUM THRESHOLDS
# =============================================================================
# Minimum scores that canonical works should achieve after underrecognition
# correction. These ensure that pre-1970 masterpieces score appropriately.

TIER_S_MINIMUM = 80  # Universal Giants minimum score
TIER_A_MINIMUM = 70  # Essential Moderns minimum score
TIER_B_MINIMUM = 60  # Important Regional minimum score

# Tier minimum mapping for easy lookup
TIER_MINIMUMS = {
    'S': TIER_S_MINIMUM,
    'A': TIER_A_MINIMUM,
    'B': TIER_B_MINIMUM
}

# =============================================================================
# UNDERRECOGNITION CORRECTION
# =============================================================================
# Maximum additional points for pre-1970 canonical works to reach tier minimums

MAX_UNDERRECOGNITION_CORRECTION = 40
PRE_1970_CUTOFF_YEAR = 1970

# =============================================================================
# CROSS-ERA VALIDATION
# =============================================================================
# Bonus points for books recognized across multiple decades
# (demonstrates enduring quality beyond publication era)

CROSS_ERA_3_DECADES_BONUS = 20  # Enduring masterpiece
CROSS_ERA_2_DECADES_BONUS = 10  # Established classic
CROSS_ERA_MIN_DECADES_FOR_BONUS = 2

# =============================================================================
# LIST CREATION YEARS
# =============================================================================
# Years when various "best books" lists were created
# Used for cross-era validation to identify multi-generational acclaim

LIST_CREATION_YEARS = {
    'Modern Library 100 Best Fiction': 1998,
    'Modern Library 100 Best Nonfiction': 1999,
    'Harold Bloom Western Canon': 1994,
    'Harold Bloom\'s Western Canon': 1994,
    'Guardian Best Novels': 2003,
    'BBC 100 Best Novels': 2003,
    'Telegraph 100 Novels': 2009,
    'NYTimes 100 Best 21st Century': 2024,
    'Norwegian Book Club 100 Best': 2002,
    'Le Monde 100 Best': 1999,
    'Observer 100 Greatest Novels': 2003,
    'Time 100 Best Novels': 2005,
    'Penguin Classics': 1950,  # Approximate - treat as historical
    'St Johns College Great Books': 1930,  # Great Books movement
    'Columbia Lit Hum': 1920,  # Core curriculum established
    'UChicago Common Core': 1930,  # Great Books at UChicago
    'Goodreads Choice Fiction': 2010,
    'NEA Big Read Library': 2006,
}

# =============================================================================
# AUTHOR ACHIEVEMENT THRESHOLDS
# =============================================================================
# Criteria for author achievement bonuses

# Minimum number of different books with major awards for author bonus
MIN_AWARDED_BOOKS_FOR_BONUS = 2

# =============================================================================
# SCORING METHODOLOGY
# =============================================================================

METHODOLOGY_NAME = "ERA-NEUTRAL (Timeless Quality)"
METHODOLOGY_DESCRIPTION = (
    "Era-neutral scoring designed to uncover timeless masterpieces "
    "regardless of publication date. Corrects for temporal biases that "
    "favor contemporary works over pre-1970 canonical literature."
)

# =============================================================================
# TIER LABELS
# =============================================================================
# Human-readable labels for canonical tiers

TIER_LABELS = {
    'S': 'Universal Giants',
    'A': 'Essential Moderns',
    'B': 'Important Regional'
}
