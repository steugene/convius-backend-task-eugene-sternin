.PHONY: help install dev test lint format clean docker deploy health

# Default target
help: ## Show this help message
	@echo "🍽️  Lunch Voting API - Development Commands"
	@echo "=========================================="
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make setup    - Complete local development setup (recommended)"
	@echo "  make stop     - Stop all services"
	@echo ""
	@echo "📋 All Commands:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development start with docker compose
start:
	@echo "🚀 Setting up Lunch Voting API development environment..."
	@echo "=================================================="

	# Create .env file if it doesn't exist
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file from env.example..."; \
		cp env.example .env; \
		echo "✅ .env file created! Edit it with your preferences if needed."; \
	else \
		echo "✅ .env file already exists"; \
	fi

	# Install development dependencies
	@echo "📦 Installing dependencies..."
	@pip install -e ".[dev]" > /dev/null 2>&1
	@pre-commit install > /dev/null 2>&1
	@echo "✅ Dependencies installed"

	# Start database services first (without app)
	@echo "🐳 Starting database services (PostgreSQL + Redis)..."
	@docker-compose up -d db redis

	# Wait for database to be ready
	@echo "⏳ Waiting for database to be ready..."
	@timeout=60; \
	while ! docker-compose exec -T db pg_isready -U lunch_voting > /dev/null 2>&1; do \
		if [ $$timeout -le 0 ]; then \
			echo "❌ Database failed to start within 60 seconds"; \
			exit 1; \
		fi; \
		sleep 2; \
		timeout=$$((timeout-2)); \
	done
	@echo "✅ Database is ready!"

	# Start the app container
	@echo "🚀 Starting application container..."
	@docker-compose --profile development up -d app-dev

	# Wait for app container to be ready
	@echo "⏳ Waiting for app container to start..."
	@sleep 5

	# Run database migrations from within the app container
	@echo "🗄️  Running database migrations..."
	@docker-compose exec -T app-dev alembic upgrade head
	@echo "✅ Migrations completed"

	# Wait for app to be ready
	@echo "⏳ Waiting for application to start..."
	@timeout=30; \
	while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do \
		if [ $$timeout -le 0 ]; then \
			echo "⚠️  Application startup timeout, but containers are running"; \
			break; \
		fi; \
		sleep 2; \
		timeout=$$((timeout-2)); \
	done

	@echo ""
	@echo "🎉 Development environment is ready!"
	@echo "=================================="
	@echo "🌐 API: http://localhost:8000"
	@echo "📚 Docs: http://localhost:8000/docs"
	@echo "🏥 Health: http://localhost:8000/health"
	@echo "🗄️  Database: localhost:5432 (user: lunch_voting, pass: secure_password)"
	@echo "📊 Redis: localhost:6379"
	@echo ""
	@echo "🔧 Useful commands:"
	@echo "  make stop     - Stop all services"
	@echo "  make logs     - View application logs"
	@echo "  make test     - Run tests"
	@echo "  make lint     - Run code quality checks"

stop: ## 🛑 Stop all development services
	@echo "🛑 Stopping all services..."
	@docker-compose down
	@echo "✅ All services stopped"

logs-dev: ## 📋 View development application logs
	@docker-compose logs -f app-dev

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
test: ## Run tests with coverage (local)
	pytest --cov=app --cov-report=html --cov-report=term-missing

test-watch: ## Run tests in watch mode (local)
	pytest-watch -- --cov=app

test-quick: ## Run tests without coverage (local)
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

docker-dev: ## Start development environment with Docker Compose (alternative to 'make setup')
	@echo "🐳 Starting development environment..."
	docker-compose --profile development up --build

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

logs-railway: ## View Railway production logs
	railway logs

logs: logs-dev ## Alias for logs-dev (view local development logs)

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
