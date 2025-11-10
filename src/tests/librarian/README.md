# BookWise Librarian API Tests

Comprehensive test suite for the BookWise Librarian API, including REST endpoints, MCP protocol compliance, and service layer tests.

## Test Structure

```
src/tests/librarian/
├── conftest.py                    # Test fixtures and mocks
├── test_api_endpoints.py          # REST API endpoint tests
├── test_mcp_protocol.py           # MCP protocol compliance tests
├── test_services.py               # Service layer unit tests
├── test_with_mcp_inspector.sh     # Interactive MCP testing with Inspector
└── README.md                      # This file
```

## Test Coverage

### 1. API Endpoint Tests (`test_api_endpoints.py`)

Tests all REST API endpoints with various scenarios:

**Search Library**
- ✅ Successful search with quality filtering
- ✅ Search without filters
- ✅ Empty query validation
- ✅ Invalid limit validation
- ✅ Authentication (when enabled)

**Get Book Details**
- ✅ Single and multiple book retrieval
- ✅ Non-existent book handling
- ✅ Empty list validation
- ✅ Too many IDs validation

**Get Top Quality Books**
- ✅ Browse with quality threshold
- ✅ Genre filtering
- ✅ High threshold edge cases
- ✅ Invalid quality validation

**Send Book to E-Reader**
- ✅ Successful export
- ✅ Device name handling
- ✅ Multiple format support (EPUB, MOBI, AZW3, PDF)
- ✅ Invalid format validation
- ✅ Non-existent book handling

**Integration Workflows**
- ✅ Search → Get Details workflow
- ✅ Top Books → Export workflow

### 2. MCP Protocol Tests (`test_mcp_protocol.py`)

Tests MCP 2025-06-18 specification compliance:

**MCP Root Endpoint**
- ✅ GET request handling
- ✅ OPTIONS for CORS
- ✅ Protocol information

**Initialize Method**
- ✅ Successful initialization
- ✅ Client info handling
- ✅ Protocol version validation
- ✅ Capabilities declaration
- ✅ Server info structure

**Tools List Method**
- ✅ Tool listing
- ✅ Tool structure validation
- ✅ All 4 tools present
- ✅ Input schema validation

**Tools Call Method**
- ✅ search_library tool
- ✅ get_book_details tool
- ✅ get_top_quality_books tool
- ✅ send_book_to_ereader tool
- ✅ Non-existent tool handling
- ✅ Invalid arguments handling

**Error Handling**
- ✅ Invalid method handling
- ✅ Missing fields validation
- ✅ Malformed JSON handling

**Compliance**
- ✅ JSON-RPC 2.0 structure
- ✅ Response format compliance
- ✅ Capabilities structure
- ✅ Server info structure

**End-to-End**
- ✅ Initialize → List Tools → Call Tool workflow

### 3. Service Layer Tests (`test_services.py`)

Unit tests for core services:

**VectorSearchService**
- ✅ Successful vector search
- ✅ Multiple query handling
- ✅ Quality filtering
- ✅ Book retrieval by ID
- ✅ Embedding generation

**CalibreService**
- ✅ Metadata retrieval
- ✅ Multiple books handling
- ✅ Non-existent book handling
- ✅ Format listing
- ✅ Tag retrieval

**DeliveryService**
- ✅ Book export success
- ✅ Device name handling
- ✅ Multiple formats
- ✅ Invalid folder handling

**Integration**
- ✅ Search → Metadata workflow
- ✅ Metadata → Export workflow

## Running Tests

### Run All Tests

```bash
# From project root
pytest src/tests/librarian/ -v

# With coverage
pytest src/tests/librarian/ --cov=src/librarian --cov-report=html
```

### Run Specific Test Files

```bash
# API endpoint tests only
pytest src/tests/librarian/test_api_endpoints.py -v

# MCP protocol tests only
pytest src/tests/librarian/test_mcp_protocol.py -v

# Service tests only
pytest src/tests/librarian/test_services.py -v
```

### Run Specific Test Classes

```bash
# Test search endpoint only
pytest src/tests/librarian/test_api_endpoints.py::TestSearchLibrary -v

# Test MCP initialize only
pytest src/tests/librarian/test_mcp_protocol.py::TestMCPInitialize -v
```

### Run Integration Tests Only

```bash
# All integration tests
pytest src/tests/librarian/ -m integration -v
```

### Run with MCP Inspector (Interactive)

```bash
# Start the server first
cd src/librarian/deployment
./dev-start.sh

# In another terminal, run inspector
cd src/tests/librarian
./test_with_mcp_inspector.sh
```

This will launch the MCP Inspector web interface where you can:
1. Connect to your local server
2. View available tools
3. Execute tool calls interactively
4. Inspect request/response structures
5. Test MCP protocol compliance

## Test Fixtures

The test suite uses the following fixtures (defined in `conftest.py`):

