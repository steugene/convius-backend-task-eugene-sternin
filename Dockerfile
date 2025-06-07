# Use Python 3.11 slim as base image
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy dependency files (both pyproject.toml and README.md needed for package metadata)
COPY pyproject.toml README.md ./

# Install the package in production mode
RUN pip install --no-cache-dir .

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir ".[dev]"

# Copy application code
COPY . .

# Change ownership to app user
RUN chown -R appuser:appuser /app

# Switch to app user
USER appuser

# Expose port
EXPOSE 8000

# Command for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Install production dependencies
RUN pip install --no-cache-dir ".[production]"

# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Create logs directory
RUN mkdir -p /app/logs

# Change ownership to app user
RUN chown -R appuser:appuser /app

# Switch to app user
USER appuser

# Expose port 8000 (Railway will map to dynamic PORT)
EXPOSE 8000

# Health check handled by Railway via railway.toml

# Default command (Railway will override this with startCommand)
CMD ["bash", "start.sh"] 