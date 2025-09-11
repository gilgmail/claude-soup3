"""Main FastAPI application with all endpoints."""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
import structlog

from app.core.config import settings
from app.api.dependencies import (
    get_knowledge_base, get_content_workflow, get_data_collector
)
from app.api.simple_notion_endpoints import router as notion_router
from app.api.notion_web_endpoints import router as web_router
from app.models.domain import (
    GenerationRequest, ArticleSummary, TopicSummary, ContentStyle
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Financial Wisdom Platform API")
    
    # Initialize services
    try:
        knowledge_base = await get_knowledge_base()
        await knowledge_base.initialize()
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error("Service initialization failed", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Financial Wisdom Platform API")


# Create FastAPI app
app = FastAPI(
    title="Financial Wisdom Platform",
    description="API for automated financial wisdom content generation",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Notion endpoints
app.include_router(notion_router)
app.include_router(web_router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve main HTML file at root
from fastapi.responses import FileResponse
import os

@app.get("/")
async def serve_index():
    """Serve the main HTML file."""
    return FileResponse("static/index.html")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "financial-wisdom-platform"}


# Article generation endpoints
@app.post("/api/v1/articles/generate", response_model=Dict[str, Any])
async def generate_article(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    workflow = Depends(get_content_workflow)
):
    """Generate a new financial wisdom article."""
    try:
        from app.models.domain import Topic
        
        # Create topic from request
        topic = Topic(
            keywords=request.topic_keywords,
            category=request.category,
            trend_score=5.0,  # Default trend score
            context={'user_requested': True}
        )
        
        # Generate content asynchronously
        result = await workflow.run_daily_generation()
        
        if result.success and result.article:
            return {
                "article_id": result.article.id.value,
                "status": result.article.status.value,
                "title": result.article.content.title if result.article.content else "Generating...",
                "quality_score": result.article.quality_metrics.overall_score if result.article.quality_metrics else None,
                "estimated_cost": result.cost_estimate,
                "metrics": result.metrics
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Content generation failed: {result.error_message}"
            )
    
    except Exception as e:
        logger.error("Article generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/articles/{article_id}", response_model=Dict[str, Any])
async def get_article(
    article_id: str,
    knowledge_base = Depends(get_knowledge_base)
):
    """Get a specific article by ID."""
    try:
        # Search for article in knowledge base
        results = await knowledge_base.search(
            query="*",
            filters={"article_id": article_id},
            limit=1
        )
        
        if not results:
            raise HTTPException(status_code=404, detail="Article not found")
        
        result = results[0]
        return {
            "id": result.content_id,
            "title": result.title,
            "content": result.content,
            "created_at": result.created_at.isoformat(),
            "source_info": result.source_info,
            "metadata": result.metadata
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get article", article_id=article_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/articles", response_model=List[ArticleSummary])
async def list_articles(
    limit: int = Query(default=10, le=100),
    offset: int = Query(default=0, ge=0),
    category: Optional[str] = Query(default=None),
    style: Optional[ContentStyle] = Query(default=None),
    knowledge_base = Depends(get_knowledge_base)
):
    """List articles with pagination and filtering."""
    try:
        filters = {}
        if category:
            filters["topic_category"] = category
        if style:
            filters["content_style"] = style.value
        
        # Search with pagination
        results = await knowledge_base.search(
            query="*",
            filters=filters,
            limit=limit
        )
        
        # Convert to ArticleSummary (simplified)
        articles = []
        for result in results[offset:offset+limit]:
            articles.append({
                "id": result.content_id,
                "title": result.title,
                "status": "published",  # Assume published if in KB
                "style": result.metadata.get("content_style", "motivational_finance"),
                "quality_score": result.metadata.get("quality_score"),
                "created_at": result.created_at,
                "published_at": result.created_at
            })
        
        return articles
    
    except Exception as e:
        logger.error("Failed to list articles", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Data collection endpoints
@app.post("/api/v1/sources/collect", response_model=Dict[str, Any])
async def trigger_data_collection(
    background_tasks: BackgroundTasks,
    data_collector = Depends(get_data_collector)
):
    """Trigger data collection from all sources."""
    try:
        # Run collection in background
        background_tasks.add_task(data_collector.collect_from_all_sources)
        
        return {
            "status": "started",
            "message": "Data collection started in background"
        }
    
    except Exception as e:
        logger.error("Failed to start data collection", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sources/trending", response_model=List[TopicSummary])
async def get_trending_topics(
    limit: int = Query(default=10, le=50),
    days: int = Query(default=7, le=30),
    knowledge_base = Depends(get_knowledge_base)
):
    """Get trending financial topics."""
    try:
        topics = await knowledge_base.get_trending_topics(days=days, limit=limit)
        
        return [
            {
                "keywords": topic.keywords,
                "category": topic.category,
                "trend_score": topic.trend_score
            }
            for topic in topics
        ]
    
    except Exception as e:
        logger.error("Failed to get trending topics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Knowledge management endpoints
@app.get("/api/v1/knowledge/search", response_model=Dict[str, Any])
async def search_knowledge_base(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = Query(default=None),
    content_type: Optional[str] = Query(default=None, regex="^(raw|processed)$"),
    limit: int = Query(default=10, le=50),
    knowledge_base = Depends(get_knowledge_base)
):
    """Search the knowledge base."""
    try:
        filters = {}
        if category:
            filters["category"] = category
        if content_type:
            filters["content_type"] = content_type
        
        results = await knowledge_base.search(
            query=q,
            filters=filters,
            limit=limit
        )
        
        return {
            "query": q,
            "total_results": len(results),
            "results": [
                {
                    "id": result.content_id,
                    "title": result.title,
                    "content": result.content[:500] + "..." if len(result.content) > 500 else result.content,
                    "relevance_score": result.relevance_score,
                    "content_type": result.content_type,
                    "created_at": result.created_at.isoformat(),
                    "source_info": result.source_info
                }
                for result in results
            ]
        }
    
    except Exception as e:
        logger.error("Knowledge base search failed", query=q, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Workflow management endpoints
@app.post("/api/v1/workflow/generate-now", response_model=Dict[str, Any])
async def generate_content_now(
    workflow = Depends(get_content_workflow)
):
    """Trigger immediate content generation."""
    try:
        result = await workflow.run_daily_generation()
        
        if result.success:
            return {
                "status": "success",
                "article_id": result.article.id.value if result.article else None,
                "quality_score": result.article.quality_metrics.overall_score if result.article and result.article.quality_metrics else None,
                "cost_estimate": result.cost_estimate,
                "metrics": result.metrics
            }
        else:
            return {
                "status": "failed",
                "error": result.error_message,
                "metrics": result.metrics
            }
    
    except Exception as e:
        logger.error("Manual content generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/workflow/stats", response_model=Dict[str, Any])
async def get_workflow_stats(
    workflow = Depends(get_content_workflow)
):
    """Get workflow statistics and performance metrics."""
    try:
        return workflow.get_workflow_stats()
    
    except Exception as e:
        logger.error("Failed to get workflow stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# System status and monitoring endpoints
@app.get("/api/v1/status", response_model=Dict[str, Any])
async def get_system_status(
    knowledge_base = Depends(get_knowledge_base)
):
    """Get system status and statistics."""
    try:
        kb_stats = await knowledge_base.get_stats()
        
        return {
            "status": "operational",
            "version": settings.version,
            "knowledge_base": kb_stats,
            "configuration": {
                "quality_threshold": settings.content.quality_threshold,
                "daily_generation_time": settings.content.daily_generation_time,
                "content_styles": settings.content.content_styles
            }
        }
    
    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "detail": "The requested resource was not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error("Internal server error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "An unexpected error occurred"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )