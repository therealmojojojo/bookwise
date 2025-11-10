"""
Fixtures for scoring tests
Provides sample award data, mock calculators, and test data
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch


@pytest.fixture
def sample_datasources_dir(tmp_path):
    """Create a sample datasources directory with award/list files"""
    datasources_dir = tmp_path / "datasources"
    datasources_dir.mkdir()

    # Nobel Prize Literature (Career Award)
    nobel_data = {
        "name": "Nobel Prize in Literature",
        "items": [
            {"author": "Gabriel García Márquez", "year_awarded": 1982},
            {"author": "Toni Morrison", "year_awarded": 1993},
            {"author": "Kazuo Ishiguro", "year_awarded": 2017},
            {"author": "Alice Munro", "year_awarded": 2013},
        ]
    }
    with open(datasources_dir / "nobel_literature.json", 'w', encoding='utf-8') as f:
        json.dump(nobel_data, f)

    # Pulitzer Prize Fiction (Book Award)
    pulitzer_data = {
        "name": "Pulitzer Prize for Fiction",
        "items": [
            {"title": "Beloved", "author": "Toni Morrison", "year_awarded": 1988},
            {"title": "The Color Purple", "author": "Alice Walker", "year_awarded": 1983},
            {"title": "The Goldfinch", "author": "Donna Tartt", "year_awarded": 2014},
            {"title": "Less", "author": "Andrew Sean Greer", "year_awarded": 2018},
        ]
    }
    with open(datasources_dir / "pulitzer_fiction.json", 'w', encoding='utf-8') as f:
        json.dump(pulitzer_data, f)

    # Man Booker Prize (Book Award)
    booker_data = {
        "name": "Man Booker Prize",
        "items": [
            {"title": "The Remains of the Day", "author": "Kazuo Ishiguro", "year_awarded": 1989},
            {"title": "Wolf Hall", "author": "Hilary Mantel", "year_awarded": 2009},
            {"title": "Bring Up the Bodies", "author": "Hilary Mantel", "year_awarded": 2012},
            {"title": "The White Tiger", "author": "Aravind Adiga", "year_awarded": 2008},
        ]
    }
    with open(datasources_dir / "booker_prize.json", 'w', encoding='utf-8') as f:
        json.dump(booker_data, f)

    # Modern Library 100 Best (List)
    modern_library_data = {
        "name": "Modern Library 100 Best Novels",
        "items": [
            {"title": "Ulysses", "author": "James Joyce", "rank": 1},
            {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "rank": 2},
            {"title": "A Portrait of the Artist as a Young Man", "author": "James Joyce", "rank": 3},
            {"title": "Lolita", "author": "Vladimir Nabokov", "rank": 4},
            {"title": "Brave New World", "author": "Aldous Huxley", "rank": 5},
            {"title": "The Sound and the Fury", "author": "William Faulkner", "rank": 6},
            {"title": "Catch-22", "author": "Joseph Heller", "rank": 7},
            {"title": "Darkness at Noon", "author": "Arthur Koestler", "rank": 8},
            {"title": "Sons and Lovers", "author": "D.H. Lawrence", "rank": 9},
            {"title": "The Grapes of Wrath", "author": "John Steinbeck", "rank": 10},
            {"title": "1984", "author": "George Orwell", "rank": 50},
            {"title": "Beloved", "author": "Toni Morrison", "rank": 27},
        ]
    }
    with open(datasources_dir / "modernlibrary100fiction.json", 'w', encoding='utf-8') as f:
        json.dump(modern_library_data, f)

    # Guardian 100 Best Novels (List)
    guardian_data = {
        "name": "Guardian Best Novels",
        "items": [
            {"title": "The Pilgrim's Progress", "author": "John Bunyan", "rank": 1},
            {"title": "Robinson Crusoe", "author": "Daniel Defoe", "rank": 2},
            {"title": "Ulysses", "author": "James Joyce", "rank": 46},
            {"title": "Mrs Dalloway", "author": "Virginia Woolf", "rank": 50},
        ]
    }
    with open(datasources_dir / "guardianbestnovels.json", 'w', encoding='utf-8') as f:
        json.dump(guardian_data, f)

    # Penguin Classics (Classic Series)
    penguin_data = {
        "name": "Penguin Classics",
        "items": [
            {"title": "Pride and Prejudice", "author": "Jane Austen"},
            {"title": "Moby-Dick", "author": "Herman Melville"},
            {"title": "Ulysses", "author": "James Joyce"},
            {"title": "Mrs Dalloway", "author": "Virginia Woolf"},
        ]
    }
    with open(datasources_dir / "penguinclassics.json", 'w', encoding='utf-8') as f:
        json.dump(penguin_data, f)

    # St. John's Great Books (Educational Canon)
    stjohns_data = {
        "name": "St Johns College Great Books",
        "items": [
            {"title": "The Iliad", "author": "Homer"},
            {"title": "The Odyssey", "author": "Homer"},
            {"title": "Hamlet", "author": "William Shakespeare"},
            {"title": "Ulysses", "author": "James Joyce"},
        ]
    }
    with open(datasources_dir / "stjohnsgreatbooks.json", 'w', encoding='utf-8') as f:
        json.dump(stjohns_data, f)

    # Significant Books Tier 1 (Nobel/Canonical Authors)
    significant_tier1_data = {
        "name": "Significant Books by Major Authors - Tier 1",
        "authors": [
            {
                "author": "James Joyce",
                "recognition": "Canonical Irish Modernist",
                "country": "Ireland",
                "genre": "Modernist Fiction",
                "significance": "Revolutionary stream-of-consciousness technique",
                "lived": "1882-1941",
                "works": [
                    {"title": "Ulysses", "year_published": 1922},
                    {"title": "A Portrait of the Artist as a Young Man", "year_published": 1916},
                    {"title": "Finnegans Wake", "year_published": 1939},
                ]
            },
            {
                "author": "Virginia Woolf",
                "recognition": "Canonical British Modernist",
                "country": "United Kingdom",
                "genre": "Modernist Fiction",
                "significance": "Pioneer of stream-of-consciousness",
                "lived": "1882-1941",
                "works": [
                    {"title": "Mrs Dalloway", "year_published": 1925},
                    {"title": "To the Lighthouse", "year_published": 1927},
                    {"title": "Orlando", "year_published": 1928},
                ]
            },
        ]
    }
    with open(datasources_dir / "canonical_authors_tier_s.json", 'w', encoding='utf-8') as f:
        json.dump(significant_tier1_data, f)

    # Significant Books Tier 2
    significant_tier2_data = {
        "name": "Significant Books by Major Authors - Tier 2",
        "authors": [
            {
                "author": "Hilary Mantel",
                "recognition": "Booker Prize Winner (2x)",
                "country": "United Kingdom",
                "genre": "Historical Fiction",
                "significance": "Two-time Booker winner",
                "lived": "1952-2022",
                "works": [
                    {"title": "Wolf Hall", "year_published": 2009},
                    {"title": "Bring Up the Bodies", "year_published": 2012},
                ]
            },
        ]
    }
    with open(datasources_dir / "canonical_authors_tier_a.json", 'w', encoding='utf-8') as f:
        json.dump(significant_tier2_data, f)

    # Significant Books Tier 3
    significant_tier3_data = {
        "name": "Significant Books by Major Authors - Tier 3",
        "authors": []
    }
    with open(datasources_dir / "canonical_authors_tier_b.json", 'w', encoding='utf-8') as f:
        json.dump(significant_tier3_data, f)

    return datasources_dir


@pytest.fixture
def mock_settings(sample_datasources_dir, tmp_path):
    """Mock settings object with test paths"""
    mock_settings = Mock()
    mock_settings.CALIBRE_DB_PATH = str(tmp_path / "metadata.db")
    mock_settings.DATASOURCES_DIR = str(sample_datasources_dir)

    # Scoring thresholds
    mock_settings.SCORE_NOBEL_DURING_LIFETIME = 30
    mock_settings.SCORE_MAJOR_AWARD_WINNING_AUTHOR = 10
    mock_settings.SCORE_CRITICAL_ACCLAIM_MULTIPLE_AWARDS = 5

    # Recency boost points
    mock_settings.SCORE_RECENCY_0_2_YEARS = 10
    mock_settings.SCORE_RECENCY_3_5_YEARS = 8
    mock_settings.SCORE_RECENCY_6_10_YEARS = 5
    mock_settings.SCORE_RECENCY_11_15_YEARS = 3
    mock_settings.SCORE_RECENCY_16_20_YEARS = 2

    # Significant books file paths
    mock_settings.SIGNIFICANT_BOOKS = "canonical_authors_tier_s.json"
    mock_settings.SIGNIFICANT_BOOKS_SECONDTIER = "canonical_authors_tier_a.json"
    mock_settings.SIGNIFICANT_BOOKS_THIRDTIER = "canonical_authors_tier_b.json"

    return mock_settings


@pytest.fixture
def mock_award_config():
    """Mock award configuration"""
    return {
        "AWARD_FILES": {
            "nobel_literature.json": {
                "description": "Nobel Prize in Literature",
                "name": "Nobel Prize in Literature",
                "points": 30,
                "type": "author",
                "author_qualifies": True
            },
            "pulitzer_fiction.json": {
                "description": "Pulitzer Prize for Fiction",
                "name": "Pulitzer Prize for Fiction",
                "points": 25,
                "type": "book",
                "author_qualifies": True
            },
            "booker_prize.json": {
                "description": "Man Booker Prize",
                "name": "Man Booker Prize",
                "points": 25,
                "type": "book",
                "author_qualifies": True
            },
        },
        "LIST_FILES": {
            "modernlibrary100fiction.json": {
                "description": "Modern Library 100 Best Fiction",
                "name": "Modern Library 100 Best Fiction",
                "top5_points": 15,
                "top20_points": 10,
                "top50_points": 7,
                "top100_points": 5
            },
            "guardianbestnovels.json": {
                "description": "Guardian Best Novels",
                "name": "Guardian Best Novels",
                "top5_points": 12,
                "top20_points": 8,
                "top50_points": 6,
                "top100_points": 4
            },
        },
        "CLASSIC_SERIES": {
            "penguinclassics.json": {
                "description": "Penguin Classics",
                "name": "Penguin Classics",
                "points": 10
            },
        },
        "EDUCATIONAL_CANON": {
            "stjohnsgreatbooks.json": {
                "description": "St Johns College Great Books",
                "name": "St Johns College Great Books",
                "points": 12
            },
        }
    }


@pytest.fixture
def sample_book_data():
    """Sample book data for testing"""
    return [
        {
            "book_id": 1,
            "title": "Ulysses",
            "author": "James Joyce",
            "publication_year": 1922
        },
        {
            "book_id": 2,
            "title": "Beloved",
            "author": "Toni Morrison",
            "publication_year": 1987
        },
        {
            "book_id": 3,
            "title": "The Remains of the Day",
            "author": "Kazuo Ishiguro",
            "publication_year": 1989
        },
        {
            "book_id": 4,
            "title": "Mrs Dalloway",
            "author": "Virginia Woolf",
            "publication_year": 1925
        },
        {
            "book_id": 5,
            "title": "Wolf Hall",
            "author": "Hilary Mantel",
            "publication_year": 2009
        },
        {
            "book_id": 6,
            "title": "Unknown Book",
            "author": "Unknown Author",
            "publication_year": 2020
        },
    ]


@pytest.fixture
def freeze_time():
    """Fixture to freeze time for consistent testing"""
    frozen_year = 2024
    return frozen_year
