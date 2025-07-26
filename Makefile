# MageMines Development Makefile
# Supports both Windows and Unix-like systems

# Detect OS for cross-platform commands
ifeq ($(OS),Windows_NT)
    PYTHON := python
    RM := del /F /Q
    RMDIR := rmdir /S /Q
    SEP := \\
    NULL := nul
    VENV_ACTIVATE := .venv\Scripts\activate
else
    PYTHON := python3
    RM := rm -f
    RMDIR := rm -rf
    SEP := /
    NULL := /dev/null
    VENV_ACTIVATE := .venv/bin/activate
endif

# Project variables
PROJECT_NAME := magemines
SRC_DIR := src
TEST_DIR := tests
COVERAGE_DIR := htmlcov

# Python tools
UV := uv
PYTEST := $(UV) run pytest
BLACK := $(UV) run black
ISORT := $(UV) run isort
FLAKE8 := $(UV) run flake8
MYPY := $(UV) run mypy

# Default target
.DEFAULT_GOAL := help

# Phony targets
.PHONY: help setup install clean run run-debug test test-unit test-integration \
        test-watch test-failed benchmark coverage format lint check ci \
        profile docs serve-docs

## Help
help: ## Show this help message
	@echo "MageMines Development Commands"
	@echo "=============================="
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  setup          - Complete project setup (install uv, dependencies, git hooks)"
	@echo "  install        - Install/update dependencies with uv"
	@echo "  clean          - Remove all generated files and caches"
	@echo ""
	@echo "Running the Game:"
	@echo "  run            - Run the game normally"
	@echo "  run-debug      - Run with debug logging enabled"
	@echo "  run-demo       - Run in demo mode (AI plays automatically)"
	@echo ""
	@echo "Testing:"
	@echo "  test           - Run all tests with coverage"
	@echo "  test-unit      - Run only unit tests"
	@echo "  test-integration - Run only integration tests"
	@echo "  test-watch     - Run tests on file changes"
	@echo "  test-failed    - Re-run only failed tests"
	@echo "  benchmark      - Run performance benchmarks"
	@echo "  coverage       - Generate HTML coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  format         - Auto-format code with black and isort"
	@echo "  lint           - Check code with flake8 and mypy"
	@echo "  check          - Run format, lint, and tests"
	@echo ""
	@echo "Development:"
	@echo "  profile        - Profile game performance"
	@echo "  docs           - Generate documentation"
	@echo "  ci             - Run full CI pipeline locally"

## Setup & Installation
setup: ## Complete project setup
	@echo "Setting up MageMines development environment..."
	@echo "=============================================="
	
	# Check if uv is installed
	@which $(UV) > $(NULL) 2>&1 || (echo "Installing uv..." && curl -LsSf https://astral.sh/uv/install.sh | sh)
	
	# Create virtual environment and install dependencies
	$(UV) venv
	$(UV) pip install -r requirements.txt
	$(UV) pip install -e .
	
	# Set up pre-commit hooks
	@echo "Setting up git hooks..."
	$(UV) pip install pre-commit
	$(UV) run pre-commit install
	
	# Create .env from sample if it doesn't exist
	@if not exist .env (copy .env.sample .env && echo "Created .env file - please add your API keys")
	
	@echo ""
	@echo "Setup complete! Run 'make test' to verify everything is working."

install: ## Install/update dependencies
	$(UV) pip sync requirements.txt
	$(UV) pip install -e .

clean: ## Remove all generated files
	@echo "Cleaning project..."
	$(RM) -rf $(COVERAGE_DIR)
	$(RM) -rf .pytest_cache
	$(RM) -rf .mypy_cache
	$(RM) -rf dist
	$(RM) -rf build
	$(RM) -rf *.egg-info
	find . -type d -name __pycache__ -exec $(RMDIR) {} + 2>$(NULL) || true
	find . -type f -name "*.pyc" -exec $(RM) {} + 2>$(NULL) || true
	find . -type f -name "*.pyo" -exec $(RM) {} + 2>$(NULL) || true
	@echo "Clean complete!"

## Running the Game
run: ## Run the game
ifeq ($(OS),Windows_NT)
	@chcp 65001 > nul && $(UV) run python -m $(PROJECT_NAME)
else
	$(UV) run python -m $(PROJECT_NAME)
endif

run-debug: ## Run with debug logging
	DEBUG_MODE=true $(UV) run python -m $(PROJECT_NAME)

run-demo: ## Run in demo mode (AI plays)
	AUTO_ADVANCE_TURNS=true $(UV) run python -m $(PROJECT_NAME)

## Testing
test: ## Run all tests with coverage
	$(PYTEST) -v --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html

test-unit: ## Run only unit tests
	$(PYTEST) -v -m "not integration and not slow" $(TEST_DIR)/unit/

test-integration: ## Run only integration tests
	$(PYTEST) -v -m integration $(TEST_DIR)/integration/

test-watch: ## Run tests on file changes
	$(UV) run ptw -- -v --testmon

test-failed: ## Re-run only failed tests
	$(PYTEST) -v --lf

benchmark: ## Run performance benchmarks
	$(PYTEST) -v -m benchmark --benchmark-only

coverage: test ## Generate HTML coverage report
	@echo "Opening coverage report..."
	@python -m webbrowser htmlcov/index.html

## Code Quality
format: ## Auto-format code
	@echo "Formatting code..."
	$(BLACK) $(SRC_DIR) $(TEST_DIR)
	$(ISORT) $(SRC_DIR) $(TEST_DIR)
	@echo "Format complete!"

lint: ## Check code quality
	@echo "Linting code..."
	$(FLAKE8) $(SRC_DIR) $(TEST_DIR)
	$(MYPY) $(SRC_DIR)
	@echo "Lint complete!"

check: format lint test ## Run all checks

## Development Tools
profile: ## Profile game performance
	$(UV) run python -m cProfile -o profile.stats -m $(PROJECT_NAME)
	$(UV) run python -c "import pstats; p = pstats.Stats('profile.stats'); p.strip_dirs().sort_stats('cumulative').print_stats(20)"

docs: ## Generate documentation
	$(UV) run sphinx-build -b html docs docs/_build/html

serve-docs: docs ## Serve documentation locally
	@python -m webbrowser docs/_build/html/index.html

## CI/CD
ci: ## Run full CI pipeline
	@echo "Running CI pipeline..."
	@echo "====================="
	$(MAKE) clean
	$(MAKE) install
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) test
	@echo "CI pipeline complete!"

# Advanced targets for development
.PHONY: repl shell update-deps init-db reset-db

repl: ## Start Python REPL with game context
	$(UV) run python -i -c "from src.magemines import *; print('MageMines REPL - Game modules loaded')"

shell: ## Start IPython shell with game context
	$(UV) run ipython -i -c "from src.magemines import *; print('MageMines IPython - Game modules loaded')"

update-deps: ## Update all dependencies to latest versions
	$(UV) pip compile requirements.in -o requirements.txt --upgrade

# Windows-specific helpers
ifeq ($(OS),Windows_NT)
fix-line-endings: ## Fix line endings for Windows
	@echo "Fixing line endings..."
	@for /r %%f in (*.py) do dos2unix "%%f" 2>nul || unix2dos "%%f"
endif