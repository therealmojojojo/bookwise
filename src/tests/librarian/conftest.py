"""
Test fixtures for Librarian API tests
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Try to import chromadb, but make it optional
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    chromadb = None
    ChromaSettings = None


@pytest.fixture
def temp_chromadb(tmp_path):
    """Create temporary ChromaDB for testing"""
    if not HAS_CHROMADB:
        pytest.skip("chromadb not installed")

    chroma_path = tmp_path / "test_vectors"
    chroma_path.mkdir()

    client = chromadb.PersistentClient(
        path=str(chroma_path),
        settings=ChromaSettings(anonymized_telemetry=False)
    )

    # Create test collection
    collection = client.get_or_create_collection(
        name="book_embeddings",
        metadata={"hnsw:space": "cosine"}
    )

    # Add sample book data
    collection.add(
        ids=["1", "2", "3"],
        embeddings=[
            [0.1] * 3072,  # Mock embedding
            [0.2] * 3072,
            [0.3] * 3072
        ],
        metadatas=[
            {
                "calibre_id": "1",
                "title": "Test Book 1",
                "author": "Test Author 1",
                "quality_score": "85",
                "themes": "resilience, hope",
                "description": "A test book about resilience"
            },
            {
                "calibre_id": "2",
                "title": "Test Book 2",
                "author": "Test Author 2",
                "quality_score": "75",
                "themes": "adventure, journey",
                "description": "A test book about adventure"
            },
            {
                "calibre_id": "3",
                "title": "Test Book 3",
                "author": "Test Author 3",
                "quality_score": "65",
                "themes": "mystery, suspense",
                "description": "A test book about mystery"
            }
        ]
    )

    yield client, collection, chroma_path

    # Cleanup
    client.reset()


@pytest.fixture
def temp_calibre_db(tmp_path):
    """Create temporary Calibre database for testing"""
    import sqlite3

    db_path = tmp_path / "metadata.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create minimal Calibre schema
    cursor.execute("""
        CREATE TABLE books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            sort TEXT,
            timestamp TIMESTAMP,
            pubdate TIMESTAMP,
            series_index REAL,
            author_sort TEXT,
            isbn TEXT,
            lccn TEXT,
            path TEXT NOT NULL,
            flags INTEGER,
            uuid TEXT,
            has_cover BOOL
        )
    """)

    cursor.execute("""
        CREATE TABLE authors (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            sort TEXT,
            link TEXT
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

    cursor.execute("""
        CREATE TABLE data (
            id INTEGER PRIMARY KEY,
            book INTEGER NOT NULL,
            format TEXT NOT NULL,
            uncompressed_size INTEGER,
            name TEXT NOT NULL,
            FOREIGN KEY(book) REFERENCES books(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE series (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL COLLATE NOCASE,
            sort TEXT COLLATE NOCASE
        )
    """)

    cursor.execute("""
        CREATE TABLE books_series_link (
            id INTEGER PRIMARY KEY,
            book INTEGER NOT NULL,
            series INTEGER NOT NULL,
            FOREIGN KEY(book) REFERENCES books(id),
            FOREIGN KEY(series) REFERENCES series(id)
        )
    """)

    # Insert sample authors
    cursor.execute("INSERT INTO authors (id, name, sort) VALUES (1, 'Test Author 1', 'Author 1, Test')")
    cursor.execute("INSERT INTO authors (id, name, sort) VALUES (2, 'Test Author 2', 'Author 2, Test')")
    cursor.execute("INSERT INTO authors (id, name, sort) VALUES (3, 'Ursula K. Le Guin', 'Le Guin, Ursula K.')")
    cursor.execute("INSERT INTO authors (id, name, sort) VALUES (4, 'F. Scott Fitzgerald', 'Fitzgerald, F. Scott')")

    # Insert sample series
    cursor.execute("INSERT INTO series (id, name, sort) VALUES (1, 'Earthsea Cycle', 'Earthsea Cycle')")
    cursor.execute("INSERT INTO series (id, name, sort) VALUES (2, 'Test Series', 'Test Series')")

    # Insert sample books
    cursor.execute("""
        INSERT INTO books (id, title, sort, path, uuid, has_cover, series_index)
        VALUES (1, 'Test Book 1', 'Test Book 1', 'Test Author 1/Test Book 1 (1)', 'test-uuid-1', 1, 1.0)
    """)
    cursor.execute("""
        INSERT INTO books (id, title, sort, path, uuid, has_cover, series_index)
        VALUES (2, 'Test Book 2', 'Test Book 2', 'Test Author 2/Test Book 2 (2)', 'test-uuid-2', 1, 1.0)
    """)
    cursor.execute("""
        INSERT INTO books (id, title, sort, path, uuid, has_cover, series_index)
        VALUES (3, 'A Wizard of Earthsea', 'Wizard of Earthsea, A', 'Ursula K. Le Guin/A Wizard of Earthsea (3)', 'test-uuid-3', 1, 1.0)
    """)
    cursor.execute("""
        INSERT INTO books (id, title, sort, path, uuid, has_cover, series_index)
        VALUES (4, 'The Tombs of Atuan', 'Tombs of Atuan, The', 'Ursula K. Le Guin/The Tombs of Atuan (4)', 'test-uuid-4', 1, 2.0)
    """)
    cursor.execute("""
        INSERT INTO books (id, title, sort, path, uuid, has_cover, series_index)
        VALUES (5, 'The Lathe of Heaven', 'Lathe of Heaven, The', 'Ursula K. Le Guin/The Lathe of Heaven (5)', 'test-uuid-5', 1, 1.0)
    """)
    cursor.execute("""
        INSERT INTO books (id, title, sort, path, uuid, has_cover, series_index)
        VALUES (6, 'The Great Gatsby', 'Great Gatsby, The', 'F. Scott Fitzgerald/The Great Gatsby (6)', 'test-uuid-6', 1, 1.0)
    """)

    # Link books to authors
    cursor.execute("INSERT INTO books_authors_link (book, author) VALUES (1, 1)")
    cursor.execute("INSERT INTO books_authors_link (book, author) VALUES (2, 2)")
    cursor.execute("INSERT INTO books_authors_link (book, author) VALUES (3, 3)")  # Wizard of Earthsea -> Le Guin
    cursor.execute("INSERT INTO books_authors_link (book, author) VALUES (4, 3)")  # Tombs of Atuan -> Le Guin
    cursor.execute("INSERT INTO books_authors_link (book, author) VALUES (5, 3)")  # Lathe of Heaven -> Le Guin
    cursor.execute("INSERT INTO books_authors_link (book, author) VALUES (6, 4)")  # Great Gatsby -> Fitzgerald

    # Link books to series
    cursor.execute("INSERT INTO books_series_link (book, series) VALUES (3, 1)")  # Wizard of Earthsea -> Earthsea
    cursor.execute("INSERT INTO books_series_link (book, series) VALUES (4, 1)")  # Tombs of Atuan -> Earthsea

    # Insert tags
    cursor.execute("INSERT INTO tags (id, name) VALUES (1, 'fiction')")
    cursor.execute("INSERT INTO tags (id, name) VALUES (2, 'classic')")
    cursor.execute("INSERT INTO tags (id, name) VALUES (3, 'fantasy')")

    cursor.execute("INSERT INTO books_tags_link (book, tag) VALUES (1, 1)")
    cursor.execute("INSERT INTO books_tags_link (book, tag) VALUES (3, 3)")  # Earthsea -> fantasy
    cursor.execute("INSERT INTO books_tags_link (book, tag) VALUES (6, 2)")  # Gatsby -> classic

    # Insert format data
    cursor.execute("INSERT INTO data (book, format, name) VALUES (1, 'EPUB', 'Test Book 1')")
    cursor.execute("INSERT INTO data (book, format, name) VALUES (2, 'EPUB', 'Test Book 2')")
    cursor.execute("INSERT INTO data (book, format, name) VALUES (3, 'EPUB', 'A Wizard of Earthsea')")
    cursor.execute("INSERT INTO data (book, format, name) VALUES (4, 'EPUB', 'The Tombs of Atuan')")
    cursor.execute("INSERT INTO data (book, format, name) VALUES (4, 'MOBI', 'The Tombs of Atuan')")
    cursor.execute("INSERT INTO data (book, format, name) VALUES (5, 'EPUB', 'The Lathe of Heaven')")
    cursor.execute("INSERT INTO data (book, format, name) VALUES (6, 'EPUB', 'The Great Gatsby')")
    cursor.execute("INSERT INTO data (book, format, name) VALUES (6, 'PDF', 'The Great Gatsby')")

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def mock_openai_embeddings(monkeypatch):
    """Mock OpenAI embeddings API"""
    def mock_create(*args, **kwargs):
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 3072)]
        return mock_response

    mock_client = Mock()
    mock_client.embeddings.create = mock_create

    def mock_openai(*args, **kwargs):
        return mock_client

    monkeypatch.setattr("openai.OpenAI", mock_openai)
    return mock_client


