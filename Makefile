# Makefile for lfsr-seq
#
# Common development tasks for the LFSR sequence analysis tool
#
# Usage:
#   make help          - Show this help message
#   make venv          - Create virtual environment (.venv)
#   make install       - Install package in development mode
#   make install-dev   - Install package with development dependencies
#   make test          - Run tests
#   make test-cov      - Run tests with coverage report
#   make lint          - Run linting checks
#   make format        - Format code with black
#   make type-check    - Run type checking with mypy
#   make clean         - Remove build artifacts
#   make distclean     - Remove all generated files
#   make check-env     - Check environment setup
#   make smoke-test    - Run smoke tests

.PHONY: help venv install install-dev test test-cov lint format type-check clean distclean check-env smoke-test build

# Default target
help:
	@echo "lfsr-seq Development Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make help          - Show this help message"
	@echo "  make venv          - Create virtual environment (.venv)"
	@echo "  make install       - Install package in development mode"
	@echo "  make install-dev   - Install package with development dependencies"
	@echo "  make test          - Run tests with pytest"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo "  make lint          - Run linting checks (ruff)"
	@echo "  make format        - Format code with black"
	@echo "  make format-check   - Check code formatting without modifying"
	@echo "  make type-check    - Run type checking with mypy"
	@echo "  make check-env     - Check environment setup"
	@echo "  make smoke-test    - Run smoke tests"
	@echo "  make build         - Build distribution packages"
	@echo "  make clean         - Remove build artifacts"
	@echo "  make distclean     - Remove all generated files"
	@echo ""

# Virtual environment target
venv:
	@echo "Creating virtual environment..."
	@if [ -d ".venv" ]; then \
		echo "  Virtual environment already exists at .venv"; \
		echo "  Remove it first with: rm -rf .venv"; \
	else \
		python3 -m venv .venv; \
		echo "  ✓ Virtual environment created at .venv"; \
		echo ""; \
		echo "  To activate:"; \
		echo "    source .venv/bin/activate"; \
		echo ""; \
		echo "  Then install dependencies:"; \
		echo "    make install-dev"; \
	fi

# Installation targets
install:
	@echo "Installing lfsr-seq in development mode..."
	@if [ -z "$$VIRTUAL_ENV" ] && [ ! -d ".venv" ]; then \
		echo "  ⚠ WARNING: Not in a virtual environment"; \
		echo "  Consider creating one with: make venv"; \
		echo ""; \
	fi
	python3 -m pip install -e .

install-dev:
	@echo "Installing lfsr-seq with development dependencies..."
	@if [ -z "$$VIRTUAL_ENV" ] && [ ! -d ".venv" ]; then \
		echo "  ⚠ WARNING: Not in a virtual environment"; \
		echo "  Consider creating one with: make venv"; \
		echo ""; \
	fi
	python3 -m pip install -e ".[dev]"

# Testing targets
test:
	@echo "Running tests..."
	python3 -m pytest tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	python3 -m pytest tests/ --cov=lfsr --cov-report=html --cov-report=term
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

# Code quality targets
lint:
	@echo "Running linting checks..."
	python3 -m ruff check .

format:
	@echo "Formatting code with black..."
	python3 -m black .

format-check:
	@echo "Checking code formatting..."
	python3 -m black --check .

type-check:
	@echo "Running type checking..."
	python3 -m mypy . || true

# Environment and smoke tests
check-env:
	@echo "Checking environment..."
	@./scripts/check-environment.sh

smoke-test:
	@echo "Running smoke tests..."
	@./scripts/smoke-test.sh

# Build targets
build:
	@echo "Building distribution packages..."
	python3 -m pip install --upgrade build
	python3 -m build
	@echo ""
	@echo "Distribution packages created in dist/"

# Cleanup targets
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .eggs
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	@echo "Build artifacts removed"

distclean: clean
	@echo "Performing deep clean..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.out" -delete
	@echo "All generated files removed"

clean-venv:
	@echo "Removing virtual environment..."
	@if [ -d ".venv" ]; then \
		rm -rf .venv; \
		echo "  ✓ Virtual environment removed"; \
	else \
		echo "  No virtual environment found"; \
	fi

# Quick development workflow
dev-setup: venv check-env
	@echo ""
	@echo "Activating virtual environment and installing dependencies..."
	@echo "  Run: source .venv/bin/activate"
	@echo "  Then: make install-dev"
	@echo ""
	@if [ -d ".venv" ]; then \
		.venv/bin/pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || true; \
		.venv/bin/pip install -e ".[dev]" >/dev/null 2>&1 || echo "  Install manually: source .venv/bin/activate && make install-dev"; \
		echo "Development environment setup complete!"; \
		echo "Run 'source .venv/bin/activate && make test' to verify installation"; \
	fi

# CI/CD helper
ci: lint format-check type-check test
	@echo "All CI checks passed!"

