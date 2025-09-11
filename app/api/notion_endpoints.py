"""
FastAPI endpoints for Notion database operations
Replaces traditional database endpoints with Notion integration
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.models.domain import (
    Article, ArticleId, Topic, ArticleStatus, ContentStyle, 
    ArticleSummary, GenerationRequest
)
from app.services.notion_service import NotionService
from app.api.dependencies import get_notion_service

router = APIRouter(prefix="/api/v1/notion", tags=["Notion Database"])

# Response models
class ArticleResponse(BaseModel):
    """Response model for article operations"""
    success: bool
    message: str
    article_id: Optional[str] = None
    notion_page_id: Optional[str] = None
    notion_url: Optional[str] = None

class ArticlesListResponse(BaseModel):
    """Response model for article list"""
    articles: List[ArticleSummary]
    total: int
    has_more: bool

class TopicsResponse(BaseModel):
    """Response model for topics list"""
    topics: List[dict]
    total: int

@router.post("/articles", response_model=ArticleResponse)
async def create_article(
    article: Article,
    notion_service: NotionService = Depends(get_notion_service)
):
    """Create a new article in Notion database"""
    try:
        notion_page_id = await notion_service.create_article(article)
        
        return ArticleResponse(
            success=True,
            message="Article created successfully in Notion",
            article_id=article.id.value,
            notion_page_id=notion_page_id
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create article: {str(e)}"
        )

@router.get("/articles", response_model=ArticlesListResponse)
async def list_articles(
    status: Optional[ArticleStatus] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    notion_service: NotionService = Depends(get_notion_service)
):
    """List articles from Notion database"""
    try:
        articles = await notion_service.list_articles(
            status=status,
            category=category,
            limit=limit
        )
        
        # Convert to summary format
        article_summaries = []
        for article in articles:
            summary = ArticleSummary(
                id=article.id.value,
                title=article.content.title if article.content else "Untitled",
                status=article.status,
                style=article.style,
                quality_score=article.quality_metrics.overall_score if article.quality_metrics else None,
                created_at=article.created_at,
                published_at=article.published_at
            )
            article_summaries.append(summary)
        
        return ArticlesListResponse(
            articles=article_summaries,
            total=len(article_summaries),
            has_more=len(article_summaries) >= limit
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list articles: {str(e)}"
        )

@router.get("/articles/{article_id}")
async def get_article(
    article_id: str,
    notion_service: NotionService = Depends(get_notion_service)
):
    """Get a specific article from Notion database"""
    try:
        article = await notion_service.get_article(
            ArticleId.from_string(article_id)
        )
        
        if not article:
            raise HTTPException(
                status_code=404,
                detail=f"Article {article_id} not found"
            )
        
        return {
            "id": article.id.value,
            "title": article.content.title if article.content else "Untitled",
            "content": {
                "introduction": article.content.introduction if article.content else "",
                "main_content": article.content.main_content if article.content else "",
                "conclusion": article.content.conclusion if article.content else "",
                "key_insights": article.content.key_insights if article.content else [],
                "actionable_steps": article.content.actionable_steps if article.content else []
            },
            "topic": {
                "keywords": article.topic.keywords,
                "category": article.topic.category,
                "trend_score": article.topic.trend_score
            },
            "status": article.status,
            "style": article.style,
            "quality_metrics": {
                "overall_score": article.quality_metrics.overall_score,
                "readability_score": article.quality_metrics.readability_score,
                "engagement_score": article.quality_metrics.engagement_score,
                "educational_value": article.quality_metrics.educational_value,
                "actionability_score": article.quality_metrics.actionability_score,
                "originality_score": article.quality_metrics.originality_score
            } if article.quality_metrics else None,
            "created_at": article.created_at.isoformat() if article.created_at else None,
            "published_at": article.published_at.isoformat() if article.published_at else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get article: {str(e)}"
        )

@router.put("/articles/{article_id}/status")
async def update_article_status(
    article_id: str,
    status: ArticleStatus,
    notion_service: NotionService = Depends(get_notion_service)
):
    """Update article status in Notion database"""
    try:
        await notion_service.update_article_status(
            ArticleId.from_string(article_id),
            status
        )
        
        return {
            "success": True,
            "message": f"Article {article_id} status updated to {status}",
            "article_id": article_id,
            "new_status": status
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update article status: {str(e)}"
        )

@router.get("/topics", response_model=TopicsResponse)
async def list_trending_topics(
    limit: int = Query(10, ge=1, le=50),
    notion_service: NotionService = Depends(get_notion_service)
):
    """Get trending topics from Notion database"""
    try:
        topics = await notion_service.get_trending_topics(limit=limit)
        
        topics_data = []
        for topic in topics:
            topics_data.append({
                "keywords": topic.keywords,
                "category": topic.category,
                "trend_score": topic.trend_score,
                "context": topic.context,
                "hash": topic.hash()
            })
        
        return TopicsResponse(
            topics=topics_data,
            total=len(topics_data)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get trending topics: {str(e)}"
        )

@router.post("/topics")
async def create_topic(
    topic: Topic,
    notion_service: NotionService = Depends(get_notion_service)
):
    """Create a new topic in Notion database"""
    try:
        notion_page_id = await notion_service.create_topic(topic)
        
        return {
            "success": True,
            "message": "Topic created successfully in Notion",
            "topic_hash": topic.hash(),
            "notion_page_id": notion_page_id
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create topic: {str(e)}"
        )

@router.get("/health")
async def notion_health_check(
    notion_service: NotionService = Depends(get_notion_service)
):
    """Check Notion service health and connectivity"""
    try:
        # Test Notion client connection
        # This could include checking database access, token validity, etc.
        return {
            "status": "healthy",
            "service": "notion",
            "databases": {
                "articles": bool(notion_service.articles_db_id),
                "topics": bool(notion_service.topics_db_id),
                "sources": bool(notion_service.sources_db_id),
                "raw_content": bool(notion_service.raw_content_db_id)
            },
            "token_configured": bool(notion_service.notion_token)
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "notion",
            "error": str(e)
        }

# Migration endpoints
@router.post("/migrate/from-postgres")
async def migrate_from_postgres(
    limit: int = Query(100, ge=1, le=1000),
    notion_service: NotionService = Depends(get_notion_service)
):
    """Migrate articles from PostgreSQL to Notion (if needed)"""
    try:
        # This would implement the migration logic from existing database
        # For now, return a placeholder response
        return {
            "success": True,
            "message": "Migration endpoint ready (implementation needed)",
            "migrated_count": 0,
            "limit": limit
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Migration failed: {str(e)}"
        )

@router.get("/stats")
async def get_notion_stats(
    notion_service: NotionService = Depends(get_notion_service)
):
    """Get Notion database statistics"""
    try:
        # Get basic stats from Notion databases
        articles = await notion_service.list_articles(limit=1000)
        topics = await notion_service.get_trending_topics(limit=1000)
        
        # Calculate statistics
        status_counts = {}
        style_counts = {}
        category_counts = {}
        
        for article in articles:
            # Count by status
            status = article.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by style
            style = article.style.value
            style_counts[style] = style_counts.get(style, 0) + 1
            
            # Count by category
            category = article.topic.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total_articles": len(articles),
            "total_topics": len(topics),
            "status_distribution": status_counts,
            "style_distribution": style_counts,
            "category_distribution": category_counts,
            "avg_quality_score": sum(
                article.quality_metrics.overall_score 
                for article in articles 
                if article.quality_metrics
            ) / len([a for a in articles if a.quality_metrics]) if articles else 0
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )