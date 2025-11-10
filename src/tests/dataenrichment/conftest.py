"""
Shared pytest fixtures for dataenrichment tests
"""

import pytest
import json
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Mock chromadb before any imports
sys.modules['chromadb'] = MagicMock()

# Mock anthropic before any imports
sys.modules['anthropic'] = MagicMock()

# Mock openai before any imports
sys.modules['openai'] = MagicMock()


@pytest.fixture
def mock_calibre_db(tmp_path):
    """Create a mock Calibre database with sample data"""
    db_path = tmp_path / "metadata.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create Calibre schema
    cursor.execute("""
        CREATE TABLE books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pubdate TEXT,
            path TEXT
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
            author INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE comments (
            id INTEGER PRIMARY KEY,
            book INTEGER NOT NULL,
            text TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE custom_columns (
            id INTEGER PRIMARY KEY,
            label TEXT NOT NULL,
            name TEXT NOT NULL,
            datatype TEXT NOT NULL
        )
    """)

    # Insert sample data - 10 books
    books_data = [
        (1, "War and Peace", "2020-01-01", "book1", "1869-01-01"),
        (2, "Crime and Punishment", "2020-01-02", "book2", "1866-01-01"),
        (3, "The Brothers Karamazov", "2020-01-03", "book3", "1880-01-01"),
        (4, "Ulysses", "2020-01-04", "book4", "1922-01-01"),
        (5, "In Search of Lost Time", "2020-01-05", "book5", "1913-01-01"),
        (6, "Don Quixote", "2020-01-06", "book6", "1605-01-01"),
        (7, "One Hundred Years of Solitude", "2020-01-07", "book7", "1967-01-01"),
        (8, "The Great Gatsby", "2020-01-08", "book8", "1925-01-01"),
        (9, "Moby-Dick", "2020-01-09", "book9", "1851-01-01"),
        (10, "Pride and Prejudice", "2020-01-10", "book10", "1813-01-01"),
    ]

    for book_id, title, timestamp, path, pubdate in books_data:
        cursor.execute(
            "INSERT INTO books (id, title, timestamp, path, pubdate) VALUES (?, ?, ?, ?, ?)",
            (book_id, title, timestamp, path, pubdate)
        )

    # Insert authors
    authors_data = [
        (1, "Leo Tolstoy"),
        (2, "Fyodor Dostoevsky"),
        (3, "James Joyce"),
        (4, "Marcel Proust"),
        (5, "Miguel de Cervantes"),
        (6, "Gabriel García Márquez"),
        (7, "F. Scott Fitzgerald"),
        (8, "Herman Melville"),
        (9, "Jane Austen"),
    ]

    for author_id, name in authors_data:
        cursor.execute("INSERT INTO authors (id, name) VALUES (?, ?)", (author_id, name))

    # Link books to authors
    links = [
        (1, 1, 1),  # War and Peace -> Tolstoy
        (2, 2, 2),  # Crime and Punishment -> Dostoevsky
        (3, 3, 2),  # Brothers Karamazov -> Dostoevsky
        (4, 4, 3),  # Ulysses -> Joyce
        (5, 5, 4),  # In Search of Lost Time -> Proust
        (6, 6, 5),  # Don Quixote -> Cervantes
        (7, 7, 6),  # One Hundred Years -> García Márquez
        (8, 8, 7),  # Great Gatsby -> Fitzgerald
        (9, 9, 8),  # Moby-Dick -> Melville
        (10, 10, 9), # Pride and Prejudice -> Austen
    ]

    for link_id, book, author in links:
        cursor.execute(
            "INSERT INTO books_authors_link (id, book, author) VALUES (?, ?, ?)",
            (link_id, book, author)
        )

    # Insert comments (descriptions)
    comments_data = [
        (1, 1, "Epic novel about Russian society during Napoleonic era"),
        (2, 2, "Psychological exploration of crime and morality"),
        (3, 4, "Modernist masterpiece following Leopold Bloom through Dublin"),
    ]

    for comment_id, book, text in comments_data:
        cursor.execute(
            "INSERT INTO comments (id, book, text) VALUES (?, ?, ?)",
            (comment_id, book, text)
        )

    # Insert custom column for AI summary
    cursor.execute(
        "INSERT INTO custom_columns (id, label, name, datatype) VALUES (?, ?, ?, ?)",
        (1, "ai_summary", "AI Summary", "text")
    )

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def sample_scored_books_csv(tmp_path):
    """Create a sample scored books CSV file"""
    csv_file = tmp_path / "calibre_owned_scored_books.csv"

    content = """calibre_id,title,author,score,recognition
1,War and Peace,Leo Tolstoy,95,Modern Library 100 Best Novels #20
2,Crime and Punishment,Fyodor Dostoevsky,92,Modern Library 100 Best Novels #15
3,The Brothers Karamazov,Fyodor Dostoevsky,95,Modern Library 100 Best Novels #5
4,Ulysses,James Joyce,100,Modern Library 100 Best Novels #1
5,In Search of Lost Time,Marcel Proust,99,Modern Library 100 Best Novels #2
6,Don Quixote,Miguel de Cervantes,98,Modern Library 100 Best Novels #3
7,One Hundred Years of Solitude,Gabriel García Márquez,94,Modern Library 100 Best Novels #8
8,The Great Gatsby,F. Scott Fitzgerald,88,Modern Library 100 Best Novels #10
9,Moby-Dick,Herman Melville,91,Modern Library 100 Best Novels #6
10,Pride and Prejudice,Jane Austen,85,Modern Library 100 Best Novels #25
"""

    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write(content.strip())

    return csv_file


