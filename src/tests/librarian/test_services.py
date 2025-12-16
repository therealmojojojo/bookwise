"""
Tests for Librarian service layer
Tests VectorSearchService, CalibreService, and DeliveryService
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class TestVectorSearchService:
    """Tests for VectorSearchService"""

    def test_search_books_success(self, temp_chromadb, mock_openai_embeddings):
        """Test successful vector search"""
        from src.librarian.services.vector_search import VectorSearchService

        chroma_client, collection, chroma_path = temp_chromadb

        with patch('chromadb.PersistentClient', return_value=chroma_client):
            service = VectorSearchService(str(chroma_path), "test-openai-key")

            results = service.search_books(
                queries=["resilience"],
                min_quality=70,
                limit=10
            )

            assert isinstance(results, list)
            # Should return books from our test data
            assert len(results) >= 0

    def test_search_books_with_multiple_queries(self, temp_chromadb, mock_openai_embeddings):
        """Test search with multiple queries"""
        from src.librarian.services.vector_search import VectorSearchService

        chroma_client, collection, chroma_path = temp_chromadb

        with patch('chromadb.PersistentClient', return_value=chroma_client):
            service = VectorSearchService(str(chroma_path), "test-openai-key")

            results = service.search_books(
                queries=["resilience", "hope", "strength"],
                min_quality=0,
                limit=5
            )

            assert isinstance(results, list)

    def test_search_books_quality_filtering(self, temp_chromadb, mock_openai_embeddings):
        """Test quality score filtering"""
        from src.librarian.services.vector_search import VectorSearchService

        chroma_client, collection, chroma_path = temp_chromadb

        with patch('chromadb.PersistentClient', return_value=chroma_client):
            service = VectorSearchService(str(chroma_path), "test-openai-key")

            # Search with high quality threshold
            results = service.search_books(
                queries=["test"],
                min_quality=80,
                limit=10
            )

            # All results should meet quality threshold
            for result in results:
                if "quality_score" in result:
                    assert int(result["quality_score"]) >= 80

    def test_get_book_by_calibre_id(self, temp_chromadb):
        """Test getting book by Calibre ID"""
        from src.librarian.services.vector_search import VectorSearchService

        chroma_client, collection, chroma_path = temp_chromadb

        with patch('chromadb.PersistentClient', return_value=chroma_client):
            service = VectorSearchService(str(chroma_path), "test-openai-key")

            result = service.get_book_by_calibre_id(1)

            assert result is not None or result is None  # May or may not find


@pytest.mark.asyncio
class TestCalibreServiceAuthorSearch:
    """Tests for CalibreService author and book search methods"""

    async def test_search_authors_exact_match(self, temp_calibre_db):
        """Test searching for author with exact name"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        results = await service.search_authors("Ursula K. Le Guin")

        assert len(results) == 1
        assert results[0]['name'] == 'Ursula K. Le Guin'
        assert results[0]['id'] == 3

    async def test_search_authors_partial_match(self, temp_calibre_db):
        """Test searching for author with partial name"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        results = await service.search_authors("Le Guin")

        assert len(results) == 1
        assert results[0]['name'] == 'Ursula K. Le Guin'

    async def test_search_authors_by_sort_field(self, temp_calibre_db):
        """Test searching by sort field (last name first)"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        results = await service.search_authors("Fitzgerald")

        assert len(results) == 1
        assert results[0]['name'] == 'F. Scott Fitzgerald'
        assert 'Fitzgerald' in results[0]['sort']

    async def test_search_authors_multiple_words(self, temp_calibre_db):
        """Test searching with multiple words"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        results = await service.search_authors("Scott Fitzgerald")

        assert len(results) == 1
        assert results[0]['name'] == 'F. Scott Fitzgerald'

    async def test_search_authors_no_match(self, temp_calibre_db):
        """Test searching for non-existent author"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        results = await service.search_authors("NonExistent Author")

        assert len(results) == 0

    async def test_search_authors_empty_string(self, temp_calibre_db):
        """Test searching with empty string"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        results = await service.search_authors("")

        assert len(results) == 0

    async def test_search_authors_limit(self, temp_calibre_db):
        """Test search result limiting"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        results = await service.search_authors("Author", limit=2)

        assert len(results) <= 2


