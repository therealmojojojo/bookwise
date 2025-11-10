"""
Award Configuration
Defines all award files and their scoring parameters
"""

from .settings import settings

# Award Files Configuration
AWARD_FILES = {
    # Major Literary Awards (Book-specific, 25 points)
    # author_qualifies: If True, winning this award makes ALL author's books eligible for bonus
    settings.AWARD_PULITZER_FICTION: {
        "type": "major_award",
        "points": settings.SCORE_MAJOR_AWARD,
        "category": "fiction",
        "description": "Pulitzer Prize for Fiction",
        "author_qualifies": True  # Author achievement bonus applies
    },
    settings.AWARD_BOOKER_PRIZE: {
        "type": "major_award",
        "points": settings.SCORE_MAJOR_AWARD,
        "category": "fiction",
        "description": "Booker Prize",
        "author_qualifies": True
    },
    settings.AWARD_MAN_BOOKER_PRIZE: {
        "type": "major_award",
        "points": settings.SCORE_MAJOR_AWARD,
        "category": "fiction",
        "description": "Man Booker Prize",
        "author_qualifies": True
    },
    settings.AWARD_PULITZER_BIOGRAPHY: {
        "type": "major_award",
        "points": settings.SCORE_MAJOR_AWARD,
        "category": "nonfiction",
        "description": "Pulitzer Prize for Biography",
        "author_qualifies": True
    },
    settings.AWARD_PULITZER_HISTORY: {
        "type": "major_award",
        "points": settings.SCORE_MAJOR_AWARD,
        "category": "nonfiction",
        "description": "Pulitzer Prize for History",
        "author_qualifies": True
    },
    settings.AWARD_PULITZER_GENERAL_NONFICTION: {
        "type": "major_award",
        "points": settings.SCORE_MAJOR_AWARD,
        "category": "nonfiction",
        "description": "Pulitzer Prize for General Non-Fiction",
        "author_qualifies": True
    },
    
    # Significant Literary Awards (15 points)
    settings.AWARD_NATIONAL_BOOK_AWARD_FICTION: {
        "type": "significant_award",
        "points": settings.SCORE_SIGNIFICANT_AWARD,
        "category": "fiction",
        "description": "National Book Award - Fiction",
        "author_qualifies": True  # Major award - qualifies for bonus
    },
    settings.AWARD_NATIONAL_BOOK_AWARD_NONFICTION: {
        "type": "significant_award",
        "points": settings.SCORE_SIGNIFICANT_AWARD,
        "category": "nonfiction",
        "description": "National Book Award - Nonfiction",
        "author_qualifies": True
    },
    settings.AWARD_WOMENS_PRIZE_FICTION: {
        "type": "significant_award",
        "points": settings.SCORE_SIGNIFICANT_AWARD,
        "category": "fiction",
        "description": "Women's Prize for Fiction",
        "author_qualifies": False
    },
    settings.AWARD_PRIX_GONCOURT: {
        "type": "significant_award",
        "points": settings.SCORE_SIGNIFICANT_AWARD,
        "category": "fiction",
        "description": "Prix Goncourt",
        "author_qualifies": True
    },
    settings.AWARD_FAULKNER: {
        "type": "significant_award",
        "points": settings.SCORE_SIGNIFICANT_AWARD,
        "category": "fiction",
        "description": "PEN/Faulkner Award",
        "author_qualifies": False
    },
    
    # International Literary Awards
    settings.AWARD_CERVANTES: {
        "type": "significant_award",
        "points": settings.SCORE_SIGNIFICANT_AWARD,
        "category": "career",
        "description": "Miguel de Cervantes Prize"
    },
    settings.AWARD_GEORG_BUCHNER: {
        "type": "notable_award",
        "points": settings.SCORE_NOTABLE_AWARD,
        "category": "career",
        "description": "Georg Büchner Prize"
    },
    
    # Nobel Prize (Career award, 20 points)
    settings.AWARD_NOBEL_LITERATURE: {
        "type": "nobel_prize",
        "points": settings.SCORE_NOBEL_DURING_LIFETIME,
        "category": "career",
        "description": "Nobel Prize in Literature"
    },
    
    # Science Fiction & Fantasy Awards (10 points)
    settings.AWARD_HUGO: {
        "type": "genre_award",
        "points": settings.SCORE_GENRE_AWARD,
        "category": "scifi_fantasy",
        "description": "Hugo Award"
    },
    settings.AWARD_NEBULA: {
        "type": "genre_award",
        "points": settings.SCORE_GENRE_AWARD,
        "category": "scifi_fantasy",
        "description": "Nebula Award"
    },
    
    # Additional Significant Awards (15 points)
    settings.AWARD_NBCC_FICTION: {
        "type": "significant_award",
        "points": settings.SCORE_SIGNIFICANT_AWARD,
        "category": "fiction",
        "description": "National Book Critics Circle Award - Fiction",
        "author_qualifies": True
    },
    settings.AWARD_NBCC_GENERAL_NONFICTION: {
        "type": "significant_award",
        "points": settings.SCORE_SIGNIFICANT_AWARD,
        "category": "nonfiction",
        "description": "National Book Critics Circle Award - General Nonfiction",
        "author_qualifies": True
    },
    settings.AWARD_NBCC_BIOGRAPHY: {
        "type": "significant_award",
        "points": settings.SCORE_SIGNIFICANT_AWARD,
        "category": "nonfiction",
        "description": "National Book Critics Circle Award - Biography",
        "author_qualifies": True
    },
    settings.AWARD_NBCC_HISTORY: {
        "type": "significant_award",
        "points": settings.SCORE_SIGNIFICANT_AWARD,
        "category": "nonfiction",
        "description": "National Book Critics Circle Award - History",
        "author_qualifies": True
    },
    settings.AWARD_DUBLIN_LITERARY: {
        "type": "significant_award",
        "points": settings.SCORE_SIGNIFICANT_AWARD,
        "category": "fiction",
        "description": "Dublin Literary Award",
        "author_qualifies": True
    },
    
    # Notable Awards (12 points)
    settings.AWARD_LA_TIMES_FICTION: {
        "type": "notable_award",
        "points": settings.SCORE_NOTABLE_AWARD,
        "category": "fiction",
        "description": "Los Angeles Times Book Prize - Fiction"
    },
    settings.AWARD_LA_TIMES_NONFICTION: {
        "type": "notable_award",
        "points": settings.SCORE_NOTABLE_AWARD,
        "category": "nonfiction",
        "description": "Los Angeles Times Book Prize - Nonfiction"
    },
    settings.AWARD_KIRKUS_FICTION: {
        "type": "notable_award",
        "points": settings.SCORE_NOTABLE_AWARD,
        "category": "fiction",
        "description": "Kirkus Prize for Fiction"
    },
    settings.AWARD_KIRKUS_YRL: {
        "type": "notable_award",
        "points": settings.SCORE_NOTABLE_AWARD,
        "category": "fiction",
        "description": "Kirkus Prize for Young Readers' Literature"
    },
}

