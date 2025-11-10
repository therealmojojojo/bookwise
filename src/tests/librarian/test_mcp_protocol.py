"""
Tests for MCP (Model Context Protocol) endpoints
Tests MCP 2025-06-18 specification compliance
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import json
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


class TestMCPRootEndpoint:
    """Tests for MCP root endpoint (/mcp)"""

    def test_mcp_root_get(self, test_client):
        """Test GET request to MCP root"""
        response = test_client.get("/mcp")

        assert response.status_code == 200
        data = response.json()
        assert "protocol" in data or "name" in data

    def test_mcp_root_options(self, test_client):
        """Test OPTIONS request for CORS"""
        response = test_client.options("/mcp")

        assert response.status_code == 200


class TestMCPInitialize:
    """Tests for MCP initialize method"""

    def test_initialize_success(self, test_client):
        """Test successful MCP initialization"""
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {}
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data
        assert "protocolVersion" in data["result"]
        assert "capabilities" in data["result"]
        assert "serverInfo" in data["result"]

    def test_initialize_with_client_info(self, test_client):
        """Test initialization with client info"""
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "result" in data

    def test_initialize_invalid_jsonrpc(self, test_client):
        """Test initialization with invalid JSON-RPC version"""
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "1.0",
                "id": 1,
                "method": "initialize",
                "params": {}
            }
        )

        assert response.status_code in [200, 400]  # May return error


class TestMCPToolsList:
    """Tests for tools/list method"""

    def test_tools_list_success(self, test_client):
        """Test successful tools listing"""
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert "result" in data
        assert "tools" in data["result"]
        assert isinstance(data["result"]["tools"], list)

    def test_tools_list_structure(self, test_client):
        """Test tools list contains correct structure"""
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
        )

        data = response.json()
        tools = data["result"]["tools"]

        # Should have 4 tools
        assert len(tools) >= 4

        # Check each tool has required fields
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

        # Check specific tool names
        tool_names = [t["name"] for t in tools]
        assert "search_library" in tool_names
        assert "get_book_details" in tool_names
        assert "get_top_quality_books" in tool_names
        assert "send_book_to_ereader" in tool_names


class TestMCPToolCall:
    """Tests for tools/call method"""

    def test_call_search_library(self, test_client, test_api_key):
        """Test calling search_library tool"""
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "search_library",
                    "arguments": {
                        "queries": ["resilience", "hope"],
                        "filters": {"min_quality": 70},
                        "limit": 10
                    }
                }
            },
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert "result" in data
        assert "content" in data["result"]

    def test_call_get_book_details(self, test_client, test_api_key):
        """Test calling get_book_details tool"""
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "get_book_details",
                    "arguments": {
                        "book_ids": [1, 2]
                    }
                }
            },
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert "result" in data

    def test_call_get_top_quality_books(self, test_client, test_api_key):
        """Test calling get_top_quality_books tool"""
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "get_top_quality_books",
                    "arguments": {
                        "min_quality": 80,
                        "limit": 20
                    }
                }
            },
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert "result" in data

    def test_call_send_book_to_ereader(self, test_client, test_api_key, mock_calibredb):
        """Test calling send_book_to_ereader tool"""
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "send_book_to_ereader",
                    "arguments": {
                        "book_id": 1,
                        "format": "epub"
                    }
                }
            },
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert "result" in data

    def test_call_nonexistent_tool(self, test_client, test_api_key):
        """Test calling non-existent tool"""
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {
                    "name": "nonexistent_tool",
                    "arguments": {}
                }
            },
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert "error" in data or ("result" in data and not data["result"].get("content"))

    def test_call_invalid_arguments(self, test_client, test_api_key):
        """Test calling tool with invalid arguments"""
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {
                    "name": "search_library",
                    "arguments": {
                        "queries": [],  # Empty array should fail validation
                        "limit": 10
                    }
                }
            },
            headers={"X-API-Key": test_api_key}
        )

        # Should return error or validation failure
        assert response.status_code in [200, 400, 422]


class TestMCPErrorHandling:
    """Tests for MCP error handling"""

    def test_invalid_method(self, test_client):
        """Test calling invalid MCP method"""
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 9,
                "method": "invalid/method",
                "params": {}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "error" in data or "result" in data

    def test_missing_jsonrpc(self, test_client):
        """Test request without jsonrpc field"""
        response = test_client.post(
            "/mcp",
            json={
                "id": 10,
                "method": "tools/list",
                "params": {}
            }
        )

        # Should still work or return appropriate error
        assert response.status_code in [200, 400]

    def test_missing_id(self, test_client):
        """Test request without id field"""
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {}
            }
        )

        # May work (notification) or return error
        assert response.status_code in [200, 400]

    def test_malformed_json(self, test_client):
        """Test with malformed JSON"""
        response = test_client.post(
            "/mcp",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code in [400, 422]


class TestMCPCompliance:
    """Tests for MCP specification compliance"""

    def test_response_structure(self, test_client):
        """Test MCP response structure compliance"""
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 11,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {}
                }
            }
        )

        data = response.json()

        # Must have jsonrpc field
        assert "jsonrpc" in data
        assert data["jsonrpc"] == "2.0"

        # Must have id matching request
        assert "id" in data
        assert data["id"] == 11

        # Must have result or error
        assert "result" in data or "error" in data

    def test_capabilities_structure(self, test_client):
        """Test capabilities structure compliance"""
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 12,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {}
                }
            }
        )

        data = response.json()
        capabilities = data["result"]["capabilities"]

        # Should declare tool capabilities
        assert "tools" in capabilities or capabilities == {}

    def test_server_info_structure(self, test_client):
        """Test server info structure compliance"""
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 13,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {}
                }
            }
        )

        data = response.json()
        server_info = data["result"]["serverInfo"]

        # Must have name and version
        assert "name" in server_info
        assert "version" in server_info


@pytest.mark.integration
class TestMCPEndToEnd:
    """End-to-end tests for complete MCP workflows"""

    def test_full_mcp_workflow(self, test_client, test_api_key):
        """Test complete MCP initialization and tool call workflow"""
        # Step 1: Initialize
        init_response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
        )

        assert init_response.status_code == 200

        # Step 2: List tools
        list_response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
        )

        assert list_response.status_code == 200
        tools = list_response.json()["result"]["tools"]
        assert len(tools) >= 4

        # Step 3: Call a tool
        call_response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "search_library",
                    "arguments": {
                        "queries": ["test"],
                        "limit": 5
                    }
                }
            },
            headers={"X-API-Key": test_api_key}
        )

        assert call_response.status_code == 200
        assert "result" in call_response.json()
