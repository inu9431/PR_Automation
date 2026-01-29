.PHONY: help dev up down logs shell test clean lint format

help:
	@echo "Available commands:"
	@echo "  make dev     - Start development server"
	@echo "  make up      - Start containers in background"
	@echo "  make down    - Stop containers"
	@echo "  make logs    - View logs"
	@echo "  make shell   - Access container shell"
	@echo "  make test    - Run tests with coverage"
	@echo "  make lint    - Run code quality checks"
	@echo "  make format  - Format code"
	@echo "  make clean   - Clean cache files"

dev:
	docker compose up

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f web

shell:
	docker compose exec web /bin/bash

test:
	docker compose exec web uv run pytest -v --cov=app --cov-report=term

lint:
	docker compose exec web uv run black --check .
	docker compose exec web uv run isort --check-only .

format:
	docker compose exec web uv run black .
	docker compose exec web uv run isort .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -f .coverage
