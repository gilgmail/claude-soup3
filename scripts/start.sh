#!/bin/bash

# Financial Wisdom Platform Startup Script

set -e

echo "🚀 Starting Financial Wisdom Platform..."

# Function to check if service is running
check_service() {
    local service=$1
    local port=$2
    local max_attempts=${3:-30}
    local attempt=1
    
    echo "⏳ Waiting for $service to be ready on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$port" > /dev/null 2>&1 || nc -z localhost $port 2>/dev/null; then
            echo "✅ $service is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts - $service not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    echo "❌ $service failed to start after $max_attempts attempts"
    return 1
}

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "📝 Please edit .env file with your configuration before running again."
        echo "   At minimum, set your AI API keys:"
        echo "   - ANTHROPIC_API_KEY"
        echo "   - OPENAI_API_KEY"
        exit 1
    else
        echo "❌ Neither .env nor .env.example found. Please create .env file."
        exit 1
    fi
fi

# Validate required environment variables
echo "🔍 Validating configuration..."

if ! grep -q "ANTHROPIC_API_KEY=sk-" .env 2>/dev/null && ! grep -q "ANTHROPIC_API_KEY=your_" .env 2>/dev/null; then
    echo "⚠️  ANTHROPIC_API_KEY not set in .env file"
fi

if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null && ! grep -q "OPENAI_API_KEY=your_" .env 2>/dev/null; then
    echo "⚠️  OPENAI_API_KEY not set in .env file"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p docker/{nginx/ssl,postgres,redis,prometheus,grafana}
mkdir -p logs

# Start infrastructure services first
echo "🐳 Starting infrastructure services..."
docker-compose up -d postgres redis elasticsearch

# Wait for infrastructure to be ready
check_service "PostgreSQL" 5432 || exit 1
check_service "Redis" 6379 || exit 1
check_service "Elasticsearch" 9200 || exit 1

# Run database migrations
echo "📊 Running database migrations..."
docker-compose run --rm api alembic upgrade head

# Start application services
echo "🌐 Starting application services..."
docker-compose up -d api worker scheduler nginx

# Wait for API to be ready
check_service "API" 8000 || exit 1

# Start monitoring services (optional)
if [ "$1" = "--with-monitoring" ]; then
    echo "📊 Starting monitoring services..."
    docker-compose --profile monitoring up -d
    
    check_service "Prometheus" 9090
    check_service "Grafana" 3000
fi

# Health check
echo "🔍 Performing health checks..."

API_HEALTH=$(curl -s http://localhost:8000/health | grep -o '"status":"healthy"' || echo "unhealthy")
if [[ $API_HEALTH == *"healthy"* ]]; then
    echo "✅ API health check passed"
else
    echo "❌ API health check failed"
    echo "📋 Checking logs..."
    docker-compose logs --tail=20 api
fi

# Display startup summary
echo ""
echo "🎉 Financial Wisdom Platform Started!"
echo ""
echo "📋 Service Status:"
echo "   🔗 API:           http://localhost:8000"
echo "   📚 API Docs:      http://localhost:8000/docs"
echo "   💾 PostgreSQL:    localhost:5432"
echo "   🔄 Redis:         localhost:6379"
echo "   🔍 Elasticsearch: http://localhost:9200"

if [ "$1" = "--with-monitoring" ]; then
    echo "   📊 Prometheus:    http://localhost:9090"
    echo "   📈 Grafana:       http://localhost:3000 (admin/admin)"
fi

echo ""
echo "🛠️  Useful commands:"
echo "   View logs:        docker-compose logs -f"
echo "   Stop services:    docker-compose down"
echo "   Restart:          docker-compose restart"
echo "   Run migrations:   docker-compose run --rm api alembic upgrade head"
echo ""

# Show recent logs
echo "📋 Recent API logs:"
docker-compose logs --tail=10 api

echo "✨ Platform is ready for financial wisdom generation!"