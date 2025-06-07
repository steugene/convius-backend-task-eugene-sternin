#!/bin/bash

# 🏥 Health Check Script for Lunch Voting API
# Usage: ./scripts/health_check.sh [url]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default URL
BASE_URL=${1:-"http://localhost:8000"}

echo -e "${BLUE}🏥 Running health checks for: ${BASE_URL}${NC}"

# Function to make HTTP request and check status
check_endpoint() {
    local endpoint=$1
    local expected_status=$2
    local description=$3

    echo -e "${BLUE}🔍 Checking ${description}...${NC}"

    response=$(curl -s -w "HTTPSTATUS:%{http_code}" "${BASE_URL}${endpoint}" || echo "HTTPSTATUS:000")
    status=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo "$response" | sed -e 's/HTTPSTATUS:.*//')

    if [ "$status" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ ${description}: OK (${status})${NC}"
        return 0
    else
        echo -e "${RED}❌ ${description}: Failed (${status})${NC}"
        if [ ! -z "$body" ]; then
            echo -e "${YELLOW}   Response: ${body}${NC}"
        fi
        return 1
    fi
}

# Function to check JSON response
check_json_endpoint() {
    local endpoint=$1
    local description=$2
    local expected_field=$3

    echo -e "${BLUE}🔍 Checking ${description}...${NC}"

    response=$(curl -s "${BASE_URL}${endpoint}" || echo '{"error": "connection_failed"}')

    if echo "$response" | jq -e ".$expected_field" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ${description}: OK${NC}"
        if [ "$expected_field" = "status" ]; then
            status_value=$(echo "$response" | jq -r ".$expected_field")
            echo -e "${BLUE}   Status: ${status_value}${NC}"
        fi
        return 0
    else
        echo -e "${RED}❌ ${description}: Failed${NC}"
        echo -e "${YELLOW}   Response: ${response}${NC}"
        return 1
    fi
}

# Track overall health
overall_health=0

echo -e "${BLUE}📋 Starting comprehensive health check...${NC}"
echo "=================================================="

# Basic connectivity
if ! check_endpoint "/" 200 "Basic connectivity"; then
    overall_health=1
fi

# Health endpoints
if ! check_json_endpoint "/health" "Basic health check" "status"; then
    overall_health=1
fi

if ! check_json_endpoint "/health/live" "Liveness check" "status"; then
    overall_health=1
fi

if ! check_json_endpoint "/health/ready" "Readiness check" "status"; then
    overall_health=1
fi

# API documentation
if ! check_endpoint "/docs" 200 "API documentation"; then
    overall_health=1
fi

if ! check_endpoint "/openapi.json" 200 "OpenAPI specification"; then
    overall_health=1
fi

# Metrics endpoints
if ! check_endpoint "/metrics" 200 "Prometheus metrics"; then
    overall_health=1
fi

if ! check_json_endpoint "/metrics/health" "Application metrics" "requests_total"; then
    overall_health=1
fi

# API endpoints (basic)
if ! check_endpoint "/api/v1/restaurants/" 401 "Restaurants endpoint (unauthorized)"; then
    overall_health=1
fi

if ! check_endpoint "/api/v1/auth/register" 422 "Registration endpoint (no data)"; then
    overall_health=1
fi

echo "=================================================="

# Performance check
echo -e "${BLUE}⚡ Performance check...${NC}"
start_time=$(date +%s%N)
curl -s "${BASE_URL}/health" > /dev/null
end_time=$(date +%s%N)
response_time=$(( (end_time - start_time) / 1000000 ))

if [ "$response_time" -lt 1000 ]; then
    echo -e "${GREEN}✅ Response time: ${response_time}ms (Good)${NC}"
elif [ "$response_time" -lt 5000 ]; then
    echo -e "${YELLOW}⚠️  Response time: ${response_time}ms (Acceptable)${NC}"
else
    echo -e "${RED}❌ Response time: ${response_time}ms (Slow)${NC}"
    overall_health=1
fi

# Database connection check (through health endpoint)
echo -e "${BLUE}🗄️  Database connectivity check...${NC}"
db_response=$(curl -s "${BASE_URL}/health/ready" || echo '{"status": "error"}')
db_status=$(echo "$db_response" | jq -r '.database // "unknown"')

if [ "$db_status" = "connected" ]; then
    echo -e "${GREEN}✅ Database: Connected${NC}"
elif [ "$db_status" = "unknown" ]; then
    echo -e "${YELLOW}⚠️  Database: Status unknown${NC}"
else
    echo -e "${RED}❌ Database: ${db_status}${NC}"
    overall_health=1
fi

# Memory and resource check (if metrics available)
echo -e "${BLUE}📊 Resource usage check...${NC}"
metrics_response=$(curl -s "${BASE_URL}/metrics/health" 2>/dev/null || echo '{}')
memory_usage=$(echo "$metrics_response" | jq -r '.memory_usage_mb // "unknown"')
active_connections=$(echo "$metrics_response" | jq -r '.database_connections // "unknown"')

if [ "$memory_usage" != "unknown" ]; then
    echo -e "${BLUE}   Memory usage: ${memory_usage} MB${NC}"
fi

if [ "$active_connections" != "unknown" ]; then
    echo -e "${BLUE}   Database connections: ${active_connections}${NC}"
fi

echo "=================================================="

# Summary
if [ $overall_health -eq 0 ]; then
    echo -e "${GREEN}🎉 All health checks passed!${NC}"
    echo -e "${GREEN}✅ System is healthy and ready for traffic${NC}"
    exit 0
else
    echo -e "${RED}❌ Some health checks failed!${NC}"
    echo -e "${YELLOW}⚠️  Please check the failed endpoints above${NC}"
    exit 1
fi
