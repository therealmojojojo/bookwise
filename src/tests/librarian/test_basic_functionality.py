"""
Basic functionality tests that don't require ChromaDB
Tests MCP protocol structure and basic API functionality
"""
import pytest
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class TestMCPProtocolBasics:
    """Basic MCP protocol structure tests"""

    def test_mcp_initialize_structure(self):
        """Test MCP initialize request structure"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {}
            }
        }

        assert request["jsonrpc"] == "2.0"
        assert request["method"] == "initialize"
        assert "params" in request

    def test_mcp_tools_list_structure(self):
        """Test MCP tools/list request structure"""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        assert request["jsonrpc"] == "2.0"
        assert request["method"] == "tools/list"

    def test_mcp_tools_call_structure(self):
        """Test MCP tools/call request structure"""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_library",
                "arguments": {
                    "queries": ["test"],
                    "limit": 10
                }
            }
        }

        assert request["jsonrpc"] == "2.0"
        assert request["method"] == "tools/call"
        assert "name" in request["params"]
        assert "arguments" in request["params"]


class TestAPIModels:
    """Test API request/response models"""

    def test_search_library_request(self):
        """Test search library request model"""
        from src.librarian.api.models import SearchLibraryRequest

        request = SearchLibraryRequest(
            queries=["test"],
            quality_threshold=70,
            max_results=10
        )

        assert request.queries == ["test"]
        assert request.quality_threshold == 70
        assert request.max_results == 10

    def test_get_book_details_request(self):
        """Test get book details request model"""
        from src.librarian.api.models import GetBookDetailsRequest

        request = GetBookDetailsRequest(book_ids=[1, 2, 3])

        assert request.book_ids == [1, 2, 3]
        assert len(request.book_ids) == 3

    def test_get_top_books_request(self):
        """Test get top books request model"""
        from src.librarian.api.models import GetTopBooksRequest

        request = GetTopBooksRequest(
            genre="fiction",
            min_quality=80,
            limit=20
        )

        assert request.genre == "fiction"
        assert request.min_quality == 80
        assert request.limit == 20

    def test_send_book_request(self):
        """Test send book request model"""
        from src.librarian.api.models import SendBookRequest

        request = SendBookRequest(
            book_id=1,
            format="epub",
            device_name="My Kindle"
        )

        assert request.book_id == 1
        assert request.format == "epub"
        assert request.device_name == "My Kindle"


class TestConfigSettings:
    """Test configuration loading"""

    def test_config_import(self):
        """Test that config can be imported"""
        from src.librarian.config import settings

        assert settings is not None

    def test_config_attributes(self):
        """Test that config has expected attributes"""
        from src.librarian.config import settings

        # Should have these attributes even if not configured
        assert hasattr(settings, 'PORT')
        assert hasattr(settings, 'HOST')


class TestServiceImports:
    """Test that services can be imported"""

    def test_vector_search_import(self):
        """Test VectorSearchService can be imported"""
        from src.librarian.services.vector_search import VectorSearchService

        assert VectorSearchService is not None

    def test_calibre_service_import(self):
        """Test CalibreService can be imported"""
        from src.librarian.services.calibre_db import CalibreService

        assert CalibreService is not None

    def test_delivery_service_import(self):
        """Test DeliveryService can be imported"""
        from src.librarian.services.delivery_service import DeliveryService

        assert DeliveryService is not None


class TestAPIRoutesImport:
    """Test that API routes can be imported"""

    def test_routes_import(self):
        """Test routes module can be imported"""
        from src.librarian.api import router

        assert router is not None

    def test_mcp_root_import(self):
        """Test MCP root router can be imported"""
        from src.librarian.api.mcp_root import router

        assert router is not None


class TestQualityTierFunction:
    """Test quality tier mapping function"""

    def test_quality_tier_legendary(self):
        """Test legendary tier (90-100)"""
        from src.librarian.api.routes import get_quality_tier

        assert get_quality_tier(100) == "Legendary"
        assert get_quality_tier(95) == "Legendary"
        assert get_quality_tier(90) == "Legendary"

    def test_quality_tier_exceptional(self):
        """Test exceptional tier (80-89)"""
        from src.librarian.api.routes import get_quality_tier

        assert get_quality_tier(89) == "Exceptional"
        assert get_quality_tier(85) == "Exceptional"
        assert get_quality_tier(80) == "Exceptional"

    def test_quality_tier_outstanding(self):
        """Test outstanding tier (70-79)"""
        from src.librarian.api.routes import get_quality_tier

        assert get_quality_tier(79) == "Outstanding"
        assert get_quality_tier(75) == "Outstanding"
        assert get_quality_tier(70) == "Outstanding"

    def test_quality_tier_excellent(self):
        """Test excellent tier (60-69)"""
        from src.librarian.api.routes import get_quality_tier

        assert get_quality_tier(69) == "Excellent"
        assert get_quality_tier(65) == "Excellent"
        assert get_quality_tier(60) == "Excellent"

    def test_quality_tier_very_good(self):
        """Test very good tier (50-59)"""
        from src.librarian.api.routes import get_quality_tier

        assert get_quality_tier(59) == "Very Good"
        assert get_quality_tier(55) == "Very Good"
        assert get_quality_tier(50) == "Very Good"

    def test_quality_tier_good(self):
        """Test good tier (40-49)"""
        from src.librarian.api.routes import get_quality_tier

        assert get_quality_tier(49) == "Good"
        assert get_quality_tier(45) == "Good"
        assert get_quality_tier(40) == "Good"

    def test_quality_tier_lower(self):
        """Test lower quality tiers"""
        from src.librarian.api.routes import get_quality_tier

        # Solid: 30-39
        assert get_quality_tier(35) == "Solid"
        assert get_quality_tier(30) == "Solid"

        # Notable: 20-29
        assert get_quality_tier(25) == "Notable"
        assert get_quality_tier(20) == "Notable"

        # Recognized: 10-19
        assert get_quality_tier(15) == "Recognized"
        assert get_quality_tier(10) == "Recognized"

        # Limited: <10
        assert get_quality_tier(5) == "Limited"
        assert get_quality_tier(0) == "Limited"


class TestMCPToolDefinitions:
    """Test MCP tool definitions structure"""

    @pytest.mark.asyncio
    async def test_tool_definitions_exist(self):
        """Test that tool definitions can be accessed"""
        from src.librarian.mcp_server import list_tools

        tools = await list_tools()

        assert isinstance(tools, list)
        assert len(tools) == 4

    @pytest.mark.asyncio
    async def test_tool_names(self):
        """Test that all expected tools are defined"""
        from src.librarian.mcp_server import list_tools

        tools = await list_tools()
        tool_names = [t.name for t in tools]

        assert "search_library" in tool_names
        assert "get_book_details" in tool_names
        assert "get_library_stats" in tool_names
        assert "export_book_to_ereader" in tool_names

    @pytest.mark.asyncio
    async def test_tool_structure(self):
        """Test that tools have required fields"""
        from src.librarian.mcp_server import list_tools

        tools = await list_tools()

        for tool in tools:
            # Tools are Pydantic models with these attributes
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
            assert tool.name is not None
            assert tool.description is not None
            assert tool.inputSchema is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
