# 🤝 Contributing to Lunch Voting API

Thank you for your interest in contributing to the Lunch Voting API! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Code of Conduct](#code-of-conduct)

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 12 or higher
- Git
- Docker (optional, for containerized development)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/steugene/convius-backend-task-eugene-sternin.git
   cd convius-backend-task-eugene-sternin
   ```

## 🛠️ Development Setup

### Quick Start

```bash
# Install development dependencies
make dev

# Or manually:
pip install -e ".[dev]"
pre-commit install

# Set up environment variables
cp env.example .env
# Edit .env with your database credentials

# Run database migrations
make db-upgrade

# Start development server
make run
```

### Available Commands

Use `make help` to see all available commands:

```bash
make help
```

Common commands:
- `make dev` - Install development dependencies
- `make test` - Run tests with coverage
- `make lint` - Run linting
- `make format` - Format code
- `make run` - Start development server

## 🎨 Code Style

We use the following tools to maintain code quality:

### Formatting
- **Black** for code formatting
- **isort** for import sorting

### Linting
- **flake8** for style guide enforcement
- **mypy** for type checking
- **bandit** for security analysis

### Pre-commit Hooks

Pre-commit hooks are automatically installed with `make dev`. They run:
- Code formatting (black, isort)
- Linting (flake8, mypy, bandit)
- Security checks
- Tests

To run manually:
```bash
make pre-commit
```

### Code Style Guidelines

1. **Follow PEP 8** with 88 character line length
2. **Use type hints** for all function parameters and return values
3. **Write docstrings** for all public functions and classes
4. **Use descriptive variable names**
5. **Keep functions small and focused**

Example:
```python
from typing import List, Optional
from app.schemas.restaurant import Restaurant

def get_restaurants(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[Restaurant]:
    """
    Retrieve a list of restaurants with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of restaurant objects
    """
    return db.query(Restaurant).offset(skip).limit(limit).all()
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests with coverage
make test

# Run tests without coverage (faster)
make test-quick

# Run specific test file
pytest tests/test_restaurants.py -v

# Run specific test
pytest tests/test_restaurants.py::test_create_restaurant -v
```

### Writing Tests

1. **Write tests for all new functionality**
2. **Use descriptive test names**
3. **Follow AAA pattern** (Arrange, Act, Assert)
4. **Use fixtures** for common test data

Example:
```python
def test_create_restaurant_success(client, test_user_token):
    """Test successful restaurant creation with valid data."""
    # Arrange
    restaurant_data = {
        "name": "Test Restaurant",
        "description": "A test restaurant",
        "address": "123 Test St"
    }

    # Act
    response = client.post(
        "/api/v1/restaurants/",
        json=restaurant_data,
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == restaurant_data["name"]
```

### Coverage Requirements

- **Minimum 80% coverage** for new code
- **Aim for 90%+ coverage** on critical paths
- **100% coverage** on utility functions

## 📝 Pull Request Process

### Before Submitting

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the style guide

3. **Add tests** for your changes

4. **Run the test suite**:
   ```bash
   make test
   make lint
   ```

5. **Update documentation** if needed

6. **Commit your changes** with descriptive messages:
   ```bash
   git commit -m "feat: add restaurant search functionality"
   ```

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

### Submitting the PR

1. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** on GitHub

3. **Fill out the PR template** completely

4. **Wait for review** and address feedback

### Review Process

- All PRs require at least one review
- CI checks must pass
- Code coverage must not decrease
- Documentation must be updated if needed

## 🐛 Issue Reporting

### Before Creating an Issue

1. **Search existing issues** to avoid duplicates
2. **Check the documentation** for solutions
3. **Try the latest version** to see if the issue persists

### Bug Reports

Use the bug report template and include:
- Clear description of the issue
- Steps to reproduce
- Expected vs. actual behavior
- Environment details
- Error logs/screenshots

### Feature Requests

Use the feature request template and include:
- Clear description of the feature
- Use cases and motivation
- Acceptance criteria
- Implementation ideas (if any)

## 🔧 Development Tips

### Database Development

```bash
# Create a new migration
make db-revision msg="your migration description"

# Apply migrations
make db-upgrade

# Reset database (development only)
make db-reset
```

### Docker Development

```bash
# Start development environment
make docker-dev

# Build production image
make docker-build
```

### Debugging

1. **Use the debugger** instead of print statements
2. **Check logs** for error details
3. **Use health check endpoints** to verify service status

### API Testing

- Use the **interactive docs** at `http://localhost:8000/docs`
- Test with **different user roles** and permissions
- Verify **error handling** and edge cases

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [Pytest Documentation](https://docs.pytest.org/)

## 🤔 Questions?

- **General questions**: Use GitHub Discussions
- **Bug reports**: Create an issue
- **Feature requests**: Create an issue
- **Security issues**: Email eu.steinberg@gmail.com

## 🙏 Recognition

Contributors are recognized in our [README.md](README.md) and release notes.

Thank you for contributing! 🎉
