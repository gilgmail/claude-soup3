"""Domain models following DDD principles."""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Types of data sources for content collection."""
    WEB = "web"
    API = "api"
    DATABASE = "database"
    SOCIAL = "social"
    RSS = "rss"


class ArticleStatus(str, Enum):
    """Article lifecycle status."""
    DRAFT = "draft"
    GENERATED = "generated"
    QUALITY_CHECK = "quality_check"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContentStyle(str, Enum):
    """Content generation styles."""
    MOTIVATIONAL_FINANCE = "motivational_finance"
    PHILOSOPHICAL_MONEY = "philosophical_money"
    PRACTICAL_WISDOM = "practical_wisdom"
    HISTORICAL_INSIGHTS = "historical_insights"


@dataclass
class ArticleId:
    """Article unique identifier."""
    value: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    @classmethod
    def from_string(cls, value: str) -> 'ArticleId':
        return cls(value=value)


@dataclass
class SourceId:
    """Data source unique identifier."""
    value: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    @classmethod
    def from_string(cls, value: str) -> 'SourceId':
        return cls(value=value)


@dataclass
class Topic:
    """Financial topic for content generation."""
    keywords: List[str]
    category: str
    trend_score: float
    context: Dict[str, Any] = field(default_factory=dict)
    
    def hash(self) -> str:
        """Generate unique hash for caching."""
        keywords_str = "_".join(sorted(self.keywords))
        return f"{self.category}_{keywords_str}_{self.trend_score:.2f}"


@dataclass
class DataSource:
    """Data source configuration and metadata."""
    id: SourceId
    name: str
    source_type: SourceType
    base_url: str
    config: Dict[str, Any]
    is_active: bool = True
    last_collected: Optional[datetime] = None
    collection_count: int = 0
    success_rate: float = 1.0
    
    def can_collect(self) -> bool:
        """Check if source is ready for collection."""
        return self.is_active and self.success_rate > 0.5


@dataclass
class RawContent:
    """Raw collected content before processing."""
    id: str
    source_id: SourceId
    title: str
    content: str
    url: str
    metadata: Dict[str, Any]
    collected_at: datetime
    processed: bool = False
    
    def extract_keywords(self) -> List[str]:
        """Extract key financial terms from content."""
        # Simplified keyword extraction - in production use NLP
        financial_terms = [
            "investment", "savings", "debt", "budget", "wealth",
            "compound", "dividend", "portfolio", "risk", "return"
        ]
        
        content_lower = self.content.lower()
        return [term for term in financial_terms if term in content_lower]


@dataclass 
class Content:
    """Generated article content."""
    title: str
    introduction: str
    main_content: str
    conclusion: str
    key_insights: List[str]
    actionable_steps: List[str]
    
    def full_text(self) -> str:
        """Get complete article text."""
        return f"{self.title}\n\n{self.introduction}\n\n{self.main_content}\n\n{self.conclusion}"
    
    def word_count(self) -> int:
        """Calculate total word count."""
        return len(self.full_text().split())


@dataclass
class QualityMetrics:
    """Content quality assessment metrics."""
    readability_score: float
    engagement_score: float  
    educational_value: float
    actionability_score: float
    originality_score: float
    
    @property
    def overall_score(self) -> float:
        """Calculate weighted overall quality score."""
        weights = {
            'readability': 0.2,
            'engagement': 0.25,
            'educational': 0.25, 
            'actionability': 0.2,
            'originality': 0.1
        }
        
        return (
            self.readability_score * weights['readability'] +
            self.engagement_score * weights['engagement'] +
            self.educational_value * weights['educational'] +
            self.actionability_score * weights['actionability'] +
            self.originality_score * weights['originality']
        )


@dataclass
class Article:
    """Main article aggregate root."""
    id: ArticleId
    topic: Topic
    content: Optional[Content]
    sources: List[SourceId]
    status: ArticleStatus
    style: ContentStyle
    quality_metrics: Optional[QualityMetrics] = None
    created_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    
    def generate_content(self, generator_service) -> None:
        """Generate content using AI service."""
        if self.status != ArticleStatus.DRAFT:
            raise ValueError(f"Cannot generate content for article in {self.status} status")
            
        # This would call the content generation service
        self.content = generator_service.generate(self.topic, self.style)
        self.status = ArticleStatus.GENERATED
    
    def assess_quality(self, quality_service) -> None:
        """Assess content quality."""
        if not self.content:
            raise ValueError("Cannot assess quality without content")
            
        self.quality_metrics = quality_service.assess(self.content)
        self.status = ArticleStatus.QUALITY_CHECK
    
    def approve_for_publishing(self) -> None:
        """Approve article for publishing."""
        if not self.quality_metrics:
            raise ValueError("Cannot approve without quality assessment")
            
        if self.quality_metrics.overall_score < 8.0:
            raise ValueError(f"Quality score {self.quality_metrics.overall_score:.2f} below threshold")
            
        self.status = ArticleStatus.APPROVED
    
    def publish(self) -> None:
        """Mark article as published."""
        if self.status != ArticleStatus.APPROVED:
            raise ValueError(f"Cannot publish article in {self.status} status")
            
        self.status = ArticleStatus.PUBLISHED
        self.published_at = datetime.now()


# Value Objects for API responses
class TopicSummary(BaseModel):
    """Topic information for API responses."""
    keywords: List[str]
    category: str
    trend_score: float


class ArticleSummary(BaseModel):
    """Article summary for API responses."""
    id: str
    title: str
    status: ArticleStatus
    style: ContentStyle
    quality_score: Optional[float] = None
    created_at: datetime
    published_at: Optional[datetime] = None


class GenerationRequest(BaseModel):
    """Request for content generation."""
    topic_keywords: List[str] = Field(..., min_items=1, max_items=10)
    category: str = Field(..., min_length=1, max_length=50)
    style: ContentStyle = ContentStyle.MOTIVATIONAL_FINANCE
    source_preferences: List[SourceType] = Field(default_factory=list)