@pytest.fixture
def sample_enrichment_status(tmp_path):
    """Create a sample enrichment status JSON file"""
    status_file = tmp_path / "enrichment_status.json"

    status_data = {
        "1": {
            "status": "completed",
            "processed_date": "2024-01-15T10:00:00",
            "title": "War and Peace",
            "author": "Leo Tolstoy"
        },
        "2": {
            "status": "completed",
            "processed_date": "2024-01-15T10:05:00",
            "title": "Crime and Punishment",
            "author": "Fyodor Dostoevsky"
        },
        "3": {
            "status": "error",
            "error_date": "2024-01-15T10:10:00",
            "title": "The Brothers Karamazov",
            "author": "Fyodor Dostoevsky"
        }
    }

    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=2)

    return status_file


@pytest.fixture
def sample_enriched_books_jsonl(tmp_path):
    """Create a sample enriched books JSONL file"""
    jsonl_file = tmp_path / "enriched_books.jsonl"

    books = [
        {
            "calibre_id": 1,
            "title": "War and Peace",
            "author": "Leo Tolstoy",
            "quality_score": 95,
            "awards_and_recognition": "Modern Library 100 Best Novels #20",
            "tags": ["Russian Literature", "Historical Fiction", "War", "Philosophy"],
            "themes": ["War and Peace", "Human Nature", "Russian Society"],
            "enhanced_description": "Epic novel exploring Russian society during the Napoleonic era through the interconnected stories of aristocratic families.",
            "original_publication_year": 1869,
            "processing_date": "2024-01-15T10:00:00"
        },
        {
            "calibre_id": 2,
            "title": "Crime and Punishment",
            "author": "Fyodor Dostoevsky",
            "quality_score": 92,
            "awards_and_recognition": "Modern Library 100 Best Novels #15",
            "tags": ["Russian Literature", "Psychological Fiction", "Crime", "Morality"],
            "themes": ["Guilt and Redemption", "Poverty", "Mental Illness"],
            "enhanced_description": "Psychological exploration of a poor student who commits murder and grapples with the moral consequences.",
            "original_publication_year": 1866,
            "processing_date": "2024-01-15T10:05:00"
        }
    ]

    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for book in books:
            f.write(json.dumps(book) + '\n')

    return jsonl_file


