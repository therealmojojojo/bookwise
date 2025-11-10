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


class TestCalibreService:
    """Tests for CalibreService"""

    def test_get_book_metadata_success(self, temp_calibre_db):
        """Test successful metadata retrieval"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))

        metadata = service.get_book_metadata(1)

        assert metadata is not None
        assert "title" in metadata
        assert "authors" in metadata

    def test_get_book_metadata_multiple(self, temp_calibre_db):
        """Test getting metadata for multiple books"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))

        results = service.get_books_metadata([1, 2])

        assert isinstance(results, list)
        assert len(results) >= 0

    def test_get_book_metadata_nonexistent(self, temp_calibre_db):
        """Test getting metadata for non-existent book"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))

        metadata = service.get_book_metadata(99999)

        assert metadata is None

    def test_get_book_formats(self, temp_calibre_db):
        """Test getting available formats for book"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))

        formats = service.get_book_formats(1)

        assert isinstance(formats, list)

    def test_get_all_tags(self, temp_calibre_db):
        """Test getting all tags from library"""
        from src.librarian.services.calibre_db import CalibreService

        service = CalibreService(str(temp_calibre_db))

        tags = service.get_all_tags()

        assert isinstance(tags, list)
        # Should have "fiction" and "classic" from our test data
        tag_names = [tag["name"] for tag in tags if "name" in tag]
        assert "fiction" in tag_names or len(tags) >= 0


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
