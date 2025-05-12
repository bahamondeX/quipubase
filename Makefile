.PHONY: install dev test clean start stop restart lint build

# Python interpreter and Poetry paths
# Poetry python path
PYTHON = $(shell poetry env info -p)/bin/python	
POETRY = poetry
VENV = .venv
PYTHONDONTWRITEBYTECODE = 1
# Application settings
APP_MODULE = main:app
HOST = 0.0.0.0
PORT = 5454
WORKERS = 4

# Install dependencies
install:
	$(POETRY) install

# Install development dependencies
run:
	$(POETRY) install --with dev

# Run tests with pytest
test:
	$(POETRY) run pytest -xvs

# Run specific test file
test-file:
	$(POETRY) run pytest -xvs $(FILE)

# Clean up cache files and temporary data
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".eggs" -exec rm -rf {} +
	find . -type d -name "*.dist-info" -exec rm -rf {} +
	rm -rf dist build .coverage htmlcov

# Start the application with Uvicorn
start:
	$(PYTHON) -m uvicorn $(APP_MODULE) --host $(HOST) --port $(PORT) --workers $(WORKERS) --reload

# Start in development mode
dev:
	$(PYTHON) -m uvicorn $(APP_MODULE) --host $(HOST) --port $(PORT) --workers $(WORKERS) --reload

# Stop the application (find and kill Uvicorn processes)
stop:
	-pkill -f "uvicorn $(APP_MODULE)"

# Restart the application
restart: stop start

# Run linting checks
lint:
	$(POETRY) run ruff check .

# Format code
format:
	$(POETRY) run ruff format .

# Build package distribution
build:
	$(POETRY) build

# Generate documentation
docs:
	$(POETRY) run sphinx-build -b html docs/source docs/build/html

# Export dependencies to requirements.txt
export-requirements:
	$(POETRY) export -f requirements.txt --output requirements.txt --without-hashes

# Default target
all: install test

help:
	@echo "Available targets:"
	@echo "  install               - Install dependencies using Poetry"
	@echo "  dev                   - Install development dependencies"
	@echo "  test                  - Run tests with pytest"
	@echo "  test-file FILE=path   - Run specific test file"
	@echo "  clean                 - Clean up cache files and temporary data"
	@echo "  start                 - Start the application with Uvicorn"
	@echo "  dev           - Start in development mode with auto-reload"
	@echo "  stop                  - Stop the application"
	@echo "  restart               - Restart the application"
	@echo "  lint                  - Run linting checks"
	@echo "  format                - Format code with ruff"
	@echo "  build                 - Build package distribution"
	@echo "  docs                  - Generate documentation"
	@echo "  export-requirements   - Export dependencies to requirements.txt"