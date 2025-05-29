.PHONY: install run dev test test-file clean start stop restart lint format build requirements deploy docs help all

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────
POETRY = poetry
PYTHON = $(shell $(POETRY) env info -p)/bin/python
APP_NAME = quipubase
APP_MODULE = main:app
HOST = 0.0.0.0
PORT = 8080
WORKERS = 4
VENV = .venv
PYTHONDONTWRITEBYTECODE = 1

UVICORN_OPTS = --host $(HOST) --port $(PORT) --workers $(WORKERS) --reload

# ─────────────────────────────────────────────────────────────
# Dependency Management
# ─────────────────────────────────────────────────────────────
install:
	$(POETRY) install

run:
	$(POETRY) install --with dev

requirements:
	$(POETRY) export --without-hashes > requirements.txt

# ─────────────────────────────────────────────────────────────
# Development
# ─────────────────────────────────────────────────────────────
dev:
	$(PYTHON) -m uvicorn $(APP_MODULE) $(UVICORN_OPTS)

start:
	$(PYTHON) -m uvicorn $(APP_MODULE) $(UVICORN_OPTS)

stop:
	-pkill -f "uvicorn $(APP_MODULE)"

restart: stop start

# ─────────────────────────────────────────────────────────────
# Testing & Quality
# ─────────────────────────────────────────────────────────────
test:
	$(POETRY) run pytest -xvs

test-file:
	$(POETRY) run pytest -xvs $(FILE)

lint:
	$(POETRY) run ruff check .

format:
	$(POETRY) run ruff format .

# ─────────────────────────────────────────────────────────────
# Build & Deployment
# ─────────────────────────────────────────────────────────────
build:
	$(POETRY) build
	docker build -t $(APP_NAME) .

deploy:
	git add 
	docker compose up -d --build --remove-orphans --force-recreate


# ─────────────────────────────────────────────────────────────
# Maintenance
# ─────────────────────────────────────────────────────────────
clean:
	find . -type d \( -name '__pycache__' -o -name '.pytest_cache' -o -name '*.egg-info' -o -name '.eggs' -o -name '*.dist-info' \) -print0 | xargs -0 rm -rf
	find . -type f \( -name "*.pyc" -o -name "*.pyo" -o -name "*.pyd" -o -name ".coverage" \) -delete
	rm -rf dist build htmlcov

# ─────────────────────────────────────────────────────────────
# Documentation
# ─────────────────────────────────────────────────────────────
docs:
	$(POETRY) run mkdocs build


openapi:
	curl http://localhost:8080/openapi.json > openapi.json

# ─────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────
all: install test

help:
	@echo "Available targets:"
	@echo "  install             - Install dependencies using Poetry"
	@echo "  run                 - Install with dev dependencies"
	@echo "  dev                 - Start app in dev mode (hot reload)"
	@echo "  start               - Start the application"
	@echo "  stop                - Stop the application"
	@echo "  restart             - Restart the application"
	@echo "  test                - Run all tests with pytest"
	@echo "  test-file FILE=...  - Run specific test file"
	@echo "  lint                - Run linting checks (ruff)"
	@echo "  format              - Auto-format code (ruff)"
	@echo "  build               - Build Poetry & Docker distributions"
	@echo "  requirements        - Export deps to requirements.txt"
	@echo "  deploy              - Rebuild and redeploy containers"
	@echo "  clean               - Remove cache & build artifacts"
	@echo "  docs                - Build static documentation site"