### Database Fixtures

**`temp_chromadb`** - Temporary ChromaDB with sample embeddings
- 3 test books with embeddings
- Quality scores: 85, 75, 65
- Themes and descriptions

**`temp_calibre_db`** - Temporary Calibre SQLite database
- 2 test books with metadata
- Authors, tags, formats
- Minimal but complete schema

### Mock Fixtures

**`mock_openai_embeddings`** - Mocks OpenAI API
- Returns fixed 3072-dimensional embeddings
- Avoids real API calls in tests

**`mock_calibredb`** - Mocks calibredb CLI
- Simulates successful exports
- Prevents actual file operations

**`mock_settings`** - Complete settings mock
- Points to temp databases
- Safe test configuration

### Utility Fixtures

**`test_api_key`** - Test API key for authentication
**`test_client`** - FastAPI TestClient instance

## Test Configuration

Tests require these dependencies:

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock fastapi[test] chromadb openai
```

### Environment Variables for Tests

Tests use mocked values by default, but you can override:

```bash
# Optional: Use real databases for integration testing
export TEST_CALIBRE_DB_PATH=/path/to/real/metadata.db
export TEST_CHROMADB_PATH=/path/to/real/vectors

# Run tests with real data
pytest src/tests/librarian/ -v
```

## Writing New Tests

### Adding API Endpoint Tests

```python
class TestNewEndpoint:
    """Tests for new endpoint"""

    def test_success_case(self, test_client, test_api_key):
        response = test_client.post(
            "/api/v1/new_endpoint",
            json={"param": "value"},
            headers={"X-API-Key": test_api_key}
        )

        assert response.status_code == 200
        data = response.json()
        assert "expected_field" in data
```

### Adding MCP Protocol Tests

```python
def test_new_mcp_method(self, test_client):
    response = test_client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "new/method",
            "params": {}
        }
    )

    assert response.status_code == 200
    assert response.json()["jsonrpc"] == "2.0"
```

### Adding Service Tests

```python
def test_new_service_method(self, temp_calibre_db):
    from src.librarian.services.calibre_db import CalibreService

    service = CalibreService(str(temp_calibre_db))
    result = service.new_method()

    assert result is not None
```

## Continuous Integration

Tests are designed to run in CI environments:

```yaml
# .github/workflows/test-librarian.yml
name: Test Librarian API

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest src/tests/librarian/ --cov=src/librarian
```

## Debugging Failed Tests

### View Detailed Output

```bash
# Show print statements
pytest src/tests/librarian/ -v -s

# Show detailed tracebacks
pytest src/tests/librarian/ -v --tb=long

# Stop on first failure
pytest src/tests/librarian/ -x
```

### Run Specific Test with Debug

```bash
# Single test with maximum verbosity
pytest src/tests/librarian/test_api_endpoints.py::TestSearchLibrary::test_search_library_success -vvs
```

### Check Test Coverage

```bash
# Generate coverage report
pytest src/tests/librarian/ --cov=src/librarian --cov-report=html

# Open in browser
open htmlcov/index.html
```

## Test Performance

Current test suite performance:

- **Total Tests**: 60+ tests
- **Execution Time**: < 5 seconds
- **Coverage**: 80%+ (services and endpoints)

## Known Limitations

1. **Authentication**: Tests currently run with auth disabled (see `routes.py`)
   - Re-enable auth in production: `router = APIRouter(dependencies=[Depends(verify_api_key)])`

2. **Real Embeddings**: Tests use mock embeddings
   - For integration tests with real OpenAI, set `OPENAI_API_KEY` env var

3. **Real Calibre DB**: Tests use minimal SQLite schema
   - Some edge cases may not match production Calibre schema

## MCP Inspector Testing

The MCP Inspector provides visual, interactive testing:

### Setup

```bash
# Install Node.js if needed
brew install node

# Inspector is installed via npx (no manual install needed)
```

### Usage

```bash
# Start server
cd src/librarian/deployment
./dev-start.sh

# Run inspector (in another terminal)
cd src/tests/librarian
./test_with_mcp_inspector.sh
```

### What to Test

1. **Initialize** - Verify server responds correctly
2. **List Tools** - Confirm 4 tools are available
3. **Tool Schemas** - Validate input schemas
4. **Call Tools** - Test each tool with various inputs
5. **Error Cases** - Try invalid inputs and missing parameters

### Inspector Features

- Real-time request/response inspection
- Schema validation
- Interactive tool execution
- Error visualization
- Protocol compliance checking

## Contributing

When adding new features to the Librarian API:

1. Write tests first (TDD approach)
2. Cover success cases and error cases
3. Test edge cases and validation
4. Update this README with new test coverage
5. Ensure all tests pass before submitting PR

## Questions?

See main project documentation:
- [Librarian README](../../librarian/README.md)
- [Main Project README](../../../README.md)
