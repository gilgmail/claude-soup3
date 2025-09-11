"""
Notion Database Service
Replaces PostgreSQL with Notion as the primary database
"""

import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from notion_client import Client
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from app.models.domain import (
    Article, ArticleId, Topic, DataSource, RawContent, Content,
    QualityMetrics, ArticleStatus, ContentStyle, SourceType
)
from app.core.config import settings

logger = logging.getLogger(__name__)

class NotionService:
    """Notion database service for financial wisdom platform"""
    
    def __init__(self, notion_token: Optional[str] = None):
        self.notion_token = notion_token or settings.NOTION_TOKEN
        if not self.notion_token:
            raise ValueError("NOTION_TOKEN is required")
        
        self.client = Client(auth=self.notion_token)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Database IDs (set via environment or configuration)
        self.articles_db_id = settings.NOTION_ARTICLES_DB_ID
        self.topics_db_id = settings.NOTION_TOPICS_DB_ID
        self.sources_db_id = settings.NOTION_SOURCES_DB_ID
        self.raw_content_db_id = settings.NOTION_RAW_CONTENT_DB_ID
    
    async def create_article(self, article: Article) -> str:
        """Create article in Notion database"""
        loop = asyncio.get_event_loop()
        
        properties = {
            "Title": {
                "title": [{"text": {"content": article.content.title if article.content else "Untitled"}}]
            },
            "Article ID": {
                "rich_text": [{"text": {"content": article.id.value}}]
            },
            "Status": {
                "select": {"name": self._map_status(article.status)}
            },
            "Content Style": {
                "select": {"name": self._map_content_style(article.style)}
            },
            "Topic Category": {
                "select": {"name": article.topic.category}
            },
            "Keywords": {
                "multi_select": [{"name": kw} for kw in article.topic.keywords[:10]]
            },
            "Trend Score": {
                "number": article.topic.trend_score
            },
            "Created At": {
                "date": {"start": article.created_at.isoformat()}
            }
        }
        
        # Add quality metrics if available
        if article.quality_metrics:
            properties.update({
                "Overall Score": {"number": round(article.quality_metrics.overall_score, 2)},
                "Readability": {"number": round(article.quality_metrics.readability_score, 2)},
                "Engagement": {"number": round(article.quality_metrics.engagement_score, 2)},
                "Educational Value": {"number": round(article.quality_metrics.educational_value, 2)},
                "Actionability": {"number": round(article.quality_metrics.actionability_score, 2)},
                "Originality": {"number": round(article.quality_metrics.originality_score, 2)}
            })
        
        # Add content details if available
        if article.content:
            properties.update({
                "Word Count": {"number": article.content.word_count()},
                "Insights Count": {"number": len(article.content.key_insights)},
                "Action Steps": {"number": len(article.content.actionable_steps)}
            })
        
        # Add published date if published
        if article.published_at:
            properties["Published At"] = {
                "date": {"start": article.published_at.isoformat()}
            }
        
        def create_page():
            return self.client.pages.create(
                parent={"database_id": self.articles_db_id},
                properties=properties
            )
        
        page = await loop.run_in_executor(self.executor, create_page)
        page_id = page["id"]
        
        # Add content blocks if available
        if article.content:
            await self._add_content_blocks(page_id, article.content)
        
        logger.info(f"Created article in Notion: {article.id.value}")
        return page_id
    
    async def _add_content_blocks(self, page_id: str, content: Content):
        """Add content blocks to Notion page"""
        blocks = []
        
        # Introduction
        if content.introduction:
            blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "Introduction"}}]}
                },
                {
                    "object": "block", 
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": content.introduction}}]}
                }
            ])
        
        # Main content
        if content.main_content:
            blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2", 
                    "heading_2": {"rich_text": [{"text": {"content": "Main Content"}}]}
                },
                *self._convert_text_to_blocks(content.main_content)
            ])
        
        # Key insights
        if content.key_insights:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "Key Insights"}}]}
            })
            for insight in content.key_insights:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"text": {"content": insight}}]}
                })
        
        # Actionable steps
        if content.actionable_steps:
            blocks.append({
                "object": "block",
                "type": "heading_2", 
                "heading_2": {"rich_text": [{"text": {"content": "Action Steps"}}]}
            })
            for i, step in enumerate(content.actionable_steps, 1):
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": [{"text": {"content": f"{step}"}}]}
                })
        
        # Conclusion
        if content.conclusion:
            blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "Conclusion"}}]}
                },
                {
                    "object": "block",
                    "type": "paragraph", 
                    "paragraph": {"rich_text": [{"text": {"content": content.conclusion}}]}
                }
            ])
        
        # Add blocks in chunks (Notion API limit)
        loop = asyncio.get_event_loop()
        chunk_size = 100
        
        for i in range(0, len(blocks), chunk_size):
            chunk = blocks[i:i + chunk_size]
            
            def append_blocks():
                return self.client.blocks.children.append(
                    block_id=page_id,
                    children=chunk
                )
            
            await loop.run_in_executor(self.executor, append_blocks)
    
    def _convert_text_to_blocks(self, text: str) -> List[Dict]:
        """Convert text to Notion blocks"""
        blocks = []
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            if paragraph.strip():
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": paragraph.strip()}}]}
                })
        
        return blocks
    
    async def get_article(self, article_id: ArticleId) -> Optional[Article]:
        """Retrieve article from Notion"""
        loop = asyncio.get_event_loop()
        
        # Query by Article ID property
        def query_articles():
            return self.client.databases.query(
                database_id=self.articles_db_id,
                filter={
                    "property": "Article ID",
                    "rich_text": {"equals": article_id.value}
                }
            )
        
        result = await loop.run_in_executor(self.executor, query_articles)
        
        if not result["results"]:
            return None
        
        page = result["results"][0]
        return await self._convert_notion_page_to_article(page)
    
    async def list_articles(
        self, 
        status: Optional[ArticleStatus] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Article]:
        """List articles from Notion database"""
        loop = asyncio.get_event_loop()
        
        # Build filters
        filters = []
        
        if status:
            filters.append({
                "property": "Status",
                "select": {"equals": self._map_status(status)}
            })
        
        if category:
            filters.append({
                "property": "Topic Category", 
                "select": {"equals": category}
            })
        
        query_filter = None
        if len(filters) == 1:
            query_filter = filters[0]
        elif len(filters) > 1:
            query_filter = {"and": filters}
        
        def query_articles():
            params = {
                "database_id": self.articles_db_id,
                "page_size": limit,
                "sorts": [{"property": "Created At", "direction": "descending"}]
            }
            if query_filter:
                params["filter"] = query_filter
            return self.client.databases.query(**params)
        
        result = await loop.run_in_executor(self.executor, query_articles)
        
        articles = []
        for page in result["results"]:
            article = await self._convert_notion_page_to_article(page)
            if article:
                articles.append(article)
        
        return articles
    
    async def update_article_status(self, article_id: ArticleId, status: ArticleStatus):
        """Update article status in Notion"""
        loop = asyncio.get_event_loop()
        
        # First find the page
        article = await self.get_article(article_id)
        if not article:
            raise ValueError(f"Article {article_id.value} not found")
        
        # Get the Notion page ID
        def query_page():
            return self.client.databases.query(
                database_id=self.articles_db_id,
                filter={
                    "property": "Article ID",
                    "rich_text": {"equals": article_id.value}
                }
            )
        
        result = await loop.run_in_executor(self.executor, query_page)
        if not result["results"]:
            raise ValueError(f"Article {article_id.value} not found in Notion")
        
        page_id = result["results"][0]["id"]
        
        properties = {
            "Status": {"select": {"name": self._map_status(status)}}
        }
        
        if status == ArticleStatus.PUBLISHED:
            properties["Published At"] = {
                "date": {"start": datetime.now(timezone.utc).isoformat()}
            }
        
        def update_page():
            return self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
        
        await loop.run_in_executor(self.executor, update_page)
        logger.info(f"Updated article {article_id.value} status to {status}")
    
    async def create_topic(self, topic: Topic) -> str:
        """Create topic in Notion database"""
        loop = asyncio.get_event_loop()
        
        properties = {
            "Keywords": {
                "title": [{"text": {"content": ", ".join(topic.keywords)}}]
            },
            "Category": {
                "select": {"name": topic.category}
            },
            "Trend Score": {
                "number": topic.trend_score
            },
            "Topic Hash": {
                "rich_text": [{"text": {"content": topic.hash()}}]
            },
            "Context": {
                "rich_text": [{"text": {"content": str(topic.context)}}]
            },
            "Created At": {
                "date": {"start": datetime.now(timezone.utc).isoformat()}
            }
        }
        
        def create_page():
            return self.client.pages.create(
                parent={"database_id": self.topics_db_id},
                properties=properties
            )
        
        page = await loop.run_in_executor(self.executor, create_page)
        logger.info(f"Created topic in Notion: {topic.hash()}")
        return page["id"]
    
    async def get_trending_topics(self, limit: int = 10) -> List[Topic]:
        """Get trending topics from Notion"""
        loop = asyncio.get_event_loop()
        
        def query_topics():
            return self.client.databases.query(
                database_id=self.topics_db_id,
                sorts=[{"property": "Trend Score", "direction": "descending"}],
                page_size=limit
            )
        
        result = await loop.run_in_executor(self.executor, query_topics)
        
        topics = []
        for page in result["results"]:
            topic = self._convert_notion_page_to_topic(page)
            if topic:
                topics.append(topic)
        
        return topics
    
    async def _convert_notion_page_to_article(self, page: Dict) -> Optional[Article]:
        """Convert Notion page to Article domain object"""
        try:
            props = page["properties"]
            
            # Extract basic properties
            article_id = ArticleId.from_string(
                self._extract_rich_text(props.get("Article ID", {}))
            )
            
            title = self._extract_title(props.get("Title", {}))
            status = self._parse_status(self._extract_select(props.get("Status", {})))
            style = self._parse_content_style(self._extract_select(props.get("Content Style", {})))
            
            # Extract topic information
            category = self._extract_select(props.get("Topic Category", {}))
            keywords = [item["name"] for item in props.get("Keywords", {}).get("multi_select", [])]
            trend_score = props.get("Trend Score", {}).get("number", 0.0)
            
            topic = Topic(
                keywords=keywords,
                category=category,
                trend_score=trend_score
            )
            
            # Extract timestamps
            created_at = self._extract_date(props.get("Created At", {}))
            published_at = self._extract_date(props.get("Published At", {}))
            
            # Extract quality metrics if available
            quality_metrics = None
            overall_score = props.get("Overall Score", {}).get("number")
            if overall_score:
                quality_metrics = QualityMetrics(
                    readability_score=props.get("Readability", {}).get("number", 0.0),
                    engagement_score=props.get("Engagement", {}).get("number", 0.0),
                    educational_value=props.get("Educational Value", {}).get("number", 0.0),
                    actionability_score=props.get("Actionability", {}).get("number", 0.0),
                    originality_score=props.get("Originality", {}).get("number", 0.0)
                )
            
            # Create minimal content object (full content would require additional API calls)
            content = Content(
                title=title,
                introduction="",
                main_content="",
                conclusion="",
                key_insights=[],
                actionable_steps=[]
            ) if title else None
            
            article = Article(
                id=article_id,
                topic=topic,
                content=content,
                sources=[],  # Would need to be populated from relationships
                status=status,
                style=style,
                quality_metrics=quality_metrics,
                created_at=created_at,
                published_at=published_at
            )
            
            return article
            
        except Exception as e:
            logger.error(f"Error converting Notion page to Article: {e}")
            return None
    
    def _convert_notion_page_to_topic(self, page: Dict) -> Optional[Topic]:
        """Convert Notion page to Topic domain object"""
        try:
            props = page["properties"]
            
            keywords_text = self._extract_title(props.get("Keywords", {}))
            keywords = [kw.strip() for kw in keywords_text.split(",")]
            
            category = self._extract_select(props.get("Category", {}))
            trend_score = props.get("Trend Score", {}).get("number", 0.0)
            
            context_text = self._extract_rich_text(props.get("Context", {}))
            context = eval(context_text) if context_text else {}
            
            return Topic(
                keywords=keywords,
                category=category,
                trend_score=trend_score,
                context=context
            )
            
        except Exception as e:
            logger.error(f"Error converting Notion page to Topic: {e}")
            return None
    
    # Helper methods for data extraction and mapping
    def _extract_title(self, title_prop: Dict) -> str:
        title_list = title_prop.get("title", [])
        if title_list:
            return title_list[0].get("plain_text", "")
        return ""
    
    def _extract_rich_text(self, rich_text_prop: Dict) -> str:
        rich_text_list = rich_text_prop.get("rich_text", [])
        if rich_text_list:
            return rich_text_list[0].get("plain_text", "")
        return ""
    
    def _extract_select(self, select_prop: Dict) -> str:
        select_obj = select_prop.get("select")
        if select_obj:
            return select_obj.get("name", "")
        return ""
    
    def _extract_date(self, date_prop: Dict) -> Optional[datetime]:
        date_obj = date_prop.get("date")
        if date_obj:
            date_str = date_obj.get("start")
            if date_str:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return None
    
    def _map_status(self, status: ArticleStatus) -> str:
        return {
            ArticleStatus.DRAFT: "草稿",
            ArticleStatus.GENERATED: "已生成",
            ArticleStatus.QUALITY_CHECK: "質量檢查",
            ArticleStatus.APPROVED: "已批准",
            ArticleStatus.PUBLISHED: "已發布",
            ArticleStatus.ARCHIVED: "已存檔"
        }.get(status, "草稿")
    
    def _parse_status(self, status_str: str) -> ArticleStatus:
        mapping = {
            "草稿": ArticleStatus.DRAFT,
            "已生成": ArticleStatus.GENERATED,
            "質量檢查": ArticleStatus.QUALITY_CHECK,
            "已批准": ArticleStatus.APPROVED,
            "已發布": ArticleStatus.PUBLISHED,
            "已存檔": ArticleStatus.ARCHIVED
        }
        return mapping.get(status_str, ArticleStatus.DRAFT)
    
    def _map_content_style(self, style: ContentStyle) -> str:
        return {
            ContentStyle.MOTIVATIONAL_FINANCE: "勵志財經",
            ContentStyle.PHILOSOPHICAL_MONEY: "哲學思考", 
            ContentStyle.PRACTICAL_WISDOM: "實用智慧",
            ContentStyle.HISTORICAL_INSIGHTS: "歷史洞察"
        }.get(style, "實用智慧")
    
    def _parse_content_style(self, style_str: str) -> ContentStyle:
        mapping = {
            "勵志財經": ContentStyle.MOTIVATIONAL_FINANCE,
            "哲學思考": ContentStyle.PHILOSOPHICAL_MONEY,
            "實用智慧": ContentStyle.PRACTICAL_WISDOM,
            "歷史洞察": ContentStyle.HISTORICAL_INSIGHTS
        }
        return mapping.get(style_str, ContentStyle.PRACTICAL_WISDOM)

# Singleton pattern for service instance
_notion_service_instance = None

def get_notion_service() -> NotionService:
    """Get Notion service instance (singleton)"""
    global _notion_service_instance
    if _notion_service_instance is None:
        _notion_service_instance = NotionService()
    return _notion_service_instance