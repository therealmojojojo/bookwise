"""
Shared pytest fixtures for BookWise tests
Provides mock databases, file systems, and sample data
"""

import pytest
import sqlite3
import tempfile
import json
import csv
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import sys

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test outputs"""
    return tmp_path


@pytest.fixture
def mock_calibre_db(tmp_path):
    """Create a mock Calibre database with sample data"""
    db_path = tmp_path / "metadata.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create Calibre schema (complete with all tables needed for JSONL export)
    cursor.execute("""
        CREATE TABLE books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pubdate TEXT,
            isbn TEXT,
            path TEXT,
            last_modified TIMESTAMP,
            series_index REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE authors (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE books_authors_link (
            id INTEGER PRIMARY KEY,
            book INTEGER NOT NULL,
            author INTEGER NOT NULL,
            FOREIGN KEY(book) REFERENCES books(id),
            FOREIGN KEY(author) REFERENCES authors(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE publishers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE books_publishers_link (
            id INTEGER PRIMARY KEY,
            book INTEGER NOT NULL,
            publisher INTEGER NOT NULL,
            FOREIGN KEY(book) REFERENCES books(id),
            FOREIGN KEY(publisher) REFERENCES publishers(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE comments (
            id INTEGER PRIMARY KEY,
            book INTEGER NOT NULL,
            text TEXT,
            FOREIGN KEY(book) REFERENCES books(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE languages (
            id INTEGER PRIMARY KEY,
            lang_code TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE books_languages_link (
            id INTEGER PRIMARY KEY,
            book INTEGER NOT NULL,
            lang_code INTEGER NOT NULL,
            FOREIGN KEY(book) REFERENCES books(id),
            FOREIGN KEY(lang_code) REFERENCES languages(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE series (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE books_series_link (
            id INTEGER PRIMARY KEY,
            book INTEGER NOT NULL,
            series INTEGER NOT NULL,
            idx REAL,
            FOREIGN KEY(book) REFERENCES books(id),
            FOREIGN KEY(series) REFERENCES series(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE tags (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE books_tags_link (
            id INTEGER PRIMARY KEY,
            book INTEGER NOT NULL,
            tag INTEGER NOT NULL,
            FOREIGN KEY(book) REFERENCES books(id),
            FOREIGN KEY(tag) REFERENCES tags(id)
        )
    """)

    # Insert sample data
    # Authors
    authors_data = [
        (1, "Leo Tolstoy"),
        (2, "Fyodor Dostoevsky"),
        (3, "James Joyce"),
        (4, "Virginia Woolf"),
        (5, "Gabriel García Márquez"),
        (6, "Toni Morrison"),
        (7, "Unknown Author"),
    ]
    cursor.executemany("INSERT INTO authors VALUES (?, ?)", authors_data)

    # Publishers
    publishers_data = [
        (1, "Penguin Classics"),
        (2, "Vintage"),
        (3, "Modern Library"),
    ]
    cursor.executemany("INSERT INTO publishers VALUES (?, ?)", publishers_data)

    # Languages
    languages_data = [
        (1, "eng"),
        (2, "spa"),
    ]
    cursor.executemany("INSERT INTO languages VALUES (?, ?)", languages_data)

    # Series
    series_data = [
        (1, "Modern Library Classics"),
    ]
    cursor.executemany("INSERT INTO series VALUES (?, ?)", series_data)

    # Books (id, title, timestamp, pubdate, isbn, path, last_modified, series_index)
    books_data = [
        (1, "War and Peace", "2023-01-15", "1869-01-01", "9780143039990", "Leo Tolstoy/War and Peace (1)", "2023-01-15", None),
        (2, "Anna Karenina", "2023-01-16", "1877-01-01", None, "Leo Tolstoy/Anna Karenina (2)", "2023-01-16", None),
        (3, "Crime and Punishment", "2023-01-17", "1866-01-01", None, "Fyodor Dostoevsky/Crime and Punishment (3)", "2023-01-17", None),
        (4, "The Brothers Karamazov", "2023-01-18", "1880-01-01", None, "Fyodor Dostoevsky/The Brothers Karamazov (4)", "2023-01-18", None),
        (5, "Ulysses", "2023-02-01", "1922-01-01", None, "James Joyce/Ulysses (5)", "2023-02-01", None),
        (6, "Mrs Dalloway", "2023-02-02", "1925-01-01", None, "Virginia Woolf/Mrs Dalloway (6)", "2023-02-02", None),
        (7, "To the Lighthouse", "2023-02-03", "1927-01-01", None, "Virginia Woolf/To the Lighthouse (7)", "2023-02-03", None),
        (8, "One Hundred Years of Solitude", "2023-03-01", "1967-01-01", None, "Gabriel Garcia Marquez/One Hundred Years of Solitude (8)", "2023-03-01", None),
        (9, "Beloved", "2023-03-02", "1987-01-01", None, "Toni Morrison/Beloved (9)", "2023-03-02", None),
        (10, "Some Random Book", "2023-04-01", None, None, "Unknown Author/Some Random Book (10)", "2023-04-01", None),
    ]
    cursor.executemany("INSERT INTO books VALUES (?, ?, ?, ?, ?, ?, ?, ?)", books_data)

    # Books-Authors links
    links_data = [
        (1, 1, 1),  # War and Peace -> Tolstoy
        (2, 2, 1),  # Anna Karenina -> Tolstoy
        (3, 3, 2),  # Crime and Punishment -> Dostoevsky
        (4, 4, 2),  # Brothers Karamazov -> Dostoevsky
        (5, 5, 3),  # Ulysses -> Joyce
        (6, 6, 4),  # Mrs Dalloway -> Woolf
        (7, 7, 4),  # To the Lighthouse -> Woolf
        (8, 8, 5),  # One Hundred Years -> García Márquez
        (9, 9, 6),  # Beloved -> Morrison
        (10, 10, 7), # Random Book -> Unknown
    ]
    cursor.executemany("INSERT INTO books_authors_link VALUES (?, ?, ?)", links_data)

    # Books-Publishers links
    publisher_links = [
        (1, 1, 1),  # War and Peace -> Penguin Classics
        (2, 2, 1),  # Anna Karenina -> Penguin Classics
        (3, 3, 2),  # Crime and Punishment -> Vintage
    ]
    cursor.executemany("INSERT INTO books_publishers_link VALUES (?, ?, ?)", publisher_links)

    # Comments (descriptions)
    comments_data = [
        (1, 1, "Epic novel about Russia during Napoleonic Wars"),
        (2, 2, "Tragic story of Anna Karenina's affair"),
        (3, 3, "Psychological novel about murder and morality"),
    ]
    cursor.executemany("INSERT INTO comments VALUES (?, ?, ?)", comments_data)

    # Books-Languages links
    language_links = [
        (1, 1, 1),  # War and Peace -> English
        (2, 2, 1),  # Anna Karenina -> English
        (3, 3, 1),  # Crime and Punishment -> English
        (4, 4, 1),  # Brothers Karamazov -> English
        (5, 5, 1),  # Ulysses -> English
        (6, 6, 1),  # Mrs Dalloway -> English
        (7, 7, 1),  # To the Lighthouse -> English
        (8, 8, 2),  # One Hundred Years -> Spanish
        (9, 9, 1),  # Beloved -> English
    ]
    cursor.executemany("INSERT INTO books_languages_link VALUES (?, ?, ?)", language_links)

    # Tags (optional - can keep existing tags)
    tags_data = [
        (1, "Classic"),
        (2, "Fiction"),
        (3, "Russian Literature"),
    ]
    cursor.executemany("INSERT INTO tags VALUES (?, ?)", tags_data)

    # Books-Tags links
    tag_links = [
        (1, 1, 1),  # War and Peace -> Classic
        (2, 1, 2),  # War and Peace -> Fiction
        (3, 1, 3),  # War and Peace -> Russian Literature
    ]
    cursor.executemany("INSERT INTO books_tags_link VALUES (?, ?, ?)", tag_links)

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def sample_scored_books_csv(tmp_path):
    """Create a sample scored books CSV file"""
    csv_path = tmp_path / "all_books_quality_scores.csv"

    data = [
        {
            'title': 'War and Peace',
            'author': 'Leo Tolstoy',
            'final_score': 95,
            'awards_and_recognition': 'Nobel Prize; Modern Library #1; Time 100'
        },
        {
            'title': 'Anna Karenina',
            'author': 'Leo Tolstoy',
            'final_score': 92,
            'awards_and_recognition': 'Modern Library #10; BBC 100'
        },
        {
            'title': 'Crime and Punishment',
            'author': 'Fyodor Dostoevsky',
            'final_score': 90,
            'awards_and_recognition': 'Modern Library #15; Guardian Best'
        },
        {
            'title': 'The Brothers Karamazov',
            'author': 'Fyodor Dostoevsky',
            'final_score': 88,
            'awards_and_recognition': 'Modern Library #5; Penguin Classics'
        },
        {
            'title': 'Ulysses',
            'author': 'James Joyce',
            'final_score': 100,
            'awards_and_recognition': 'Modern Library #1; Guardian Best; BBC 100'
        },
        {
            'title': 'Mrs Dalloway',
            'author': 'Virginia Woolf',
            'final_score': 85,
            'awards_and_recognition': 'Modern Library #50; Penguin Classics'
        },
        {
            'title': 'To the Lighthouse',
            'author': 'Virginia Woolf',
            'final_score': 87,
            'awards_and_recognition': 'Time 100; BBC 100'
        },
        {
            'title': 'One Hundred Years of Solitude',
            'author': 'Gabriel García Márquez',
            'final_score': 94,
            'awards_and_recognition': 'Nobel Prize; Modern Library #25'
        },
        {
            'title': 'Beloved',
            'author': 'Toni Morrison',
            'final_score': 89,
            'awards_and_recognition': 'Pulitzer Prize (1988); Nobel Prize; Modern Library #30'
        },
        {
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald',
            'final_score': 85,
            'awards_and_recognition': 'Modern Library #2; Time 100'
        },
        {
            'title': 'Moby-Dick',
            'author': 'Herman Melville',
            'final_score': 91,
            'awards_and_recognition': 'Modern Library #7; Penguin Classics'
        },
    ]

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'author', 'final_score', 'awards_and_recognition'])
        writer.writeheader()
        writer.writerows(data)

    return csv_path


@pytest.fixture
def sample_award_files(tmp_path):
    """Create sample award JSON files"""
    datasources_dir = tmp_path / "datasources"
    datasources_dir.mkdir()

    # Nobel Prize file
    nobel_data = {
        "name": "Nobel Prize in Literature",
        "winners": [
            {"author": "Leo Tolstoy", "year": 1901},  # Note: Tolstoy never won, but for testing
            {"author": "Gabriel García Márquez", "year": 1982},
            {"author": "Toni Morrison", "year": 1993},
        ]
    }
    with open(datasources_dir / "nobel_literature.json", 'w', encoding='utf-8') as f:
        json.dump(nobel_data, f)

    # Pulitzer Prize file
    pulitzer_data = {
        "name": "Pulitzer Prize for Fiction",
        "winners": [
            {"title": "Beloved", "author": "Toni Morrison", "year": 1988},
            {"title": "The Color Purple", "author": "Alice Walker", "year": 1983},
        ]
    }
    with open(datasources_dir / "pulitzer_fiction.json", 'w', encoding='utf-8') as f:
        json.dump(pulitzer_data, f)

    # Modern Library 100 file
    modern_library_data = {
        "name": "Modern Library 100 Best Novels",
        "entries": [
            {"title": "Ulysses", "author": "James Joyce", "rank": 1},
            {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "rank": 2},
            {"title": "War and Peace", "author": "Leo Tolstoy", "rank": 3},
        ]
    }
    with open(datasources_dir / "modern_library_100.json", 'w', encoding='utf-8') as f:
        json.dump(modern_library_data, f)

    return datasources_dir


@pytest.fixture
def mock_settings(tmp_path, mock_calibre_db, sample_scored_books_csv, sample_award_files):
    """Mock settings object with test paths"""
    settings_mock = Mock()
    settings_mock.CALIBRE_DB_PATH = str(mock_calibre_db)
    settings_mock.CALIBRE_LIBRARY_PATH = str(tmp_path / "calibre_library")
    settings_mock.OUTPUT_DIR = str(tmp_path / "output")
    settings_mock.DATASOURCES_DIR = str(sample_award_files)
    settings_mock.CHROMADB_PATH = str(tmp_path / "chromadb")

    # Create output directory
    Path(settings_mock.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Copy scored books CSV to output directory
    import shutil
    shutil.copy(sample_scored_books_csv, Path(settings_mock.OUTPUT_DIR) / "all_books_quality_scores.csv")

    return settings_mock


@pytest.fixture
def sample_processed_books_csv(tmp_path):
    """Create a sample calibre_metadata_updates.csv (processed books)"""
    csv_path = tmp_path / "output" / "calibre_metadata_updates.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    data = [
        {
            'calibre_id': 1,
            'title': 'War and Peace',
            'author': 'Leo Tolstoy',
            'match_key': 'warandpeace__leotolstoy',
            'quality_score': 95,
            'score_category': 'Score: Legendary (90+)',
            'processing_date': '2024-01-01',
            'scoring_version': '1.0',
            'awards': 'Nobel Prize',
            'lists': 'Modern Library; Time 100',
            'list_ranks': '{}',
            'tags': 'Award: Nobel Prize, List: Modern Library, Score: Legendary (90+)',
            'recognition_full': 'Nobel Prize; Modern Library #1; Time 100'
        },
    ]

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    return csv_path


@pytest.fixture
def mock_title_variants():
    """Mock title variants for testing"""
    return {
        'ulysses__jamesjoyce': [('Ulysses', 'James Joyce')],
        'warandpeace__leotolstoy': [('War and Peace', 'Leo Tolstoy')],
        'crimeandpunishment__fyodordostoevsky': [('Crime and Punishment', 'Fyodor Dostoevsky')],
    }


@pytest.fixture
def capture_output(capsys):
    """Fixture to capture stdout/stderr"""
    return capsys


# Mock functions for common operations
@pytest.fixture
def mock_normalize_title():
    """Mock normalize_title function"""
    def _normalize(title, author=""):
        # Simple normalization for testing
        title = title.lower().replace(" ", "").replace("the", "").replace("a", "").replace("an", "")
        author = author.lower().replace(" ", "")
        return f"{title}__{author}"
    return _normalize


@pytest.fixture
def mock_normalize_author():
    """Mock normalize_author function"""
    def _normalize(author):
        return author.lower().replace(" ", "")
    return _normalize


@pytest.fixture
def sample_enrichment_jsonl(tmp_path):
    """Create a sample enrichment-ready JSONL file"""
    from datetime import datetime

    jsonl_path = tmp_path / "calibre_enrichment_ready.jsonl"

    books = [
        {
            "calibre_id": 1,
            "title": "War and Peace",
            "author": "Leo Tolstoy",
            "quality_score": 95.0,
            "quality_tier": "Legendary",
            "awards_and_recognition": "Nobel Prize; Modern Library #1; Time 100",
            "existing_description": "Epic novel about Russia during Napoleonic Wars",
            "publication_date": "1869-01-01",
            "isbn": None,
            "publisher": "Russian Messenger",
            "file_path": "Leo Tolstoy/War and Peace (1)",
            "language": "eng",
            "series": None,
            "series_index": 1.0,
            "added_date": "2023-01-15",
            "modified_date": "2023-01-15",
            "score_metadata": {
                "score_date": datetime.now().isoformat(),
                "score_version": "1.0"
            },
            "enrichment_ready": True,
            "enrichment_priority": "high"
        },
        {
            "calibre_id": 2,
            "title": "Anna Karenina",
            "author": "Leo Tolstoy",
            "quality_score": 92.0,
            "quality_tier": "Legendary",
            "awards_and_recognition": "Modern Library #10; BBC 100",
            "existing_description": "Tragic story of Anna Karenina's affair",
            "publication_date": "1877-01-01",
            "isbn": None,
            "publisher": "Russian Messenger",
            "file_path": "Leo Tolstoy/Anna Karenina (2)",
            "language": "eng",
            "series": None,
            "series_index": 1.0,
            "added_date": "2023-01-16",
            "modified_date": "2023-01-16",
            "score_metadata": {
                "score_date": datetime.now().isoformat(),
                "score_version": "1.0"
            },
            "enrichment_ready": True,
            "enrichment_priority": "high"
        },
        {
            "calibre_id": 3,
            "title": "Crime and Punishment",
            "author": "Fyodor Dostoevsky",
            "quality_score": 90.0,
            "quality_tier": "Legendary",
            "awards_and_recognition": "Modern Library #15; Guardian Best",
            "existing_description": "Psychological novel about murder and morality",
            "publication_date": "1866-01-01",
            "isbn": None,
            "publisher": "The Russian Messenger",
            "file_path": "Fyodor Dostoevsky/Crime and Punishment (3)",
            "language": "eng",
            "series": None,
            "series_index": 1.0,
            "added_date": "2023-01-17",
            "modified_date": "2023-01-17",
            "score_metadata": {
                "score_date": datetime.now().isoformat(),
                "score_version": "1.0"
            },
            "enrichment_ready": True,
            "enrichment_priority": "high"
        }
    ]

    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for book in books:
            f.write(json.dumps(book, ensure_ascii=False) + '\n')

    return jsonl_path
