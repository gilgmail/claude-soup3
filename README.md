# Financial Wisdom Platform 💰🧠

A comprehensive financial wisdom content generation platform that automatically creates daily financial insights, motivational content, and practical guidance using AI-powered analysis of trending topics and curated financial knowledge.

## 🎯 Features

### 🤖 AI-Powered Content Generation
- Daily automated financial wisdom articles
- Multiple content styles: motivational, philosophical, practical, historical
- Quality assessment with 8.0+ scoring threshold
- Cost-optimized AI usage with intelligent caching (70% cost reduction)

### 📊 Multi-Source Data Collection
- Automated web scraping from financial websites (Investopedia, Bloomberg, CNBC)
- Trending topic analysis and identification
- Social media integration (planned)
- RSS feed monitoring

### 🔍 Intelligent Knowledge Management
- Elasticsearch-powered search and indexing
- Content similarity detection to avoid duplication
- Multi-layer caching strategy (Redis + in-memory)
- Semantic content organization

### 🏗️ Enterprise Architecture
- Domain-Driven Design (DDD) principles
- RESTful API with FastAPI
- PostgreSQL with Alembic migrations
- Docker containerization with Kubernetes support
- Comprehensive monitoring and logging

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- AI API Keys (Anthropic Claude & OpenAI)

### 1. Clone and Configure
```bash
git clone <repository-url>
cd financial-wisdom-platform
cp .env.example .env
```

### 2. Set API Keys
Edit `.env` file and add your AI service API keys:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Start Platform
```bash
./scripts/start.sh
```

### 4. Access Services
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Monitoring** (optional): `./scripts/start.sh --with-monitoring`
  - Prometheus: http://localhost:9090
  - Grafana: http://localhost:3000 (admin/admin)

## 📋 API Endpoints

### Content Generation
```http
POST /api/v1/articles/generate
{
  "topic_keywords": ["investment", "compound interest"],
  "category": "finance", 
  "style": "motivational_finance"
}
```

### Content Retrieval
```http
GET /api/v1/articles/{article_id}
GET /api/v1/articles?category=finance&limit=10
```

### Data Collection
```http
POST /api/v1/sources/collect
GET /api/v1/sources/trending?days=7&limit=10
```

### Knowledge Search
```http
GET /api/v1/knowledge/search?q=retirement planning&limit=5
```

### Workflow Management
```http
POST /api/v1/workflow/generate-now
GET /api/v1/workflow/stats
```

## 🏛️ Architecture

### Domain-Driven Design Structure
```
app/
├── core/           # Configuration, logging, monitoring
├── models/         # Domain models and database schemas
├── services/       # Business logic services
│   ├── data_collection.py     # Multi-source data gathering
│   ├── ai_content_generation.py # AI content creation
│   ├── knowledge_base.py      # Search and indexing
│   ├── content_workflow.py    # Orchestration
│   └── cache.py              # Multi-layer caching
├── api/           # REST API endpoints
└── workers/       # Background task processors
```

### Key Components

**Data Collection Service**
- Web scraping with rate limiting
- Multiple source strategies (web, API, social)
- Content deduplication and keyword extraction

**AI Content Generation Service**
- Multi-model approach (Claude-3 + GPT-3.5)
- Template-based generation for cost efficiency
- Quality assessment and regeneration

**Knowledge Base Service**
- Elasticsearch integration
- Vector similarity search
- Multi-layer caching (Redis + memory)

**Content Workflow**
- Daily generation pipeline
- Topic trend analysis
- Quality assurance gates
- Cost optimization

## 💰 Cost Optimization

### Intelligent Caching Strategy
- **Content Reuse**: 70% cost reduction through intelligent content adaptation
- **Multi-Layer Caching**: Memory (5min) → Redis (1hr) → Database
- **Template System**: Pre-structured content reduces generation needs
- **Model Selection**: Use cost-efficient models for supporting tasks

### Estimated Monthly Costs
- **Infrastructure**: ~$370/month
- **AI Services**: ~$130/month (optimized)
- **Total**: ~$500/month
- **Break-even**: ~1,000 active users

## 📊 Monitoring & Observability

### Metrics Tracked
- API request rates and response times
- Content generation costs and quality scores
- Cache hit rates and cost savings
- System resource usage
- AI service usage and costs

### Prometheus Metrics
```
api_requests_total
content_generation_duration_seconds
ai_service_cost_total
cache_hit_rate_percent
```

### Structured Logging
All events logged with structured JSON format:
```json
{
  "timestamp": "2025-09-07T09:00:00Z",
  "event_type": "content_generation",
  "article_id": "uuid",
  "quality_score": 8.5,
  "cost_estimate": 0.015,
  "cache_hit": false
}
```

## 🔧 Development

### Local Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start local services
docker-compose up -d postgres redis elasticsearch

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.api.main:app --reload
```

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Type checking
mypy app/

# Code formatting
black app/
isort app/
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🔐 Security

### Security Features
- Input validation with Pydantic
- Rate limiting on content generation endpoints
- Secure credential management
- Non-root container execution
- HTTPS support with SSL termination

### Security Best Practices
- API keys stored in environment variables
- Database credentials rotation
- Regular dependency updates
- Container image scanning

## 📈 Scaling

### Horizontal Scaling
- Stateless API design
- Separate worker processes for background tasks
- Database connection pooling
- Redis cluster support

### Performance Optimization
- Async/await throughout
- Connection pooling
- Query optimization with indexes
- CDN for static assets

### Kubernetes Deployment
```yaml
# Provided in k8s/ directory
- Deployment manifests
- Service definitions
- ConfigMaps and Secrets
- HPA (Horizontal Pod Autoscaling)
```

## 🤝 Contributing

### Development Workflow
1. Fork repository
2. Create feature branch
3. Follow code style (Black, isort, mypy)
4. Add tests for new functionality
5. Update documentation
6. Submit pull request

### Code Standards
- Type hints required
- Docstrings for public methods
- Test coverage >80%
- Follow DDD principles
- Structured logging

## 📚 Documentation

### API Documentation
- Interactive Swagger UI: `/docs`
- OpenAPI spec: `/openapi.json`
- ReDoc interface: `/redoc`

### Architecture Documentation
- [Domain Models](docs/domain-models.md)
- [API Reference](docs/api-reference.md)
- [Deployment Guide](docs/deployment.md)
- [Cost Optimization](docs/cost-optimization.md)

## 🐛 Troubleshooting

### Common Issues

**Services not starting**
```bash
# Check Docker logs
docker-compose logs api

# Verify environment variables
cat .env | grep -E "(API_KEY|DB_URL)"

# Check service health
curl http://localhost:8000/health
```

**High AI costs**
```bash
# Check cost metrics
curl http://localhost:8000/api/v1/workflow/stats

# Review cache hit rates
curl http://localhost:8000/api/v1/status
```

**Database connection issues**
```bash
# Reset database
docker-compose down
docker volume rm financial-wisdom_postgres_data
docker-compose up -d postgres
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with FastAPI, PostgreSQL, Redis, and Elasticsearch
- AI models: Anthropic Claude-3 and OpenAI GPT-3.5
- Financial data sources: Investopedia, Bloomberg, CNBC
- Monitoring: Prometheus and Grafana

---

**Financial Wisdom Platform** - Automated financial wisdom for the modern world 💰✨