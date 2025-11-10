# BookWise Test Suite

Comprehensive test suite for the BookWise project, covering all calibrebrowser functionality and core modules.

## Overview

The test suite is organized by module and includes:
- **Unit tests**: Test individual functions and methods
- **Integration tests**: Test complete workflows
- **Fixtures**: Shared test data and mock objects

## Structure

```
src/tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── README.md                      # This file
├── calibrebrowser/                # Calibrebrowser tests
│   ├── __init__.py
│   ├── test_analyze_calibre_awards.py
│   ├── test_analyze_calibre_coverage.py
│   ├── test_find_unprocessed_books.py
│   ├── test_generate_calibre_imports.py
│   └── test_analyze_library.py
└── fixtures/                      # Test data files
```

## Installation

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

## Running Tests

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src --cov-report=html
```

### Run Specific Test Files

```bash
# Test specific module
pytest src/tests/calibrebrowser/test_analyze_calibre_awards.py

# Test specific class
pytest src/tests/calibrebrowser/test_analyze_calibre_awards.py::TestNormalization

# Test specific function
pytest src/tests/calibrebrowser/test_analyze_calibre_awards.py::TestNormalization::test_normalize_string_basic
```

### Run Tests by Pattern

```bash
# Run tests matching pattern
pytest -k "awards"

# Run tests NOT matching pattern
pytest -k "not integration"
```

### Run Tests in Parallel

```bash
# Run tests using multiple CPU cores
pytest -n auto
```

## Test Coverage

Generate coverage reports:

```bash
# Terminal report
pytest --cov=src

# HTML report (opens in browser)
pytest --cov=src --cov-report=html
open htmlcov/index.html

# XML report (for CI/CD)
pytest --cov=src --cov-report=xml
```

## Writing Tests

### Test Structure

Follow this structure for new tests:

```python
"""
Tests for module_name.py
Brief description of what is being tested
"""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock
import sys

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.module import function_to_test


class TestFunctionality:
    """Test specific functionality"""

    def test_basic_case(self):
        """Test basic functionality"""
        result = function_to_test()
        assert result is not None

    def test_edge_case(self):
        """Test edge case"""
        result = function_to_test(edge_input)
        assert result == expected
```

### Using Fixtures

Use shared fixtures from `conftest.py`:

```python
def test_with_mock_db(mock_calibre_db):
    """Test using mock Calibre database"""
    # mock_calibre_db is a temporary SQLite database
    conn = sqlite3.connect(str(mock_calibre_db))
    # ... test code
```

### Mocking Settings

Mock settings to isolate tests:

```python
@patch('src.calibrebrowser.module.settings')
def test_function(mock_settings_obj, mock_settings):
    """Test with mocked settings"""
    mock_settings_obj.CALIBRE_DB_PATH = mock_settings.CALIBRE_DB_PATH
    # ... test code
```

## Available Fixtures

### Database Fixtures
- `mock_calibre_db`: SQLite database with sample Calibre data
- `sample_scored_books_csv`: CSV file with scored books
- `sample_award_files`: JSON award files

### Path Fixtures
- `temp_dir`: Temporary directory for test outputs
- `mock_settings`: Complete mocked settings object

### Data Fixtures
- `mock_title_variants`: Sample title variants
- `sample_processed_books_csv`: Processed books CSV

## Test Categories

### Unit Tests
Test individual functions in isolation:
- String normalization
- Data parsing
- Score calculation
- Tag generation

### Integration Tests
Test complete workflows:
- Full analysis runs
- File generation
- Database queries
- Output validation

### CLI Tests
Test command-line interface:
- Argument parsing
- Menu navigation
- Error handling
- Output formatting

## Continuous Integration

Tests are designed to run in CI/CD environments:

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Best Practices

### 1. Test Independence
- Each test should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order

### 2. Descriptive Names
- Use descriptive test names: `test_normalize_removes_articles`
- Use descriptive docstrings
- Group related tests in classes

### 3. Arrange-Act-Assert
```python
def test_something():
    # Arrange
    input_data = prepare_data()

    # Act
    result = function_to_test(input_data)

    # Assert
    assert result == expected
```

### 4. Mock External Dependencies
- Mock file I/O
- Mock database connections
- Mock API calls
- Mock environment variables

### 5. Test Edge Cases
- Empty inputs
- None values
- Invalid data
- Boundary conditions

## Debugging Tests

### Run with Debug Output
```bash
# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Enter debugger on failure
pytest --pdb
```

### Using IPython Debugger
```python
def test_something():
    import ipdb; ipdb.set_trace()
    # ... test code
```

## Common Issues

### Import Errors
If you get import errors, ensure:
1. You're running from project root
2. `src` is in Python path
3. All `__init__.py` files exist

### Database Lock Errors
If SQLite database is locked:
1. Close all connections in tests
2. Use separate databases per test
3. Use `tmp_path` fixture for isolation

### Fixture Scope
Control fixture lifespan:
```python
@pytest.fixture(scope="function")  # Default, runs per test
@pytest.fixture(scope="class")     # Runs per test class
@pytest.fixture(scope="module")    # Runs per module
@pytest.fixture(scope="session")   # Runs once per session
```

## Contributing

When adding new functionality:
1. Write tests first (TDD)
2. Ensure tests pass: `pytest`
3. Check coverage: `pytest --cov=src`
4. Format code: `black src/tests/`
5. Sort imports: `isort src/tests/`
6. Check linting: `flake8 src/tests/`

## Test Metrics

Target metrics:
- **Coverage**: > 80% overall
- **Execution time**: < 30 seconds for full suite
- **Success rate**: 100% on main branch

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
