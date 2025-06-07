#!/bin/bash

# 🚀 Deployment Script for Lunch Voting API
# Usage: ./scripts/deploy.sh [environment]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default environment
ENVIRONMENT=${1:-production}

echo -e "${BLUE}🚀 Starting deployment for ${ENVIRONMENT} environment${NC}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
    echo -e "${YELLOW}Valid environments: development, staging, production${NC}"
    exit 1
fi

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}⚠️  Railway CLI not found. Installing...${NC}"
    curl -fsSL https://railway.app/install.sh | sh
    export PATH="$HOME/.railway/bin:$PATH"
fi

# Check if user is logged in to Railway
if ! railway whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Please log in to Railway first:${NC}"
    echo "railway login"
    exit 1
fi

# Pre-deployment checks
echo -e "${BLUE}🔍 Running pre-deployment checks...${NC}"

# Check if Docker is running (for local testing)
if command -v docker &> /dev/null && docker ps &> /dev/null; then
    echo -e "${GREEN}✅ Docker is running${NC}"

    # Build and test Docker image
    echo -e "${BLUE}🔨 Building Docker image...${NC}"
    docker build --target production -t lunch-voting-api:latest .

    echo -e "${BLUE}🧪 Testing Docker image...${NC}"
    docker run --rm -d --name test-api -p 8001:8000 -e ENVIRONMENT=development lunch-voting-api:latest
    sleep 10

    # Test health endpoint
    if curl -f http://localhost:8001/health &> /dev/null; then
        echo -e "${GREEN}✅ Docker image health check passed${NC}"
        docker stop test-api
    else
        echo -e "${RED}❌ Docker image health check failed${NC}"
        docker stop test-api
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Docker not available, skipping local image test${NC}"
fi

# Run tests
echo -e "${BLUE}🧪 Running test suite...${NC}"
if command -v pytest &> /dev/null; then
    export ENVIRONMENT=development
    export POSTGRES_USER=postgres
    export POSTGRES_PASSWORD=postgres
    export POSTGRES_DB=lunch_voting_test
    export SECRET_KEY=test-secret-key

    if pytest --tb=short -q; then
        echo -e "${GREEN}✅ All tests passed${NC}"
    else
        echo -e "${RED}❌ Tests failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  pytest not found, skipping tests${NC}"
fi

# Deploy to Railway
echo -e "${BLUE}🚂 Deploying to Railway (${ENVIRONMENT})...${NC}"

if [[ "$ENVIRONMENT" == "production" ]]; then
    # Production deployment
    railway up --detach
elif [[ "$ENVIRONMENT" == "staging" ]]; then
    # Staging deployment (if you have a staging environment)
    railway up --detach --environment staging
else
    # Development deployment
    railway up --detach --environment development
fi

# Wait for deployment to complete
echo -e "${BLUE}⏳ Waiting for deployment to complete...${NC}"
sleep 30

# Get deployment URL
DEPLOYMENT_URL=$(railway url)

# Health check
echo -e "${BLUE}🏥 Performing health check...${NC}"
if curl -f "${DEPLOYMENT_URL}/health" &> /dev/null; then
    echo -e "${GREEN}✅ Health check passed${NC}"
    echo -e "${GREEN}🎉 Deployment successful!${NC}"
    echo -e "${BLUE}🌐 Application URL: ${DEPLOYMENT_URL}${NC}"
    echo -e "${BLUE}📊 Metrics: ${DEPLOYMENT_URL}/metrics/health${NC}"
    echo -e "${BLUE}📖 API Docs: ${DEPLOYMENT_URL}/docs${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo -e "${YELLOW}Check logs: railway logs${NC}"
    exit 1
fi

# Run database migrations
echo -e "${BLUE}🗄️  Running database migrations...${NC}"
railway run alembic upgrade head

echo -e "${GREEN}🚀 Deployment completed successfully!${NC}"
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  View logs: ${YELLOW}railway logs${NC}"
echo -e "  Open shell: ${YELLOW}railway shell${NC}"
echo -e "  Check status: ${YELLOW}railway status${NC}"
echo -e "  Open dashboard: ${YELLOW}railway open${NC}"
