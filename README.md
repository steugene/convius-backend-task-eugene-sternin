# 🍽️ Lunch Voting API

A production-ready REST API for lunch voting system built with FastAPI, featuring advanced security, monitoring, and deployment capabilities.

## ✨ Features

### 🔧 Core Functionality
- **User Authentication** - JWT-based authentication with secure password hashing
- **Restaurant Management** - CRUD operations for restaurants
- **Voting System** - Weighted voting with daily limits and winner determination
- **Vote History** - Track voting patterns and historical data

### 🛡️ Security & Production Features
- **Rate Limiting** - Configurable request limits per endpoint
- **Input Validation** - Comprehensive request validation with Pydantic
- **Security Headers** - CSRF, XSS, and other security protections
- **Error Handling** - Global exception handling with structured logging
- **CORS Configuration** - Configurable cross-origin resource sharing

### 📊 Monitoring & Observability
- **Health Checks** - Liveness, readiness, and database connectivity checks
- **Metrics** - Prometheus metrics for monitoring and alerting
- **Structured Logging** - JSON logging with request tracking
- **Performance Monitoring** - Request duration and error rate tracking

### 🚀 Deployment & DevOps
- **Containerization** - Multi-stage Docker builds for development and production
- **Environment Configuration** - Comprehensive environment variable support
- **Database Migrations** - Alembic integration for schema management
- **Load Balancer Ready** - Health check endpoints and graceful shutdown

## 🏗️ Architecture

```
├── app/
│   ├── api/v1/endpoints/     # API endpoints
│   ├── core/                 # Core configuration and utilities
│   ├── crud/                 # Database operations
│   ├── db/                   # Database configuration
│   ├── models/               # SQLAlchemy models
│   └── schemas/              # Pydantic schemas
├── tests/                    # Test suite
├── alembic/                  # Database migrations
├── logs/                     # Application logs
└── monitoring/               # Monitoring configurations
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- Docker & Docker Compose (optional)

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd lunch-voting-api

# Copy environment template
cp env.example .env

# Edit .env with your configuration
vim .env
```

### 2. Database Setup

```bash
# Create database
createdb lunch_voting

# Run migrations
alembic upgrade head
```

### 3. Development Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Run development server
uvicorn app.main:app --reload

# Or use Docker Compose
docker-compose --profile development up
```

### 4. Production Deployment

```bash
# Using Docker Compose
docker-compose --profile production up -d

# Or build and run manually
docker build --target production -t lunch-voting-api .
docker run -p 8000:8000 lunch-voting-api
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Deployment environment | `development` | No |
| `DEBUG` | Debug mode | `false` | No |
| `SECRET_KEY` | JWT secret key | Generated | **Yes** |
| `POSTGRES_SERVER` | Database host | `localhost` | **Yes** |
| `POSTGRES_USER` | Database user | - | **Yes** |
| `POSTGRES_PASSWORD` | Database password | - | **Yes** |
| `POSTGRES_DB` | Database name | - | **Yes** |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `VOTES_PER_DAY` | Daily vote limit | `3` | No |

See `env.example` for complete configuration options.

## 📡 API Documentation

### Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login

#### Restaurants
- `GET /api/v1/restaurants` - List restaurants
- `POST /api/v1/restaurants` - Create restaurant
- `GET /api/v1/restaurants/{id}` - Get restaurant
- `PUT /api/v1/restaurants/{id}` - Update restaurant
- `DELETE /api/v1/restaurants/{id}` - Delete restaurant
- `POST /api/v1/restaurants/{id}/vote` - Vote for restaurant
- `GET /api/v1/restaurants/winner/today` - Get today's winner

#### Monitoring
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check
- `GET /health/live` - Liveness check
- `GET /metrics` - Prometheus metrics
- `GET /metrics/health` - Application metrics

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs` (development only)
- **ReDoc**: `http://localhost:8000/redoc` (development only)

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

### Security Headers
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security (production)

## 📊 Monitoring

### Health Checks
- `GET /health` - Basic service status
- `GET /health/ready` - Service readiness (includes DB check)
- `GET /health/live` - Service liveness

### Metrics
Prometheus metrics available at `/metrics`:
- HTTP request metrics
- Database connection metrics
- Vote counting metrics
- Custom application metrics

### Logging
Structured JSON logging with:
- Request/response tracking
- Error tracking with stack traces
- Performance metrics
- Security events

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_voting.py

# Run with verbose output
pytest -v
```

## 🏭 Production Deployment

### Docker Compose (Recommended)

```bash
# Production deployment
docker-compose --profile production up -d

# With monitoring
docker-compose --profile production --profile monitoring up -d
```

### Manual Deployment

```bash
# Build production image
docker build --target production -t lunch-voting-api .

# Run with proper environment
docker run -d \
  --name lunch-voting-api \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e SECRET_KEY=your-secret-key \
  -e POSTGRES_SERVER=your-db-host \
  -e POSTGRES_USER=your-db-user \
  -e POSTGRES_PASSWORD=your-db-password \
  -e POSTGRES_DB=lunch_voting \
  lunch-voting-api
```

### Environment-Specific Configurations

#### Development
- Debug mode enabled
- Detailed error messages
- Auto-reload on code changes
- API documentation accessible

#### Production
- Debug mode disabled
- Generic error messages
- Optimized performance
- Security headers enabled
- API documentation disabled

## 🔄 Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check current version
alembic current
```

## 🎯 Performance

### Optimization Features
- Connection pooling with SQLAlchemy
- Async request handling
- Response caching headers
- Gzip compression
- Static file serving optimization

### Scaling Considerations
- Stateless design for horizontal scaling
- Database connection pooling
- Redis integration for session storage
- Load balancer health checks
- Graceful shutdown handling

## 🛠️ Development

### Code Quality Tools
```bash
# Format code
black app tests

# Sort imports
isort app tests

# Type checking
mypy app

# Linting
flake8 app tests

# Run all quality checks
pre-commit run --all-files
```

### Testing Strategy
- Unit tests for business logic
- Integration tests for API endpoints
- Database transaction testing
- Authentication flow testing
- Error handling validation

## 📈 Monitoring Setup

### Prometheus + Grafana

```bash
# Start monitoring stack
docker-compose --profile monitoring up -d

# Access Grafana
open http://localhost:3000
# Default login: admin/admin
```

### Key Metrics to Monitor
- HTTP request rate and latency
- Error rates and types
- Database query performance
- Authentication success/failure rates
- Vote submission patterns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues

**Database Connection Errors**
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database exists and is accessible

**Authentication Issues**
- Verify `SECRET_KEY` is set
- Check token expiration
- Validate user credentials

**Rate Limiting**
- Check current rate limits in logs
- Wait for rate limit reset
- Configure higher limits if needed

### Getting Help
- Check the logs in `logs/` directory
- Review health check endpoints
- Enable debug mode for detailed errors
- Consult the API documentation at `/docs`

---

**Built with ❤️ using FastAPI, SQLAlchemy, and modern Python practices.**
