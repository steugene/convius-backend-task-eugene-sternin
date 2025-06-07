# 🍽️ Lunch Voting API

A production-ready REST API for lunch voting system built with FastAPI, featuring JWT authentication, weighted voting, and comprehensive monitoring.

## ✨ Features

- **🔐 User Authentication** - JWT-based authentication with secure password hashing
- **🏪 Restaurant Management** - CRUD operations for restaurants
- **🗳️ Weighted Voting System** - Time-based voting weights with daily limits
- **🏆 Winner Determination** - Automatic daily winner calculation
- **🛡️ Security** - Rate limiting, input validation, CORS, and security headers
- **📊 Monitoring** - Health checks, metrics, and structured logging
- **🚀 Production Ready** - Deployed on Railway with PostgreSQL

## 🔗 Live API

- **🌐 Production API**: [https://conviustask-production.up.railway.app](https://conviustask-production.up.railway.app)
- **📚 Interactive Docs**: [https://conviustask-production.up.railway.app/docs](https://conviustask-production.up.railway.app/docs)
- **📖 ReDoc**: [https://conviustask-production.up.railway.app/redoc](https://conviustask-production.up.railway.app/redoc)

## 🏗️ Architecture

```
├── app/
│   ├── api/v1/endpoints/     # API endpoints
│   ├── core/                 # Configuration and utilities
│   ├── crud/                 # Database operations
│   ├── db/                   # Database configuration
│   ├── models/               # SQLAlchemy models
│   └── schemas/              # Pydantic schemas
├── tests/                    # Test suite
└── alembic/                  # Database migrations
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 12+

### 1. Setup

```bash
# Clone the repository
git clone <repository-url>
cd lunch-voting-api

# Copy environment template
cp env.example .env
# Edit .env with your database credentials

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks for code quality
pre-commit install
```

### 2. Database

```bash
# Create database
createdb lunch_voting

# Run migrations
alembic upgrade head
```

### 3. Run

```bash
# Development server
uvicorn app.main:app --reload

# Access API documentation
open http://localhost:8000/docs
```

## 🛠️ Development

### Code Quality

This project uses pre-commit hooks to ensure code quality and consistency:

```bash
# Pre-commit hooks run automatically on git commit
git commit -m "Your commit message"

# Run hooks manually on all files
pre-commit run --all-files

# Individual tools can also be run directly
black app tests          # Code formatting
isort app tests          # Import sorting
flake8 app tests         # Linting
mypy app                 # Type checking
pytest                   # Tests
```

**Pre-commit Hooks Include:**
- ✅ **Black**: Code formatting
- ✅ **isort**: Import sorting
- ✅ **flake8**: Style and error checking
- ✅ **mypy**: Static type checking
- ✅ **pytest**: Automated testing
- ✅ File cleanup (trailing whitespace, end of file)

All code must pass these checks before being committed!

## 📡 API Documentation

### 🎯 Quick API Overview

| Category | Description | Key Endpoints |
|----------|-------------|---------------|
| **Authentication** | User registration and JWT login | `/auth/register`, `/auth/login` |
| **Restaurants** | CRUD operations and voting | `/restaurants/`, `/restaurants/{id}/vote` |
| **Voting** | Daily weighted voting system | `/restaurants/winner/today` |
| **Health** | System monitoring | `/health`, `/metrics` |

> 💡 **Tip**: Visit the [Swagger UI](https://conviustask-production.up.railway.app/docs) for complete API documentation with interactive testing!

## 🔒 Security

### Authentication
JWT tokens with configurable expiration. Include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### Rate Limiting
- Global: 60 requests/minute
- Auth endpoints: 5 requests/minute
- Vote endpoints: 10 requests/minute

### Security Features
- Input validation with Pydantic
- CORS configuration
- Security headers (XSS, CSRF protection)
- Secure password hashing

## 🗳️ Vote Session System

### Flexible Voting Architecture
Modern vote session system where users create, manage, and participate in voting polls:

### 🔧 **How It Works**
1. **Create Session**: Any user creates a new vote session (e.g., "Lunch Dec 12th")
2. **Add Restaurants**: Session creator selects which restaurants to include
3. **Start Voting**: Creator starts the session → Status becomes ACTIVE
4. **Users Vote**: All users can vote for their preferred restaurant (one vote per user)
5. **View Results**: Real-time results showing vote counts
6. **Close Session**: Creator ends voting → Status becomes CLOSED

### 🎯 **Key Features**
- **User-Created**: Any authenticated user can create voting sessions
- **Controlled Access**: Only session creator can manage (add restaurants, start/end)
- **Flexible Restaurant Selection**: Choose specific restaurants for each vote
- **Vote Changes**: Users can change their choice while session is active
- **Real-time Results**: Live vote counting and winner determination
- **Session States**: DRAFT → ACTIVE → CLOSED workflow

### 📊 **Session States**
- **DRAFT**: Session created, restaurants being added
- **ACTIVE**: Voting is open to all users
- **CLOSED**: Voting ended, results finalized

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_voting.py
```

## 🔄 Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Check current version
alembic current
```

## ⚙️ Configuration

Key environment variables (see `env.example` for complete list):

```bash
# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=lunch_voting

# Security
SECRET_KEY=your-secret-key

# Optional
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Install pre-commit hooks: `pre-commit install`
5. Add tests for new functionality
6. Ensure all pre-commit hooks pass: `pre-commit run --all-files`
7. Submit a pull request

**Note**: All commits must pass pre-commit hooks (formatting, linting, type checking, and tests).

## 🆘 Support

### Common Issues

**Database Connection**
- Verify PostgreSQL is running
- Check credentials in `.env`
- Ensure database exists

**Authentication**
- Verify `SECRET_KEY` is set
- Check token expiration
- Use correct Authorization header format

### Getting Help
- Check application logs
- Review [API documentation](https://conviustask-production.up.railway.app/docs)
- Test endpoints with Swagger UI

---

**Built with ❤️ using FastAPI, SQLAlchemy, and deployed on Railway.**
