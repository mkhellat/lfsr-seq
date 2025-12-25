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

.PHONY: help venv install install-dev test test-cov lint format type-check clean distclean check-env smoke-test build uninstall clean-venv docs docs-clean docs-live

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
	@echo "  make format-check  - Check code formatting without modifying"
	@echo "  make type-check    - Run type checking with mypy"
	@echo "  make check-env     - Check environment setup"
	@echo "  make smoke-test    - Run smoke tests"
	@echo "  make build         - Build distribution packages"
	@echo "  make clean         - Remove build artifacts"
	@echo "  make clean-venv    - Remove virtual environment"
	@echo "  make distclean     - Remove all generated files (including venv)"
	@echo "  make uninstall     - Uninstall the package"
	@echo "  make docs          - Build Sphinx documentation"
	@echo "  make docs-clean    - Clean documentation build artifacts"
	@echo "  make docs-live     - Start live documentation server (auto-reload)"
	@echo ""

# Virtual environment target
# This target ensures venv exists but doesn't fail if it already exists
venv:
	@if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv .venv; \
		echo "  ✓ Virtual environment created at .venv"; \
	fi

# Helper to ensure venv exists and get Python/pip paths
VENV_PYTHON := $(if $(wildcard .venv),.venv/bin/python3,python3)
VENV_PIP := $(if $(wildcard .venv),.venv/bin/pip,python3 -m pip)

# Installation targets
install: venv
	@echo "Installing lfsr-seq in development mode..."
	@if [ -d ".venv" ]; then \
		echo "  Using virtual environment at .venv"; \
		.venv/bin/pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || true; \
		.venv/bin/pip install -e .; \
	else \
		echo "  ✗ ERROR: Virtual environment not found"; \
		echo "  This should not happen - venv target should have created it"; \
		exit 1; \
	fi

install-dev: venv
	@echo "Installing lfsr-seq with development dependencies..."
	@if [ -d ".venv" ]; then \
		echo "  Using virtual environment at .venv"; \
		.venv/bin/pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || true; \
		.venv/bin/pip install -e ".[dev]"; \
	else \
		echo "  ✗ ERROR: Virtual environment not found"; \
		echo "  This should not happen - venv target should have created it"; \
		exit 1; \
	fi

# Testing targets
test: venv
	@echo "Running tests..."
	@if [ -d ".venv" ]; then \
		.venv/bin/python -m pytest tests/ -v; \
	else \
		python3 -m pytest tests/ -v; \
	fi

test-cov: venv
	@echo "Running tests with coverage..."
	@if [ -d ".venv" ]; then \
		.venv/bin/python -m pytest tests/ --cov=lfsr --cov-report=html --cov-report=term; \
	else \
		python3 -m pytest tests/ --cov=lfsr --cov-report=html --cov-report=term; \
	fi
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

# Code quality targets
lint: venv
	@echo "Running linting checks..."
	@if [ -d ".venv" ]; then \
		.venv/bin/python -m ruff check .; \
	else \
		python3 -m ruff check .; \
	fi

format: venv
	@echo "Formatting code with black..."
	@if [ -d ".venv" ]; then \
		.venv/bin/python -m black .; \
	else \
		python3 -m black .; \
	fi

format-check: venv
	@echo "Checking code formatting..."
	@if [ -d ".venv" ]; then \
		.venv/bin/python -m black --check .; \
	else \
		python3 -m black --check .; \
	fi

type-check: venv
	@echo "Running type checking..."
	@if [ -d ".venv" ]; then \
		.venv/bin/python -m mypy . || true; \
	else \
		python3 -m mypy . || true; \
	fi

# Environment and smoke tests
check-env:
	@echo "Checking environment..."
	@./scripts/check-environment.sh

smoke-test:
	@echo "Running smoke tests..."
	@./scripts/smoke-test.sh

# Build targets
build: venv
	@echo "Building distribution packages..."
	@if [ -d ".venv" ]; then \
		.venv/bin/pip install --upgrade build >/dev/null 2>&1 || true; \
		.venv/bin/python -m build; \
	else \
		python3 -m pip install --upgrade build >/dev/null 2>&1 || true; \
		python3 -m build; \
	fi
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

distclean: clean clean-venv
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

# Uninstall target
uninstall:
	@echo "Uninstalling lfsr-seq..."
	@if [ -d ".venv" ]; then \
		echo "  Using virtual environment at .venv"; \
		if .venv/bin/pip show lfsr-seq >/dev/null 2>&1; then \
			.venv/bin/pip uninstall -y lfsr-seq || true; \
			echo "  ✓ Package uninstalled from virtual environment"; \
		else \
			echo "  Package not found in virtual environment"; \
		fi; \
		rm -rf *.egg-info 2>/dev/null || true; \
		rm -rf .eggs 2>/dev/null || true; \
		echo "  ✓ Build metadata cleaned"; \
	else \
		echo "  Checking system-wide installation..."; \
		if python3 -m pip show lfsr-seq >/dev/null 2>&1; then \
			echo "  WARNING: Package found in system Python"; \
			echo "  To uninstall system-wide, run: python3 -m pip uninstall lfsr-seq"; \
			echo "  Or activate your virtual environment first"; \
		else \
			echo "  Package not found in system Python"; \
		fi; \
		rm -rf *.egg-info 2>/dev/null || true; \
		rm -rf .eggs 2>/dev/null || true; \
		echo "  ✓ Build metadata cleaned"; \
	fi
	@echo "Uninstall complete"

# Quick development workflow
dev-setup: venv check-env install-dev
	@echo ""
	@echo "Development environment setup complete!"
	@echo ""
	@echo "Virtual environment is ready at .venv"
	@echo "To activate: source .venv/bin/activate"
	@echo ""
	@echo "Run tests: make test"
	@echo "Format code: make format"
	@echo "Run linting: make lint"

# Documentation targets
docs: venv
	@echo "Building Sphinx documentation..."
	@if [ -d ".venv" ]; then \
		.venv/bin/pip install sphinx sphinx-rtd-theme >/dev/null 2>&1 || true; \
		cd docs && ../.venv/bin/sphinx-build -b html . _build/html; \
		echo ""; \
		echo "Documentation built in docs/_build/html/"; \
		echo "Open docs/_build/html/index.html in your browser"; \
	else \
		python3 -m pip install sphinx sphinx-rtd-theme >/dev/null 2>&1 || true; \
		cd docs && python3 -m sphinx -b html . _build/html; \
		echo ""; \
		echo "Documentation built in docs/_build/html/"; \
	fi

docs-clean:
	@echo "Cleaning documentation build artifacts..."
	rm -rf docs/_build/
	rm -rf docs/.doctrees/
	@echo "Documentation build artifacts removed"

docs-live: venv
	@echo "Starting live documentation server..."
	@if [ -d ".venv" ]; then \
		.venv/bin/pip install sphinx-autobuild >/dev/null 2>&1 || true; \
		cd docs && ../.venv/bin/sphinx-autobuild . _build/html --host 0.0.0.0 --port 8000; \
	else \
		python3 -m pip install sphinx-autobuild >/dev/null 2>&1 || true; \
		cd docs && python3 -m sphinx_autobuild . _build/html --host 0.0.0.0 --port 8000; \
	fi

# CI/CD helper
ci: lint format-check type-check test
	@echo "All CI checks passed!"

