"""SQLAlchemy database models."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, String, Text, DateTime, Float, Integer, 
    Boolean, JSON, ForeignKey, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.domain import SourceType, ArticleStatus, ContentStyle

Base = declarative_base()


class DataSourceModel(Base):
    """Data source configuration table."""
    
    __tablename__ = "data_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    source_type = Column(String(50), nullable=False, index=True)
    base_url = Column(String(500), nullable=False)
    collection_config = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_collected_at = Column(DateTime, nullable=True, index=True)
    collection_count = Column(Integer, default=0, nullable=False)
    success_rate = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    raw_contents = relationship("RawContentModel", back_populates="source")
    
    def __repr__(self):
        return f"<DataSource(name='{self.name}', type='{self.source_type}')>"


class RawContentModel(Base):
    """Raw collected content table."""
    
    __tablename__ = "raw_content"
    
    id = Column(String(255), primary_key=True)  # Hash-based ID
    source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=False, index=True)
    title = Column(String(1000), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(2000), nullable=False)
    content_metadata = Column(JSON, nullable=False, default=dict)
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    processed = Column(Boolean, default=False, nullable=False, index=True)
    keywords = Column(JSON, nullable=True)  # Extracted keywords array
    financial_terms = Column(JSON, nullable=True)  # Financial terms array
    word_count = Column(Integer, nullable=True)
    
    # Relationships
    source = relationship("DataSourceModel", back_populates="raw_contents")
    
    # Indexes
    __table_args__ = (
        Index('idx_raw_content_source_date', 'source_id', 'collected_at'),
        Index('idx_raw_content_processed', 'processed', 'collected_at'),
    )
    
    def __repr__(self):
        return f"<RawContent(title='{self.title[:50]}...', source_id='{self.source_id}')>"


class ArticleModel(Base):
    """Processed articles table."""
    
    __tablename__ = "articles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content_json = Column(JSON, nullable=False)  # Full Content object as JSON
    topic_keywords = Column(JSON, nullable=False)  # Array of keywords
    topic_category = Column(String(100), nullable=False, index=True)
    topic_context = Column(JSON, nullable=True)
    content_style = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    quality_score = Column(Float, nullable=True, index=True)
    quality_metrics = Column(JSON, nullable=True)  # QualityMetrics as JSON
    source_materials = Column(JSON, nullable=True)  # Array of source IDs
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    published_at = Column(DateTime, nullable=True, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Content analysis fields
    word_count = Column(Integer, nullable=True)
    readability_score = Column(Float, nullable=True)
    engagement_score = Column(Float, nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_articles_status_created', 'status', 'created_at'),
        Index('idx_articles_category_style', 'topic_category', 'content_style'),
        Index('idx_articles_published', 'published_at'),
        Index('idx_articles_quality', 'quality_score'),
    )
    
    def __repr__(self):
        return f"<Article(title='{self.title[:50]}...', status='{self.status}')>"


class TopicModel(Base):
    """Trending topics tracking table."""
    
    __tablename__ = "topics"
    
    id = Column(String(255), primary_key=True)  # Topic hash as ID
    keywords = Column(JSON, nullable=False)  # Array of keywords
    category = Column(String(100), nullable=False, index=True)
    trend_score = Column(Float, nullable=False, index=True)
    context = Column(JSON, nullable=True)
    mention_count = Column(Integer, default=0, nullable=False)
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Analytics fields
    weekly_mentions = Column(Integer, default=0)
    monthly_mentions = Column(Integer, default=0)
    peak_trend_score = Column(Float, default=0.0)
    
    # Indexes
    __table_args__ = (
        Index('idx_topics_trend_active', 'is_active', 'trend_score'),
        Index('idx_topics_category_updated', 'category', 'last_updated'),
    )
    
    def __repr__(self):
        return f"<Topic(keywords='{self.keywords}', trend_score='{self.trend_score}')>"


class ContentCacheModel(Base):
    """Content generation cache table."""
    
    __tablename__ = "content_cache"
    
    cache_key = Column(String(255), primary_key=True)
    content_data = Column(JSON, nullable=False)
    content_type = Column(String(50), nullable=False, index=True)  # 'article', 'topic', 'search'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    hit_count = Column(Integer, default=0, nullable=False)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Cost tracking
    generation_cost = Column(Float, default=0.0)  # Cost saved by caching
    
    # Indexes
    __table_args__ = (
        Index('idx_cache_expiry_type', 'expires_at', 'content_type'),
        Index('idx_cache_accessed', 'last_accessed'),
    )
    
    def __repr__(self):
        return f"<ContentCache(key='{self.cache_key}', type='{self.content_type}')>"


class WorkflowRunModel(Base):
    """Workflow execution tracking table."""
    
    __tablename__ = "workflow_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_type = Column(String(50), nullable=False, index=True)  # 'daily', 'manual', 'scheduled'
    status = Column(String(50), nullable=False, index=True)  # 'running', 'completed', 'failed'
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Results
    article_id = Column(UUID(as_uuid=True), nullable=True)
    topics_analyzed = Column(Integer, default=0)
    content_generated = Column(Boolean, default=False)
    quality_checks = Column(Integer, default=0)
    cache_hits = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Metrics
    metrics = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_workflow_runs_type_status', 'run_type', 'status'),
        Index('idx_workflow_runs_started', 'started_at'),
    )
    
    def __repr__(self):
        return f"<WorkflowRun(type='{self.run_type}', status='{self.status}')>"


class UsageStatsModel(Base):
    """API and service usage statistics table."""
    
    __tablename__ = "usage_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime, nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    usage_metadata = Column(JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_usage_stats_date_service', 'date', 'service_name'),
        Index('idx_usage_stats_metric', 'service_name', 'metric_name', 'date'),
    )
    
    def __repr__(self):
        return f"<UsageStats(service='{self.service_name}', metric='{self.metric_name}')>"


# Create indexes for better query performance
def create_additional_indexes(engine):
    """Create additional indexes for optimization."""
    from sqlalchemy import text
    
    indexes = [
        # Full-text search indexes (PostgreSQL specific)
        "CREATE INDEX IF NOT EXISTS idx_raw_content_title_fts ON raw_content USING gin(to_tsvector('english', title))",
        "CREATE INDEX IF NOT EXISTS idx_raw_content_content_fts ON raw_content USING gin(to_tsvector('english', content))",
        "CREATE INDEX IF NOT EXISTS idx_articles_title_fts ON articles USING gin(to_tsvector('english', title))",
        
        # Partial indexes for active records
        "CREATE INDEX IF NOT EXISTS idx_data_sources_active ON data_sources (name, source_type) WHERE is_active = true",
        "CREATE INDEX IF NOT EXISTS idx_topics_active ON topics (trend_score DESC, last_updated DESC) WHERE is_active = true",
        
        # Composite indexes for common query patterns
        "CREATE INDEX IF NOT EXISTS idx_articles_quality_published ON articles (quality_score DESC, published_at DESC) WHERE status = 'published'",
        "CREATE INDEX IF NOT EXISTS idx_raw_content_recent ON raw_content (collected_at DESC, processed) WHERE processed = false",
    ]
    
    with engine.connect() as conn:
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
                conn.commit()
            except Exception as e:
                print(f"Warning: Could not create index - {e}")


# Database utility functions
def get_table_sizes(engine) -> dict:
    """Get sizes of all tables for monitoring."""
    from sqlalchemy import text
    
    query = text("""
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
            pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY size_bytes DESC
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query)
        return {row.tablename: row.size for row in result}