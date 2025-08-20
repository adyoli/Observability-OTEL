#!/bin/bash
set -e

echo "Robin Interview - Document API Setup"
echo "===================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1 && ! docker compose version > /dev/null 2>&1; then
    echo "Error: Docker Compose is not available. Please install Docker Compose and try again."
    exit 1
fi

echo "✓ Docker is running"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ Created .env file"
fi

# Build Docker images
echo "Building Docker images..."
docker compose build

echo "✓ Docker images built successfully"

# Start services
echo "Starting services..."
docker compose up -d

echo "✓ Services started"

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo "Checking service health..."

# Check postgres
if docker compose exec postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✓ PostgreSQL is ready"
else
    echo "⚠ PostgreSQL not ready yet, waiting..."
    sleep 5
fi

# Check data-store
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "✓ Data Store service is ready"
else
    echo "⚠ Data Store service not ready yet, waiting..."
    sleep 5
fi

# Check document-api
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Document API service is ready"
else
    echo "⚠ Document API service not ready yet, waiting..."
    sleep 5
fi

# Check nginx
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✓ Nginx proxy is ready"
else
    echo "⚠ Nginx proxy not ready yet, this might be normal"
fi

echo ""
echo "Setup complete! 🎉"
echo ""
echo "Services are now running:"
echo "  - Nginx Proxy:    http://localhost"
echo "  - Document API:   http://localhost:8000 (direct)"
echo "  - Data Store:     http://localhost:8001"
echo "  - PostgreSQL:     localhost:5432"
echo ""
echo "To test the API, run:"
echo "  make test"
echo ""
echo "To view logs:"
echo "  docker compose logs -f"
echo ""
echo "To stop services:"
echo "  docker compose down"
