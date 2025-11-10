#!/bin/bash
#
# Quick test runner for BookWise Librarian tests
# Runs different test suites with various options
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== BookWise Librarian Test Runner ==="
echo

# Parse command line arguments
TEST_TYPE="${1:-all}"
VERBOSE="${2:-}"

case $TEST_TYPE in
    "all")
        echo -e "${BLUE}Running all tests...${NC}"
        pytest src/tests/librarian/ -v $VERBOSE
        ;;

    "api")
        echo -e "${BLUE}Running API endpoint tests...${NC}"
        pytest src/tests/librarian/test_api_endpoints.py -v $VERBOSE
        ;;

    "mcp")
        echo -e "${BLUE}Running MCP protocol tests...${NC}"
        pytest src/tests/librarian/test_mcp_protocol.py -v $VERBOSE
        ;;

    "services")
        echo -e "${BLUE}Running service layer tests...${NC}"
        pytest src/tests/librarian/test_services.py -v $VERBOSE
        ;;

    "integration")
        echo -e "${BLUE}Running integration tests only...${NC}"
        pytest src/tests/librarian/ -m integration -v $VERBOSE
        ;;

    "coverage")
        echo -e "${BLUE}Running tests with coverage report...${NC}"
        pytest src/tests/librarian/ --cov=src/librarian --cov-report=html --cov-report=term
        echo
        echo -e "${GREEN}Coverage report generated: htmlcov/index.html${NC}"
        ;;

    "quick")
        echo -e "${BLUE}Running quick smoke tests...${NC}"
        pytest src/tests/librarian/ -v --tb=short -x
        ;;

    "inspector")
        echo -e "${BLUE}Launching MCP Inspector...${NC}"
        echo "Make sure the server is running first!"
        echo
        ./src/tests/librarian/test_with_mcp_inspector.sh
        ;;

    *)
        echo "Usage: $0 [test_type] [verbose_flag]"
        echo
        echo "Test types:"
        echo "  all         - Run all tests (default)"
        echo "  api         - Run API endpoint tests only"
        echo "  mcp         - Run MCP protocol tests only"
        echo "  services    - Run service layer tests only"
        echo "  integration - Run integration tests only"
        echo "  coverage    - Run with coverage report"
        echo "  quick       - Quick smoke test (stop on first failure)"
        echo "  inspector   - Launch MCP Inspector (interactive)"
        echo
        echo "Verbose flag:"
        echo "  -v          - Verbose output"
        echo "  -vv         - Very verbose output"
        echo "  -s          - Show print statements"
        echo
        echo "Examples:"
        echo "  $0 all -v           # All tests, verbose"
        echo "  $0 api -vv          # API tests, very verbose"
        echo "  $0 coverage         # Generate coverage report"
        echo "  $0 quick -s         # Quick test with print output"
        exit 1
        ;;
esac

echo
echo -e "${GREEN}✓ Tests completed${NC}"