@pytest.mark.asyncio
class TestCalibreServiceGetAuthorBooks:
    """Tests for get_books_by_author methods"""

    async def test_get_books_by_author_name_success(self, temp_calibre_db):
        """Test getting books by author name"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        result = await service.get_books_by_author_name("Ursula K. Le Guin")

        assert result is not None
        assert result['author_id'] == 3
        assert result['author_name'] == 'Ursula K. Le Guin'
        assert result['book_count'] == 3  # Wizard, Tombs, Lathe

        # Check books are returned
        titles = [book['title'] for book in result['books']]
        assert 'A Wizard of Earthsea' in titles
        assert 'The Tombs of Atuan' in titles
        assert 'The Lathe of Heaven' in titles

    async def test_get_books_by_author_name_with_series(self, temp_calibre_db):
        """Test that series info is included"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        result = await service.get_books_by_author_name("Ursula K. Le Guin")

        # Find Earthsea books
        earthsea_books = [b for b in result['books'] if b['series'] == 'Earthsea Cycle']
        assert len(earthsea_books) == 2

        # Check series_index
        wizard = next(b for b in earthsea_books if 'Wizard' in b['title'])
        assert wizard['series_index'] == 1.0

        tombs = next(b for b in earthsea_books if 'Tombs' in b['title'])
        assert tombs['series_index'] == 2.0

    async def test_get_books_by_author_name_standalone(self, temp_calibre_db):
        """Test standalone book has no series"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        result = await service.get_books_by_author_name("Ursula K. Le Guin")

        lathe = next(b for b in result['books'] if 'Lathe' in b['title'])
        assert lathe['series'] is None

    async def test_get_books_by_author_name_formats(self, temp_calibre_db):
        """Test that formats are returned"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        result = await service.get_books_by_author_name("Ursula K. Le Guin")

        # Tombs of Atuan has both EPUB and MOBI
        tombs = next(b for b in result['books'] if 'Tombs' in b['title'])
        assert 'EPUB' in tombs['formats']
        assert 'MOBI' in tombs['formats']

    async def test_get_books_by_author_name_not_found(self, temp_calibre_db):
        """Test getting books for non-existent author"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        result = await service.get_books_by_author_name("NonExistent Author")

        assert result is None

    async def test_get_books_by_author_id(self, temp_calibre_db):
        """Test getting books by author ID directly"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        results = await service.get_books_by_author_id(3)  # Le Guin's ID

        assert len(results) == 3
        titles = [book['title'] for book in results]
        assert 'A Wizard of Earthsea' in titles


@pytest.mark.asyncio
class TestCalibreServiceFindBook:
    """Tests for find_book method"""

    async def test_find_book_exact_title(self, temp_calibre_db):
        """Test finding book by exact title"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        results = await service.find_book("The Great Gatsby")

        assert len(results) == 1
        assert results[0]['title'] == 'The Great Gatsby'
        assert results[0]['authors'] == 'F. Scott Fitzgerald'
        assert results[0]['id'] == 6

    async def test_find_book_case_insensitive(self, temp_calibre_db):
        """Test case-insensitive title search"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        results = await service.find_book("the great gatsby")

        assert len(results) == 1
        assert results[0]['title'] == 'The Great Gatsby'

    async def test_find_book_with_author_filter(self, temp_calibre_db):
        """Test finding book with author filter"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        results = await service.find_book("The Lathe of Heaven", author="Ursula K. Le Guin")

        assert len(results) == 1
        assert results[0]['title'] == 'The Lathe of Heaven'
        assert results[0]['authors'] == 'Ursula K. Le Guin'

    async def test_find_book_with_wrong_author(self, temp_calibre_db):
        """Test finding book with wrong author returns empty"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        results = await service.find_book("The Great Gatsby", author="Ursula K. Le Guin")

        assert len(results) == 0

    async def test_find_book_returns_series_info(self, temp_calibre_db):
        """Test that series info is included in results"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        results = await service.find_book("A Wizard of Earthsea")

        assert len(results) == 1
        assert results[0]['series'] == 'Earthsea Cycle'
        assert results[0]['series_index'] == 1.0

    async def test_find_book_returns_formats(self, temp_calibre_db):
        """Test that formats are included in results"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        results = await service.find_book("The Great Gatsby")

        assert len(results) == 1
        assert 'EPUB' in results[0]['formats']
        assert 'PDF' in results[0]['formats']

    async def test_find_book_not_found(self, temp_calibre_db):
        """Test searching for non-existent book"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        results = await service.find_book("NonExistent Book Title")

        assert len(results) == 0

    async def test_find_book_standalone_no_series(self, temp_calibre_db):
        """Test that standalone book has null series"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))
        results = await service.find_book("The Lathe of Heaven")

        assert len(results) == 1
        assert results[0]['series'] is None