@pytest.fixture
def mock_calibredb(tmp_path, monkeypatch):
    """Mock calibredb CLI for export testing"""
    export_dir = tmp_path / "exports"
    export_dir.mkdir()

    def mock_run(*args, **kwargs):
        # Simulate successful calibredb export
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Book exported successfully"
        mock_result.stderr = ""
        return mock_result

    monkeypatch.setattr("subprocess.run", mock_run)

    yield export_dir


@pytest.fixture
def test_api_key():
    """Test API key for authentication"""
    return "test-api-key-12345"


@pytest.fixture
def mock_settings(tmp_path, temp_chromadb, temp_calibre_db, test_api_key):
    """Mock settings for testing"""
    from unittest.mock import Mock

    chroma_client, chroma_collection, chroma_path = temp_chromadb

    settings = Mock()
    settings.CALIBRE_DB_PATH = str(temp_calibre_db)
    settings.CHROMADB_PATH = str(chroma_path)
    settings.EREADER_EXPORT_FOLDER = str(tmp_path / "exports")
    settings.CALIBREDB_PATH = "/usr/bin/calibredb"
    settings.OPENAI_API_KEY = "test-openai-key"
    settings.BOOKWISE_API_KEY = test_api_key
    settings.PORT = 8000
    settings.HOST = "127.0.0.1"

    return settings
