"""
Settings module - loads configuration from .env file
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'

if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded configuration from: {env_path}")
else:
    print(f"⚠ Warning: .env file not found at {env_path}")
    print(f"  Using default values. Copy env.example to .env and configure.")


class Settings:
    """Application settings loaded from environment variables"""
    
    def __init__(self):
        # Database Configuration
        self.CALIBRE_DB_PATH = os.getenv('CALIBRE_DB_PATH')
        if not self.CALIBRE_DB_PATH:
            raise ValueError(
                "CALIBRE_DB_PATH not set in .env file. "
                "Please configure your .env file with the path to your Calibre database."
            )
        
        # Calibredb command path
        self.CALIBREDB_PATH = os.getenv('CALIBREDB_PATH', 'calibredb')  # Default to 'calibredb' in PATH
        
        # Datasources Directory
        self.DATASOURCES_DIR = os.getenv(
            'DATASOURCES_DIR',
            str(project_root / 'datasources')
        )
        
        # Output Directory
        self.OUTPUT_DIR = os.getenv(
            'OUTPUT_DIR',
            str(project_root / 'output')
        )
        
        # Award Files - Major Awards (25 points)
        self.AWARD_PULITZER_FICTION = os.getenv('AWARD_PULITZER_FICTION', 'pulitzer_fiction.json')
        self.AWARD_PULITZER_BIOGRAPHY = os.getenv('AWARD_PULITZER_BIOGRAPHY', 'pulitzer_biography.json')
        self.AWARD_PULITZER_HISTORY = os.getenv('AWARD_PULITZER_HISTORY', 'pulitzer_history.json')
        self.AWARD_PULITZER_GENERAL_NONFICTION = os.getenv('AWARD_PULITZER_GENERAL_NONFICTION', 'pulitzer_general_nonfiction.json')
        self.AWARD_BOOKER_PRIZE = os.getenv('AWARD_BOOKER_PRIZE', 'booker_prize.json')
        self.AWARD_MAN_BOOKER_PRIZE = os.getenv('AWARD_MAN_BOOKER_PRIZE', 'manbookerprize.json')
        
        # Award Files - Significant Awards (15 points)
        self.AWARD_NATIONAL_BOOK_AWARD_FICTION = os.getenv('AWARD_NATIONAL_BOOK_AWARD_FICTION', 'national_book_award_fiction.json')
        self.AWARD_NATIONAL_BOOK_AWARD_NONFICTION = os.getenv('AWARD_NATIONAL_BOOK_AWARD_NONFICTION', 'national_book_award_nonfiction.json')
        self.AWARD_WOMENS_PRIZE_FICTION = os.getenv('AWARD_WOMENS_PRIZE_FICTION', 'womens_prize_fiction.json')
        self.AWARD_PRIX_GONCOURT = os.getenv('AWARD_PRIX_GONCOURT', 'prix_goncourt.json')
        self.AWARD_FAULKNER = os.getenv('AWARD_FAULKNER', 'faulkneraward.json')
        
        # Award Files - International Awards
        self.AWARD_CERVANTES = os.getenv('AWARD_CERVANTES', 'cervantesaward.json')
        self.AWARD_GEORG_BUCHNER = os.getenv('AWARD_GEORG_BUCHNER', 'georgbuchneraward.json')
        
        # Award Files - Career Awards
        self.AWARD_NOBEL_LITERATURE = os.getenv('AWARD_NOBEL_LITERATURE', 'nobel_literature.json')
        
        # Award Files - Genre Awards
        self.AWARD_HUGO = os.getenv('AWARD_HUGO', 'hugoaward.json')
        self.AWARD_NEBULA = os.getenv('AWARD_NEBULA', 'nebulaaward.json')
        
        # Award Files - Additional Significant Awards (15 points)
        self.AWARD_NBCC_FICTION = os.getenv('AWARD_NBCC_FICTION', 'nbcc_fiction.json')
        self.AWARD_NBCC_GENERAL_NONFICTION = os.getenv('AWARD_NBCC_GENERAL_NONFICTION', 'nbcc_general_nonfiction.json')
        self.AWARD_NBCC_BIOGRAPHY = os.getenv('AWARD_NBCC_BIOGRAPHY', 'nbcc_biography.json')
        self.AWARD_NBCC_HISTORY = os.getenv('AWARD_NBCC_HISTORY', 'nbcc_history.json')
        self.AWARD_DUBLIN_LITERARY = os.getenv('AWARD_DUBLIN_LITERARY', 'dublin_literary_award.json')
        
        # Award Files - Notable Awards (12 points)
        self.AWARD_LA_TIMES_FICTION = os.getenv('AWARD_LA_TIMES_FICTION', 'la_times_book_prize_fiction.json')
        self.AWARD_LA_TIMES_NONFICTION = os.getenv('AWARD_LA_TIMES_NONFICTION', 'la_times_book_prize_nonfiction.json')
        self.AWARD_KIRKUS_FICTION = os.getenv('AWARD_KIRKUS_FICTION', 'kirkus_prize_fiction.json')
        self.AWARD_KIRKUS_YRL = os.getenv('AWARD_KIRKUS_YRL', 'kirkus_prize_yrl.json')
        
        # Best Books Lists
        self.LIST_MODERN_LIBRARY_FICTION = os.getenv('LIST_MODERN_LIBRARY_FICTION', 'modernlibrarybestfiction.json')
        self.LIST_MODERN_LIBRARY_NONFICTION = os.getenv('LIST_MODERN_LIBRARY_NONFICTION', 'modernlibrarynonfiction.json')
        self.LIST_NYTIMES_100_BEST = os.getenv('LIST_NYTIMES_100_BEST', 'nytimes100bestnovels.json')
        self.LIST_GUARDIAN_BEST_NOVELS = os.getenv('LIST_GUARDIAN_BEST_NOVELS', 'guardianbestnovels.json')
        self.LIST_TIMES_100_BEST = os.getenv('LIST_TIMES_100_BEST', 'times100bestnovels.json')
        self.LIST_BBC_100_BEST = os.getenv('LIST_BBC_100_BEST', 'bbc100bestnovels.json')
        self.LIST_LEMONDE_100_BEST = os.getenv('LIST_LEMONDE_100_BEST', 'lemonde100bestnovles.json')
        self.LIST_NORWEGIAN_100_BEST = os.getenv('LIST_NORWEGIAN_100_BEST', 'norwegian100best.json')
        self.LIST_HAROLD_BLOOM_CANON = os.getenv('LIST_HAROLD_BLOOM_CANON', 'haroldbloomcanon.json')
        self.LIST_TELEGRAPH_100_NOVELS = os.getenv('LIST_TELEGRAPH_100_NOVELS', 'telegraph_100_novels.json')
        self.LIST_OBSERVER_100_GREATEST = os.getenv('LIST_OBSERVER_100_GREATEST', 'observer_100_greatest_novels.json')
        self.LIST_GOODREADS_CHOICE_FICTION = os.getenv('LIST_GOODREADS_CHOICE_FICTION', 'goodreads_choice_fiction_top10.json')
        self.LIST_NEA_BIG_READ = os.getenv('LIST_NEA_BIG_READ', 'nea_big_read_library.json')
        
        # Classic Series Lists
        self.LIST_PENGUIN_CLASSICS = os.getenv('LIST_PENGUIN_CLASSICS', 'penguinclassics.json')
        
        # Educational Canon Lists
        self.LIST_ST_JOHNS_GREAT_BOOKS = os.getenv('LIST_ST_JOHNS_GREAT_BOOKS', 'st_johns_college_great_books.json')
        self.LIST_COLUMBIA_LIT_HUM = os.getenv('LIST_COLUMBIA_LIT_HUM', 'columbia_lit_hum.json')
        self.LIST_UCHICAGO_COMMON_CORE = os.getenv('LIST_UCHICAGO_COMMON_CORE', 'uchicago_common_core.json')
        
        # Significant Books by Major Authors (three tiers)
        self.SIGNIFICANT_BOOKS = os.getenv('SIGNIFICANT_BOOKS', 'significant_books.json')
        self.SIGNIFICANT_BOOKS_SECONDTIER = os.getenv('SIGNIFICANT_BOOKS_SECONDTIER', 'significant_books_secondtier.json')
        self.SIGNIFICANT_BOOKS_THIRDTIER = os.getenv('SIGNIFICANT_BOOKS_THIRDTIER', 'significant_books_thirdtier.json')
        
        # Scoring Configuration
        self.SCORE_NOBEL_SPECIFIC_BOOK = int(os.getenv('SCORE_NOBEL_SPECIFIC_BOOK', '30'))
        self.SCORE_NOBEL_WITH_CITATION = int(os.getenv('SCORE_NOBEL_WITH_CITATION', '25'))
        self.SCORE_NOBEL_DURING_LIFETIME = int(os.getenv('SCORE_NOBEL_DURING_LIFETIME', '30'))
        self.SCORE_NOBEL_POSTHUMOUS = int(os.getenv('SCORE_NOBEL_POSTHUMOUS', '10'))
        
        self.SCORE_MAJOR_AWARD = int(os.getenv('SCORE_MAJOR_AWARD', '25'))
        self.SCORE_SIGNIFICANT_AWARD = int(os.getenv('SCORE_SIGNIFICANT_AWARD', '15'))
        self.SCORE_NOTABLE_AWARD = int(os.getenv('SCORE_NOTABLE_AWARD', '12'))
        self.SCORE_GENRE_AWARD = int(os.getenv('SCORE_GENRE_AWARD', '10'))
        
        # Author Achievement Bonus - for books by major award-winning authors
        self.SCORE_MAJOR_AWARD_WINNING_AUTHOR = int(os.getenv('SCORE_MAJOR_AWARD_WINNING_AUTHOR', '10'))
        
        # Critical Acclaim Bonus - extra points if author won MULTIPLE major awards (2+)
        self.SCORE_CRITICAL_ACCLAIM_MULTIPLE_AWARDS = int(os.getenv('SCORE_CRITICAL_ACCLAIM_MULTIPLE_AWARDS', '5'))
        
        self.SCORE_LIST_TOP5 = int(os.getenv('SCORE_LIST_TOP5', '15'))
        self.SCORE_LIST_TOP20 = int(os.getenv('SCORE_LIST_TOP20', '10'))
        self.SCORE_LIST_TOP50 = int(os.getenv('SCORE_LIST_TOP50', '7'))
        self.SCORE_LIST_TOP100 = int(os.getenv('SCORE_LIST_TOP100', '5'))
        
        # Classic Series and Educational Canon Scoring
        self.SCORE_CLASSIC_SERIES = int(os.getenv('SCORE_CLASSIC_SERIES', '5'))
        self.SCORE_EDUCATIONAL_CANON_HIGH = int(os.getenv('SCORE_EDUCATIONAL_CANON_HIGH', '8'))
        self.SCORE_EDUCATIONAL_CANON_MEDIUM = int(os.getenv('SCORE_EDUCATIONAL_CANON_MEDIUM', '7'))
        self.SCORE_GOODREADS_CHOICE = int(os.getenv('SCORE_GOODREADS_CHOICE', '3'))
        self.SCORE_NEA_BIG_READ = int(os.getenv('SCORE_NEA_BIG_READ', '5'))
        
        # Note: Critical acclaim scoring removed to avoid double-counting with other bonuses
        
        self.SCORE_RECENCY_0_2_YEARS = int(os.getenv('SCORE_RECENCY_0_2_YEARS', '10'))
        self.SCORE_RECENCY_3_5_YEARS = int(os.getenv('SCORE_RECENCY_3_5_YEARS', '7'))
        self.SCORE_RECENCY_6_10_YEARS = int(os.getenv('SCORE_RECENCY_6_10_YEARS', '5'))
        self.SCORE_RECENCY_11_15_YEARS = int(os.getenv('SCORE_RECENCY_11_15_YEARS', '3'))
        self.SCORE_RECENCY_16_20_YEARS = int(os.getenv('SCORE_RECENCY_16_20_YEARS', '1'))
        
        self.SCORE_MAJOR_SHORTLIST_BONUS = int(os.getenv('SCORE_MAJOR_SHORTLIST_BONUS', '5'))
        self.SCORE_MINOR_SHORTLIST_BONUS = int(os.getenv('SCORE_MINOR_SHORTLIST_BONUS', '3'))
        
        # AI Enrichment Configuration
        self.ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', None)
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', None)
        
        self.CHROMADB_PATH = os.getenv(
            'CHROMADB_PATH',
            str(project_root / 'book_vectors')
        )
        
        self.ENRICHMENT_DIR = os.getenv(
            'ENRICHMENT_DIR',
            str(Path(self.OUTPUT_DIR) / 'enrichment')
        )
        
        self.ENRICHMENT_MIN_SCORE = int(os.getenv('ENRICHMENT_MIN_SCORE', '0'))
        self.ENRICHMENT_RATE_LIMIT = float(os.getenv('ENRICHMENT_RATE_LIMIT', '1.0'))
        self.ENRICHMENT_BATCH_SIZE = int(os.getenv('ENRICHMENT_BATCH_SIZE', '0'))


# Create singleton instance
settings = Settings()