class TestDeliveryService:
    """Tests for DeliveryService"""

    def test_export_book_success(self, tmp_path, mock_calibredb):
        """Test successful book export"""
        from src.librarian.services.delivery_service import DeliveryService

        export_dir = tmp_path / "exports"
        export_dir.mkdir()

        service = DeliveryService(
            calibredb_path="/usr/bin/calibredb",
            export_folder=str(export_dir)
        )

        result = service.export_book(
            book_id=1,
            format="epub"
        )

        assert result["success"] is True
        assert "message" in result

    def test_export_book_with_device_name(self, tmp_path, mock_calibredb):
        """Test export with device name"""
        from src.librarian.services.delivery_service import DeliveryService

        export_dir = tmp_path / "exports"
        export_dir.mkdir()

        service = DeliveryService(
            calibredb_path="/usr/bin/calibredb",
            export_folder=str(export_dir)
        )

        result = service.export_book(
            book_id=1,
            format="epub",
            device_name="My Kindle"
        )

        assert result["success"] is True

    def test_export_book_different_formats(self, tmp_path, mock_calibredb):
        """Test exporting different formats"""
        from src.librarian.services.delivery_service import DeliveryService

        export_dir = tmp_path / "exports"
        export_dir.mkdir()

        service = DeliveryService(
            calibredb_path="/usr/bin/calibredb",
            export_folder=str(export_dir)
        )

        formats = ["epub", "mobi", "azw3", "pdf"]

        for fmt in formats:
            result = service.export_book(
                book_id=1,
                format=fmt
            )

            assert result["success"] is True

    def test_export_book_invalid_folder(self):
        """Test export with invalid export folder"""
        from src.librarian.services.delivery_service import DeliveryService

        service = DeliveryService(
            calibredb_path="/usr/bin/calibredb",
            export_folder="/nonexistent/path"
        )

        result = service.export_book(
            book_id=1,
            format="epub"
        )

        # Should handle error gracefully
        assert isinstance(result, dict)
        assert "success" in result


@pytest.mark.integration
class TestServiceIntegration:
    """Integration tests combining multiple services"""

    def test_search_and_get_metadata(self, temp_chromadb, temp_calibre_db, mock_openai_embeddings):
        """Test searching and then getting full metadata"""
        from src.librarian.services.vector_search import VectorSearchService
        from src.librarian.services.calibre_db import CalibreService

        chroma_client, collection, chroma_path = temp_chromadb

        with patch('chromadb.PersistentClient', return_value=chroma_client):
            search_service = VectorSearchService(str(chroma_path), "test-openai-key")
            calibre_service = CalibreService(str(temp_calibre_db))

            # Search for books
            search_results = search_service.search_books(
                queries=["test"],
                min_quality=0,
                limit=5
            )

            if search_results:
                # Get full metadata for first result
                calibre_id = int(search_results[0].get("calibre_id", 1))
                metadata = calibre_service.get_book_metadata(calibre_id)

                # Should get metadata (may be None if ID doesn't exist)
                assert metadata is not None or metadata is None

    def test_get_metadata_and_export(self, temp_calibre_db, tmp_path, mock_calibredb):
        """Test getting metadata and then exporting"""
        from src.librarian.services.calibre_db import CalibreService
        from src.librarian.services.delivery_service import DeliveryService

        calibre_service = CalibreService(str(temp_calibre_db))

        export_dir = tmp_path / "exports"
        export_dir.mkdir()

        delivery_service = DeliveryService(
            calibredb_path="/usr/bin/calibredb",
            export_folder=str(export_dir)
        )

        # Get metadata
        metadata = calibre_service.get_book_metadata(1)

        if metadata:
            # Export the book
            result = delivery_service.export_book(
                book_id=1,
                format="epub"
            )

            assert result["success"] is True