@pytest.fixture
def mock_chromadb_collection():
    """Create a mock ChromaDB collection"""
    mock_collection = Mock()

    # Sample data
    mock_collection.count.return_value = 2

    mock_collection.get.return_value = {
        'ids': ['1', '2'],
        'metadatas': [
            {
                'title': 'War and Peace',
                'author': 'Leo Tolstoy',
                'quality_score': 95.0,
                'tags': 'Russian Literature|Historical Fiction|War|Philosophy',
                'themes': 'War and Peace|Human Nature|Russian Society',
                'description': 'Epic novel exploring Russian society.',
                'publication_year': 1869,
                'awards': 'Modern Library 100 Best Novels #20',
                'enriched_at': '2024-01-15T10:00:00'
            },
            {
                'title': 'Crime and Punishment',
                'author': 'Fyodor Dostoevsky',
                'quality_score': 92.0,
                'tags': 'Russian Literature|Psychological Fiction|Crime|Morality',
                'themes': 'Guilt and Redemption|Poverty|Mental Illness',
                'description': 'Psychological exploration of a poor student.',
                'publication_year': 1866,
                'awards': 'Modern Library 100 Best Novels #15',
                'enriched_at': '2024-01-15T10:05:00'
            }
        ]
    }

    mock_collection.query.return_value = {
        'ids': [['1', '2']],
        'metadatas': [[
            {
                'title': 'War and Peace',
                'author': 'Leo Tolstoy',
                'quality_score': 95.0,
                'tags': 'Russian Literature|Historical Fiction',
                'themes': 'War and Peace|Human Nature',
                'description': 'Epic novel exploring Russian society.',
            },
            {
                'title': 'Crime and Punishment',
                'author': 'Fyodor Dostoevsky',
                'quality_score': 92.0,
                'tags': 'Psychological Fiction|Crime',
                'themes': 'Guilt and Redemption',
                'description': 'Psychological exploration.',
            }
        ]],
        'distances': [[0.1, 0.2]]
    }

    return mock_collection


@pytest.fixture
def mock_claude_response():
    """Create a mock Claude API response"""
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = json.dumps({
        "tags": ["Historical Fiction", "Russian Literature", "War", "Philosophy", "Epic Novel"],
        "enhanced_description": "Epic novel exploring Russian society during the Napoleonic era through interconnected aristocratic families.",
        "themes": ["War and Peace", "Human Nature", "Russian Society", "Love and Death"],
        "recommended_for": "Readers interested in historical epics, philosophical novels, and Russian literature.",
        "original_publication_year": 1869
    })
    return mock_response


@pytest.fixture
def mock_openai_embedding_response():
    """Create a mock OpenAI embedding response"""
    mock_response = Mock()
    mock_response.data = [Mock()]
    # Create a simple 1536-dimensional embedding (all zeros for testing)
    mock_response.data[0].embedding = [0.0] * 1536
    return mock_response


@pytest.fixture
def mock_settings(tmp_path, mock_calibre_db, sample_scored_books_csv):
    """Create a mock settings object"""
    mock = Mock()
    mock.CALIBRE_DB_PATH = str(mock_calibre_db)
    mock.OUTPUT_DIR = str(tmp_path / "output")
    mock.DATASOURCES_DIR = str(tmp_path / "datasources")
    mock.CHROMADB_PATH = str(tmp_path / "book_vectors")
    mock.CALIBREDB_PATH = "calibredb"
    mock.ANTHROPIC_API_KEY = "test-anthropic-key"
    mock.OPENAI_API_KEY = "test-openai-key"

    # Create output directory
    Path(mock.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(mock.DATASOURCES_DIR).mkdir(parents=True, exist_ok=True)

    return mock


@pytest.fixture
def enrichment_dir(tmp_path):
    """Create enrichment directory structure"""
    enrich_dir = tmp_path / "output" / "enrichment"
    enrich_dir.mkdir(parents=True, exist_ok=True)
    return enrich_dir


@pytest.fixture
def sample_canonical_authors(tmp_path):
    """Create sample canonical authors JSON files"""
    datasources = tmp_path / "datasources"
    datasources.mkdir(exist_ok=True)

    # Tier S authors
    tier_s = {
        "canonical_authors": [
            {"author": "Leo Tolstoy"},
            {"author": "Fyodor Dostoevsky"},
            {"author": "James Joyce"}
        ]
    }

    with open(datasources / "canonical_authors_tier_s.json", 'w') as f:
        json.dump(tier_s, f)

    # Tier A authors
    tier_a = {
        "canonical_authors": [
            {"author": "Jane Austen"},
            {"author": "Herman Melville"}
        ]
    }

    with open(datasources / "canonical_authors_tier_a.json", 'w') as f:
        json.dump(tier_a, f)

    return datasources
