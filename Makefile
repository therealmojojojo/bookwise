# BookWise Makefile
# Convenient commands for testing, linting, and development

.PHONY: help test test-verbose test-coverage test-fast clean install install-dev lint format

help:
	@echo "BookWise Development Commands"
	@echo "============================"
	@echo ""
	@echo "Testing:"
	@echo "  make test            - Run all tests"
	@echo "  make test-verbose    - Run tests with verbose output"
	@echo "  make test-coverage   - Run tests with coverage report"
	@echo "  make test-fast       - Run tests in parallel"
	@echo "  make test-watch      - Run tests on file changes"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint            - Run linters (flake8, pylint)"
	@echo "  make format          - Format code (black, isort)"
	@echo "  make format-check    - Check code formatting"
	@echo "  make type-check      - Run type checker (mypy)"
	@echo ""
	@echo "Installation:"
	@echo "  make install         - Install production dependencies"
	@echo "  make install-dev     - Install dev dependencies"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean           - Remove generated files"
	@echo "  make clean-test      - Remove test cache and coverage"
	@echo "  make clean-all       - Remove all generated files"

# Testing commands
test:
	pytest

test-verbose:
	pytest -v

test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

test-fast:
	pytest -n auto

test-watch:
	pytest-watch

test-specific:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-specific FILE=path/to/test_file.py"; \
		exit 1; \
	fi
	pytest $(FILE) -v

# Code quality commands
lint:
	@echo "Running flake8..."
	flake8 src --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 src --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics
	@echo ""
	@echo "Running pylint..."
	pylint src/calibrebrowser --exit-zero

format:
	@echo "Formatting with black..."
	black src/
	@echo "Sorting imports with isort..."
	isort src/

format-check:
	@echo "Checking format with black..."
	black --check src/
	@echo "Checking imports with isort..."
	isort --check-only src/

type-check:
	mypy src/calibrebrowser/ --ignore-missing-imports

# Installation commands
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

# Cleanup commands
clean-pyc:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

clean-test:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -f coverage.xml

clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

clean: clean-pyc clean-test

clean-all: clean clean-build
	@echo "All generated files removed"

# Run analysis tools
analyze-awards:
	python src/calibrebrowser/analyze_library.py --awards

analyze-coverage:
	python src/calibrebrowser/analyze_library.py --coverage

analyze-imports:
	python src/calibrebrowser/analyze_library.py --imports

analyze-all:
	python src/calibrebrowser/analyze_library.py --all

# Development helpers
check: format-check lint type-check test
	@echo ""
	@echo "All checks passed! ✓"

ci: install-dev check test-coverage
	@echo ""
	@echo "CI checks completed! ✓"
