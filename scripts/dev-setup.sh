#!/bin/bash

# Local Development Setup Script (without Docker)

set -e

echo "🚀 Setting up Financial Wisdom Platform for Local Development..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Using Python $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if PostgreSQL is available (for local development)
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL found"
    echo "📋 You can use local PostgreSQL or we'll create a SQLite fallback"
else
    echo "⚠️  PostgreSQL not found. Will use SQLite for development"
    # Update .env for SQLite
    sed -i.bak 's|postgresql+asyncpg://.*|sqlite+aiosqlite:///./financial_wisdom.db|g' .env
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs data

echo "✅ Local development environment ready!"
echo ""
echo "🚀 To start the development server:"
echo "   source venv/bin/activate"
echo "   uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "📚 API will be available at: http://localhost:8000"
echo "📖 Documentation: http://localhost:8000/docs"