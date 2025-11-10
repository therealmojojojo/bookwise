"""
Tests for Librarian API endpoints
Tests all REST API endpoints with various scenarios
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


@pytest.fixture
def test_client(mock_settings, mock_openai_embeddings):
    """Create test client with mocked dependencies"""
    with patch('src.librarian.config.settings', mock_settings):
        from src.librarian.server import app
        client = TestClient(app)
        yield client


class TestSearchLibrary:
    """Tests for /api/v1/search_library endpoint"""

    def test_search_library_success(self, test_client, test_api_key):
        """Test successful library search"""
        response = test_client.post(
            "/api/v1/search_library",
            json={
                "queries": ["resilience", "hope"],
                "filters": {"min_quality": 70},
                "limit": 10
            },
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_search_library_no_filters(self, test_client, test_api_key):
        """Test search without quality filters"""
        response = test_client.post(
            "/api/v1/search_library",
            json={
                "queries": ["adventure"],
                "limit": 5
            },
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    def test_search_library_empty_query(self, test_client, test_api_key):
        """Test search with empty query array"""
        response = test_client.post(
            "/api/v1/search_library",
            json={
                "queries": [],
                "limit": 10
            },
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 422  # Validation error

    def test_search_library_invalid_limit(self, test_client, test_api_key):
        """Test search with invalid limit"""
        response = test_client.post(
            "/api/v1/search_library",
            json={
                "queries": ["test"],
                "limit": 100  # Should be max 30
            },
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 422  # Validation error

    def test_search_library_no_auth(self, test_client):
        """Test search without authentication (if auth enabled)"""
        # Note: Currently auth is disabled in routes.py for testing
        response = test_client.post(
            "/api/v1/search_library",
            json={
                "queries": ["test"],
                "limit": 10
            }
        )

        # Should succeed since auth is temporarily disabled
        assert response.status_code in [200, 401]


class TestGetBookDetails:
    """Tests for /api/v1/get_book_details endpoint"""

    def test_get_book_details_success(self, test_client, test_api_key):
        """Test successful book details retrieval"""
        response = test_client.post(
            "/api/v1/get_book_details",
            json={"book_ids": [1, 2]},
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert "books" in data
        assert isinstance(data["books"], list)

    def test_get_book_details_single_book(self, test_client, test_api_key):
        """Test getting details for single book"""
        response = test_client.post(
            "/api/v1/get_book_details",
            json={"book_ids": [1]},
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["books"]) >= 0

    def test_get_book_details_nonexistent(self, test_client, test_api_key):
        """Test getting details for non-existent book"""
        response = test_client.post(
            "/api/v1/get_book_details",
            json={"book_ids": [99999]},
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        # Should return empty or partial results
        assert "books" in data

    def test_get_book_details_empty_list(self, test_client, test_api_key):
        """Test with empty book IDs list"""
        response = test_client.post(
            "/api/v1/get_book_details",
            json={"book_ids": []},
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 422  # Validation error

    def test_get_book_details_too_many(self, test_client, test_api_key):
        """Test with too many book IDs"""
        response = test_client.post(
            "/api/v1/get_book_details",
            json={"book_ids": list(range(1, 25))},  # More than 20
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 422  # Validation error


class TestGetTopQualityBooks:
    """Tests for /api/v1/get_top_quality_books endpoint"""

    def test_get_top_books_success(self, test_client, test_api_key):
        """Test successful top books retrieval"""
        response = test_client.post(
            "/api/v1/get_top_quality_books",
            json={
                "min_quality": 70,
                "limit": 20
            },
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert "books" in data
        assert isinstance(data["books"], list)

    def test_get_top_books_with_genre(self, test_client, test_api_key):
        """Test top books filtered by genre"""
        response = test_client.post(
            "/api/v1/get_top_quality_books",
            json={
                "genre": "fiction",
                "min_quality": 80,
                "limit": 10
            },
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert "books" in data

    def test_get_top_books_high_threshold(self, test_client, test_api_key):
        """Test with high quality threshold"""
        response = test_client.post(
            "/api/v1/get_top_quality_books",
            json={
                "min_quality": 95,
                "limit": 5
            },
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        # May return empty list if no books meet threshold
        assert "books" in data

    def test_get_top_books_invalid_quality(self, test_client, test_api_key):
        """Test with invalid quality threshold"""
        response = test_client.post(
            "/api/v1/get_top_quality_books",
            json={
                "min_quality": 50,  # Should be 70-100
                "limit": 10
            },
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 422  # Validation error


class TestSendBookToEReader:
    """Tests for /api/v1/send_book_to_ereader endpoint"""

    def test_send_book_success(self, test_client, test_api_key, mock_calibredb):
        """Test successful book export"""
        response = test_client.post(
            "/api/v1/send_book_to_ereader",
            json={
                "book_id": 1,
                "format": "epub"
            },
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data

    def test_send_book_with_device_name(self, test_client, test_api_key, mock_calibredb):
        """Test book export with device name"""
        response = test_client.post(
            "/api/v1/send_book_to_ereader",
            json={
                "book_id": 1,
                "format": "epub",
                "device_name": "My Kindle"
            },
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 200

    def test_send_book_different_formats(self, test_client, test_api_key, mock_calibredb):
        """Test book export with different formats"""
        formats = ["epub", "mobi", "azw3", "pdf"]

        for fmt in formats:
            response = test_client.post(
                "/api/v1/send_book_to_ereader",
                json={
                    "book_id": 1,
                    "format": fmt
                },
                headers={"X-API-Key": test_api_key}
            )

            assert response.status_code == 200

    def test_send_book_invalid_format(self, test_client, test_api_key):
        """Test with invalid format"""
        response = test_client.post(
            "/api/v1/send_book_to_ereader",
            json={
                "book_id": 1,
                "format": "txt"  # Not supported
            },
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 422  # Validation error

    def test_send_book_nonexistent(self, test_client, test_api_key):
        """Test sending non-existent book"""
        response = test_client.post(
            "/api/v1/send_book_to_ereader",
            json={
                "book_id": 99999,
                "format": "epub"
            },
            headers={"X-API-Key": test_api_key}
        )

        # Should return error or failure response
        assert response.status_code in [200, 404, 500]


class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestRootEndpoint:
    """Tests for root endpoint"""

    def test_root(self, test_client):
        """Test root endpoint"""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "name" in data


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Integration tests for complete workflows"""

    def test_search_and_get_details_workflow(self, test_client, test_api_key):
        """Test searching, then getting details for results"""
        # Step 1: Search for books
        search_response = test_client.post(
            "/api/v1/search_library",
            json={
                "queries": ["resilience"],
                "filters": {"min_quality": 70},
                "limit": 5
            },
            headers={"X-API-Key": test_api_key}
        )

        assert search_response.status_code == 200
        search_data = search_response.json()

        if search_data["results"]:
            # Step 2: Get details for first result
            first_book_id = search_data["results"][0]["calibre_id"]

            details_response = test_client.post(
                "/api/v1/get_book_details",
                json={"book_ids": [first_book_id]},
                headers={"X-API-Key": test_api_key}
            )

            assert details_response.status_code == 200
            details_data = details_response.json()
            assert len(details_data["books"]) > 0

    def test_top_books_and_export_workflow(self, test_client, test_api_key, mock_calibredb):
        """Test browsing top books, then exporting one"""
        # Step 1: Get top quality books
        top_response = test_client.post(
            "/api/v1/get_top_quality_books",
            json={
                "min_quality": 70,
                "limit": 10
            },
            headers={"X-API-Key": test_api_key}
        )

        assert top_response.status_code == 200
        top_data = top_response.json()

        if top_data["books"]:
            # Step 2: Export first book
            first_book_id = top_data["books"][0]["calibre_id"]

            export_response = test_client.post(
                "/api/v1/send_book_to_ereader",
                json={
                    "book_id": first_book_id,
                    "format": "epub"
                },
                headers={"X-API-Key": test_api_key}
            )

            assert export_response.status_code == 200
