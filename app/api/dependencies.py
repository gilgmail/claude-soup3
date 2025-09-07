"""FastAPI dependency injection for services."""

from functools import lru_cache
from typing import AsyncGenerator

from app.services.data_collection import (
    DataCollectionService, DataSourceFactory
)
from app.services.ai_content_generation import (
    AIContentGenerator, QualityAssessor, OpenAIModel
)
from app.services.knowledge_base import KnowledgeBaseService
from app.services.content_workflow import ContentGenerationWorkflow
from app.core.config import settings


# Service instances (singleton pattern)
_knowledge_base: KnowledgeBaseService = None
_data_collector: DataCollectionService = None
_ai_generator: AIContentGenerator = None
_content_workflow: ContentGenerationWorkflow = None


@lru_cache()
async def get_knowledge_base() -> KnowledgeBaseService:
    """Get or create knowledge base service instance."""
    global _knowledge_base
    
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBaseService(
            elasticsearch_url="http://localhost:9200"  # Configure from settings
        )
    
    return _knowledge_base


@lru_cache()
def get_data_collector() -> DataCollectionService:
    """Get or create data collection service instance."""
    global _data_collector
    
    if _data_collector is None:
        _data_collector = DataCollectionService()
        
        # Register default data sources
        default_sources = DataSourceFactory.create_default_sources()
        for source in default_sources:
            _data_collector.register_source(source)
    
    return _data_collector


@lru_cache()
def get_ai_generator() -> AIContentGenerator:
    """Get or create AI content generator instance."""
    global _ai_generator
    
    if _ai_generator is None:
        _ai_generator = AIContentGenerator()
    
    return _ai_generator


@lru_cache()
async def get_content_workflow() -> ContentGenerationWorkflow:
    """Get or create content generation workflow instance."""
    global _content_workflow
    
    if _content_workflow is None:
        knowledge_base = await get_knowledge_base()
        data_collector = get_data_collector()
        ai_generator = get_ai_generator()
        
        # Create quality assessor
        quality_assessor = QualityAssessor(OpenAIModel(settings.ai.secondary_model))
        
        _content_workflow = ContentGenerationWorkflow(
            data_collector=data_collector,
            ai_generator=ai_generator,
            knowledge_base=knowledge_base,
            quality_assessor=quality_assessor
        )
    
    return _content_workflow


# Cleanup function for graceful shutdown
async def cleanup_services():
    """Clean up all service resources."""
    global _knowledge_base, _data_collector, _ai_generator, _content_workflow
    
    if _knowledge_base:
        await _knowledge_base.cleanup()
    
    if _data_collector:
        await _data_collector.cleanup()
    
    # Reset instances
    _knowledge_base = None
    _data_collector = None  
    _ai_generator = None
    _content_workflow = None