.PHONY: help install dev test lint format clean docker deploy health

# Default target
help: ## Show this help message
	@echo "Lunch Voting API - Development Commands"
	@echo "======================================"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development setup
install: ## Install production dependencies
	pip install -e .

dev: ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

# Code quality
format: ## Format code with black and isort
	black app tests
	isort app tests

lint: ## Run linting (flake8, mypy, bandit)
	flake8 app tests --max-line-length=88 --extend-ignore=E203,W503
	mypy app --ignore-missing-imports
	bandit -r app/ -f json

security: ## Run security checks
	bandit -r app/ -ll
	safety check

# Testing
test: ## Run tests with coverage
	pytest --cov=app --cov-report=html --cov-report=term-missing

test-watch: ## Run tests in watch mode
	pytest-watch -- --cov=app

test-quick: ## Run tests without coverage
	pytest -v

# Database
db-upgrade: ## Apply database migrations
	alembic upgrade head

db-downgrade: ## Rollback database migration
	alembic downgrade -1

db-revision: ## Create new migration
	alembic revision --autogenerate -m "$(msg)"

db-reset: ## Reset database (development only)
	alembic downgrade base
	alembic upgrade head

# Application
run: ## Run development server
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run production server
	gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Docker
docker-build: ## Build Docker image
	docker build -t lunch-voting-api .

docker-run: ## Run Docker container
	docker run -p 8000:8000 --env-file .env lunch-voting-api

docker-dev: ## Start development environment with Docker Compose
	docker-compose up --build

docker-prod: ## Start production environment
	docker-compose -f docker-compose.yml up --build

# Deployment
deploy: ## Deploy to production
	./scripts/deploy.sh production

deploy-staging: ## Deploy to staging
	./scripts/deploy.sh staging

health: ## Check application health
	./scripts/health_check.sh

# Utilities
clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/

logs: ## View application logs (Railway)
	railway logs

shell: ## Open Railway shell
	railway shell

status: ## Check deployment status
	railway status

# Requirements
requirements: ## Generate requirements.txt from pyproject.toml
	pip-compile pyproject.toml

upgrade: ## Upgrade all dependencies
	pip-compile --upgrade pyproject.toml

# Pre-commit
pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

install-hooks: ## Install pre-commit hooks
	pre-commit install
