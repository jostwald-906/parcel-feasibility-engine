.PHONY: help install dev test lint format docker-up docker-down migrate

help:
	@echo "Available targets:"
	@echo "  install     - Install dependencies"
	@echo "  dev         - Run development server"
	@echo "  test        - Run tests with coverage"
	@echo "  lint        - Run linters (ruff, mypy)"
	@echo "  format      - Format code with black"
	@echo "  docker-up   - Start Docker services"
	@echo "  docker-down - Stop Docker services"
	@echo "  migrate     - Run database migrations"

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest --cov=app --cov-report=html --cov-report=term-missing

lint:
	ruff check app tests
	mypy app

format:
	black app tests
	ruff check --fix app tests

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

migrate:
	alembic upgrade head

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov
