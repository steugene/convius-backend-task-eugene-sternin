#!/bin/bash

# Set default port if not provided
PORT=${PORT:-8000}

# Set production environment variables
export ENVIRONMENT=${ENVIRONMENT:-production}
export DEBUG=${DEBUG:-false}
export LOG_LEVEL=${LOG_LEVEL:-INFO}

# Set Python path so alembic can find the app module
export PYTHONPATH=/app:$PYTHONPATH

echo "Starting application on port: $PORT"
echo "Environment: $ENVIRONMENT"

# Wait for database to be ready
echo "Waiting for database connection..."
python -c "
import time
import sys
from app.core.config import settings
from app.db.session import engine
from sqlalchemy import text

max_retries = 30
for i in range(max_retries):
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('Database connection successful!')
        break
    except Exception as e:
        print(f'Database connection attempt {i+1}/{max_retries} failed: {e}')
        if i == max_retries - 1:
            print('Failed to connect to database after 30 attempts')
            sys.exit(1)
        time.sleep(2)
"

# Run database migrations with verbose output
echo "Running database migrations..."
cd /app

echo "Current migration version:"
alembic current || echo "No current version found"

echo "Running alembic upgrade head..."
alembic upgrade head || {
    echo "Migration failed! Exiting..."
    exit 1
}

echo "Migration completed. Current version:"
alembic current

# Start the application with proper port binding
echo "Starting gunicorn server..."
exec gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:$PORT" \
    --access-logfile - \
    --error-logfile - \
    --timeout 120 \
    --keep-alive 2
