#!/bin/bash

# Sales API Quick Start Script

set -e

echo "================================"
echo "Sales API - Quick Start"
echo "================================"

# Check if Docker is running
echo ""
echo "✓ Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "✗ Docker is not installed. Please install Docker first."
    exit 1
fi

# Start Docker containers
echo "✓ Starting Docker services (PostgreSQL & Redis)..."
docker-compose up -d

# Wait for services to be healthy
echo "✓ Waiting for services to be healthy..."
sleep 5

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "✓ Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "✓ Installing dependencies..."
pip install -q -r requirements.txt

# Run migrations
echo "✓ Running Alembic migrations..."
alembic upgrade head

# Start the application
echo ""
echo "================================"
echo "✓ All set! Starting application..."
echo "================================"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo "API: http://localhost:8000"
echo ""

uvicorn app.main:app --reload
