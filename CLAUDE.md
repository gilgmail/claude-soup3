# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Financial Wisdom Platform - An AI-powered content generation platform that creates daily financial insights using web scraping, multi-source data collection, and AI content generation. Built with Domain-Driven Design (DDD) principles.

## Development Commands

### Quick Start (Docker)
```bash
# Start entire platform with Docker
./scripts/start.sh

# Start with monitoring (Prometheus + Grafana)
./scripts/start.sh --with-monitoring

# Stop all services
docker-compose down
```

### Local Development Setup
```bash
# Setup virtual environment and dependencies
./scripts/dev-setup.sh

# Activate virtual environment
source venv/bin/activate

# Start development server (without Docker)
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Database Operations
```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Rollback migration
alembic downgrade -1

# With Docker
docker-compose run --rm api alembic upgrade head
```

### Code Quality & Testing
```bash
# Format code
black app/
isort app/

# Type checking
mypy app/

# Run tests (pytest installed but no test files exist yet)
pytest
pytest --cov=app
```

## Architecture Overview

### Domain-Driven Design Structure
The application follows DDD principles with clear service boundaries:

- **`app/core/`** - Configuration, logging, monitoring infrastructure
- **`app/models/`** - Domain models (`domain.py`) and database schemas (`database.py`)
- **`app/services/`** - Core business logic services
- **`app/api/`** - FastAPI REST endpoints and dependencies

### Key Services
1. **Data Collection Service** (`data_collection.py`) - Multi-source web scraping (Investopedia, Bloomberg, CNBC)
2. **AI Content Generation** (`ai_content_generation.py`) - Uses Anthropic Claude & OpenAI with quality assessment
3. **Knowledge Base Service** (`knowledge_base.py`) - Elasticsearch-powered search and indexing
4. **Content Workflow** (`content_workflow.py`) - Orchestrates the entire content generation pipeline
5. **Cache Service** (`cache.py`) - Multi-layer caching (Redis + in-memory) for 70% cost reduction

### Configuration
- **Environment**: All configuration via `.env` file (copy from `.env.example`)
- **Required API Keys**: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`
- **Code Style**: Black (100 char line length), isort, mypy with strict typing

### Technology Stack
- **API**: FastAPI with async/await
- **Database**: PostgreSQL + SQLAlchemy with Alembic migrations
- **Caching**: Redis + aioredis
- **Search**: Elasticsearch
- **AI**: Anthropic Claude-3 + OpenAI GPT-3.5
- **Web Scraping**: BeautifulSoup4, Selenium, Scrapy
- **Monitoring**: Prometheus + Grafana + structured logging (structlog)

### Data Flow
1. **Data Collection** → Scrape financial websites for trending topics
2. **Knowledge Base** → Index and search existing content to avoid duplication
3. **AI Generation** → Create articles using Claude/OpenAI with quality scoring (8.0+ threshold)
4. **Workflow Orchestration** → Daily automated pipeline with cost optimization

### Key Patterns
- All services use dependency injection via FastAPI `Depends()`
- Async/await throughout for performance
- Structured logging with correlation IDs
- Quality gates with regeneration on low scores
- Cost optimization through intelligent caching and template reuse

### Service Endpoints
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health
- **Monitoring**: http://localhost:9090 (Prometheus), http://localhost:3000 (Grafana)

### Development Notes
- No test files exist yet - tests should be added in `tests/` directory
- Uses Poetry for dependency management (`pyproject.toml`) but also has `requirements.txt`
- Virtual environment in `venv/` directory
- Docker setup supports both development and production targets