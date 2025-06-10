# 🍽️ Lunch Voting API

REST API for team lunch voting with JWT authentication, weighted voting logic, and monitoring capabilities.

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

### One Command Setup ⚡

```bash
# Clone repository
git clone git@github.com:steugene/convius-backend-task-eugene-sternin.git
cd convius-backend-task-eugene-sternin

# 🚀 Local development setup
make start
```

**After setup completes:**
- 🌐 **API**: http://localhost:8000
- 📚 **Docs**: http://localhost:8000/docs
- 🏥 **Health**: http://localhost:8000/health

### Common Commands

```bash
# Stop all services
make stop

# View logs
make logs

# Run tests
make test

# Code formatting & linting
make format
make lint

# Database operations
make db-upgrade    # Apply migrations
make db-reset      # Reset database

# See all available commands
make help
```

### Manual Setup (if preferred)

### Prerequisites
- Python 3.9+
- PostgreSQL 12+

### 1. Setup

```bash
# Clone repository
git clone git@github.com:steugene/convius-backend-task-eugene-sternin.git
cd convius-backend-task-eugene-sternin

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
| **Restaurants** | CRUD operations for restaurants | `/restaurants/`, `/restaurants/{id}` |
| **Vote Sessions** | User-managed voting sessions | `/vote-sessions/`, `/vote-sessions/{id}/vote` |
| **Health** | System monitoring | `/health`, `/metrics` |

> 💡 **Tip**: Visit the [Swagger UI](https://conviustask-production.up.railway.app/docs) for complete API documentation with interactive testing

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

## 🗳️ Enhanced Vote Session System

### Architecture Evolution

**Original Requirements vs. Our Implementation:**

The original requirements called for a daily weighted voting system where:
- Users get X votes per day (hardcoded)
- Votes have weights: 1st = 1.0, 2nd = 0.5, 3rd+ = 0.25
- Daily reset with unused votes lost
- History of daily winners

**Why This Approach Was Chosen:**

This project implements a **flexible vote session system** that keeps all the weighted voting logic but makes it more practical:

✅ **Configurable per session** - Different sessions can have different vote limits
✅ **User-managed** - Any user can create voting sessions for specific occasions
✅ **Auto-closing** - Sessions can close automatically at specified times
✅ **Same weighted math** - Exact same voting weights (1.0, 0.5, 0.25) and tie-breaking
✅ **Better UX** - Context-aware voting instead of daily limits

This approach provides **more flexibility for real-world usage** while maintaining all the mathematical requirements from the original spec.

### How It Works

1. **Create Session**: Any user creates a new vote session with configurable settings:
   ```json
   {
     "title": "Lunch Dec 12th",
     "votes_per_user": 3,  // How many votes each user gets
     "auto_close_at": "2025-12-12T14:00:00Z"  // Optional auto-close
   }
   ```

2. **Add Restaurants**: Session creator selects which restaurants to include
3. **Start Voting**: Creator starts the session → Status becomes ACTIVE
4. **Weighted Voting**: Users cast multiple votes with decreasing weights:
   - 1st vote = 1.0 weight
   - 2nd vote = 0.5 weight
   - 3rd+ votes = 0.25 weight
5. **Real-time Results**: Weighted totals with tie-breaking by distinct voters
6. **Auto/Manual Close**: Sessions close automatically or when creator ends them

### 🎯 **Key Features**
- **User-Created**: Any authenticated user can create voting sessions
- **Configurable Voting**: Set how many votes each user gets (1-N votes per session)
- **Weighted Logic**: Implements original requirements (1.0, 0.5, 0.25 weights)
- **Auto-Closing**: Optional automatic session closing at specified times
- **Flexible Restaurant Selection**: Choose specific restaurants for each vote
- **Smart Results**: Weighted totals with tie-breaking by distinct voters
- **Session States**: DRAFT → ACTIVE → CLOSED workflow

### 📊 **Usage Examples**

**Simple Session (like traditional voting):**
```json
{
  "title": "Quick Lunch Choice",
  "votes_per_user": 1  // Each user gets 1 vote = 1.0 weight
}
```

**Weighted Session (original requirements):**
```json
{
  "title": "Complex Lunch Vote",
  "votes_per_user": 3,  // Each user gets 3 votes with weights 1.0, 0.5, 0.25
  "auto_close_at": "2025-12-12T14:00:00Z"
}
```

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

**Tech Stack**: FastAPI • SQLAlchemy • PostgreSQL • Railway