# Prestigious Book Lists Configuration
LIST_FILES = {
    settings.LIST_MODERN_LIBRARY_FICTION: {
        "category": "fiction",
        "description": "Modern Library 100 Best Novels",
        "top5_points": settings.SCORE_LIST_TOP5,
        "top20_points": settings.SCORE_LIST_TOP20,
        "top50_points": settings.SCORE_LIST_TOP50,
        "top100_points": settings.SCORE_LIST_TOP100
    },
    settings.LIST_MODERN_LIBRARY_NONFICTION: {
        "category": "nonfiction",
        "description": "Modern Library 100 Best Nonfiction",
        "top5_points": settings.SCORE_LIST_TOP5,
        "top20_points": settings.SCORE_LIST_TOP20,
        "top50_points": settings.SCORE_LIST_TOP50,
        "top100_points": settings.SCORE_LIST_TOP100
    },
    settings.LIST_NYTIMES_100_BEST: {
        "category": "fiction",
        "description": "New York Times 100 Best Novels",
        "top20_points": settings.SCORE_LIST_TOP20,
        "top50_points": settings.SCORE_LIST_TOP50,
        "top100_points": settings.SCORE_LIST_TOP100
    },
    settings.LIST_GUARDIAN_BEST_NOVELS: {
        "category": "fiction",
        "description": "The Guardian Best Novels",
        "top20_points": settings.SCORE_LIST_TOP20,
        "top50_points": settings.SCORE_LIST_TOP50,
        "top100_points": settings.SCORE_LIST_TOP100
    },
    settings.LIST_TIMES_100_BEST: {
        "category": "fiction",
        "description": "Time Magazine 100 Best Novels",
        "top20_points": settings.SCORE_LIST_TOP20,
        "top50_points": settings.SCORE_LIST_TOP50,
        "top100_points": settings.SCORE_LIST_TOP100
    },
    settings.LIST_BBC_100_BEST: {
        "category": "fiction",
        "description": "BBC 100 Best Novels",
        "top20_points": settings.SCORE_LIST_TOP20,
        "top50_points": settings.SCORE_LIST_TOP50,
        "top100_points": settings.SCORE_LIST_TOP100
    },
    settings.LIST_LEMONDE_100_BEST: {
        "category": "fiction",
        "description": "Le Monde 100 Best Novels",
        "top20_points": settings.SCORE_LIST_TOP20,
        "top50_points": settings.SCORE_LIST_TOP50,
        "top100_points": settings.SCORE_LIST_TOP100
    },
    settings.LIST_NORWEGIAN_100_BEST: {
        "category": "fiction",
        "description": "Norwegian Book Club 100 Best Books",
        "top20_points": settings.SCORE_LIST_TOP20,
        "top50_points": settings.SCORE_LIST_TOP50,
        "top100_points": settings.SCORE_LIST_TOP100
    },
    settings.LIST_HAROLD_BLOOM_CANON: {
        "category": "fiction",
        "description": "Harold Bloom Western Canon",
        "points": 8  # Special case: canonical inclusion
    },
    settings.LIST_TELEGRAPH_100_NOVELS: {
        "category": "fiction",
        "description": "The Telegraph 100 Novels Everyone Should Read",
        "top20_points": settings.SCORE_LIST_TOP20,
        "top50_points": settings.SCORE_LIST_TOP50,
        "top100_points": settings.SCORE_LIST_TOP100
    },
    settings.LIST_OBSERVER_100_GREATEST: {
        "category": "fiction",
        "description": "The Observer 100 Greatest Novels",
        "top20_points": settings.SCORE_LIST_TOP20,
        "top50_points": settings.SCORE_LIST_TOP50,
        "top100_points": settings.SCORE_LIST_TOP100
    },
    settings.LIST_GOODREADS_CHOICE_FICTION: {
        "category": "fiction",
        "description": "Goodreads Choice Awards - Best Fiction Top 10",
        "points": settings.SCORE_GOODREADS_CHOICE  # Special case: popular validation
    },
    settings.LIST_NEA_BIG_READ: {
        "category": "fiction",
        "description": "National Endowment for the Arts - Big Read Library",
        "points": settings.SCORE_NEA_BIG_READ  # Special case: institutional validation
    },
}

# Classic Series Configuration
CLASSIC_SERIES = {
    settings.LIST_PENGUIN_CLASSICS: {
        "category": "classics",
        "description": "Penguin Classics",
        "points": settings.SCORE_CLASSIC_SERIES
    },
}

# Educational Canon Configuration
EDUCATIONAL_CANON = {
    settings.LIST_ST_JOHNS_GREAT_BOOKS: {
        "category": "educational_canon",
        "description": "St. John's College Great Books Program",
        "points": settings.SCORE_EDUCATIONAL_CANON_HIGH
    },
    settings.LIST_COLUMBIA_LIT_HUM: {
        "category": "educational_canon",
        "description": "Columbia Core Curriculum - Literature Humanities",
        "points": settings.SCORE_EDUCATIONAL_CANON_MEDIUM
    },
    settings.LIST_UCHICAGO_COMMON_CORE: {
        "category": "educational_canon",
        "description": "University of Chicago Common Core Reading List",
        "points": settings.SCORE_EDUCATIONAL_CANON_MEDIUM
    },
}

