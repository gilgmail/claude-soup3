"""Content generation workflow orchestrating the entire process."""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import structlog

from app.models.domain import (
    Article, ArticleId, Topic, Content, ContentStyle,
    ArticleStatus, QualityMetrics, DataSource
)
from app.services.data_collection import (
    DataCollectionService, DataSourceFactory
)
from app.services.ai_content_generation import (
    AIContentGenerator, QualityAssessor
)
from app.services.knowledge_base import KnowledgeBaseService
from app.core.config import settings

logger = structlog.get_logger()


@dataclass
class WorkflowResult:
    """Result of content generation workflow."""
    success: bool
    article: Optional[Article] = None
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None
    cost_estimate: float = 0.0


class ContentGenerationWorkflow:
    """Main workflow orchestrating daily content generation."""
    
    def __init__(
        self,
        data_collector: DataCollectionService,
        ai_generator: AIContentGenerator,
        knowledge_base: KnowledgeBaseService,
        quality_assessor: QualityAssessor
    ):
        self.data_collector = data_collector
        self.ai_generator = ai_generator
        self.knowledge_base = knowledge_base
        self.quality_assessor = quality_assessor
        
        # Workflow configuration
        self.quality_threshold = settings.content.quality_threshold
        self.similarity_threshold = settings.content.similarity_threshold
        self.max_regeneration_attempts = 2
        
        # Workflow state
        self.daily_stats = {
            'topics_analyzed': 0,
            'content_generated': 0,
            'quality_checks': 0,
            'cache_hits': 0,
            'total_cost': 0.0
        }
    
    async def run_daily_generation(self) -> WorkflowResult:
        """Execute the complete daily content generation workflow."""
        start_time = datetime.now()
        logger.info("Starting daily content generation workflow")
        
        try:
            # Step 1: Collect and analyze trending topics
            trending_topics = await self._analyze_trending_topics()
            if not trending_topics:
                return WorkflowResult(
                    success=False,
                    error_message="No trending topics found"
                )
            
            # Step 2: Select best topic for content generation
            selected_topic = await self._select_optimal_topic(trending_topics)
            
            # Step 3: Check for existing similar content
            existing_content = await self._check_existing_content(selected_topic)
            
            # Step 4: Generate or customize content
            if existing_content:
                article = await self._customize_existing_content(existing_content, selected_topic)
                self.daily_stats['cache_hits'] += 1
            else:
                article = await self._generate_new_content(selected_topic)
                self.daily_stats['content_generated'] += 1
            
            # Step 5: Quality assurance
            article = await self._ensure_quality(article)
            
            # Step 6: Store and index content
            await self._store_content(article)
            
            # Step 7: Calculate metrics
            workflow_time = datetime.now() - start_time
            metrics = {
                'workflow_duration_seconds': workflow_time.total_seconds(),
                'topic_selected': {
                    'keywords': selected_topic.keywords,
                    'trend_score': selected_topic.trend_score
                },
                'final_quality_score': article.quality_metrics.overall_score if article.quality_metrics else None,
                'content_cached': existing_content is not None,
                **self.daily_stats
            }
            
            logger.info(
                "Daily content generation completed successfully",
                article_id=article.id.value,
                quality_score=article.quality_metrics.overall_score if article.quality_metrics else None,
                duration=workflow_time.total_seconds()
            )
            
            return WorkflowResult(
                success=True,
                article=article,
                metrics=metrics,
                cost_estimate=self.daily_stats['total_cost']
            )
            
        except Exception as e:
            logger.error("Daily content generation failed", error=str(e))
            return WorkflowResult(
                success=False,
                error_message=str(e),
                metrics=self.daily_stats
            )
    
    async def _analyze_trending_topics(self) -> List[Topic]:
        """Analyze trending topics from multiple sources."""
        logger.info("Analyzing trending topics")
        
        # Get trending topics from knowledge base (recent content analysis)
        kb_topics = await self.knowledge_base.get_trending_topics(days=7, limit=10)
        
        # Get trending topics from data collection
        collection_topics = await self.data_collector.collect_trending_topics()
        
        # Combine and deduplicate topics
        all_topics = kb_topics + collection_topics
        unique_topics = []
        seen_keywords = set()
        
        for topic in all_topics:
            topic_key = tuple(sorted(topic.keywords))
            if topic_key not in seen_keywords:
                unique_topics.append(topic)
                seen_keywords.add(topic_key)
        
        # Sort by trend score and take top topics
        unique_topics.sort(key=lambda t: t.trend_score, reverse=True)
        
        self.daily_stats['topics_analyzed'] = len(unique_topics)
        logger.info("Topic analysis completed", topics_found=len(unique_topics))
        
        return unique_topics[:5]  # Return top 5 trending topics
    
    async def _select_optimal_topic(self, topics: List[Topic]) -> Topic:
        """Select the optimal topic for content generation."""
        if not topics:
            raise ValueError("No topics available for selection")
        
        # Selection criteria:
        # 1. Trend score (40%)
        # 2. Content gap analysis (30%)
        # 3. Audience engagement potential (30%)
        
        scored_topics = []
        for topic in topics:
            # Check content gap - how much content already exists
            existing_content = await self.knowledge_base.search(
                query=' '.join(topic.keywords),
                filters={'category': topic.category},
                limit=10
            )
            
            content_gap_score = max(0, 10 - len(existing_content))  # Fewer existing = higher score
            
            # Engagement potential based on keywords
            engagement_score = self._assess_engagement_potential(topic)
            
            # Weighted score
            final_score = (
                topic.trend_score * 0.4 +
                content_gap_score * 0.3 +
                engagement_score * 0.3
            )
            
            scored_topics.append((topic, final_score))
        
        # Select topic with highest score
        scored_topics.sort(key=lambda x: x[1], reverse=True)
        selected_topic = scored_topics[0][0]
        
        logger.info(
            "Topic selected",
            keywords=selected_topic.keywords,
            trend_score=selected_topic.trend_score,
            final_score=scored_topics[0][1]
        )
        
        return selected_topic
    
    def _assess_engagement_potential(self, topic: Topic) -> float:
        """Assess topic engagement potential based on keywords."""
        high_engagement_keywords = {
            'cryptocurrency': 9.0, 'bitcoin': 9.0, 'investment': 8.5,
            'retirement': 8.0, 'debt': 8.0, 'budget': 7.5,
            'savings': 7.0, 'real estate': 8.5, 'stocks': 8.0
        }
        
        scores = []
        for keyword in topic.keywords:
            score = high_engagement_keywords.get(keyword.lower(), 6.0)
            scores.append(score)
        
        return sum(scores) / len(scores) if scores else 6.0
    
    async def _check_existing_content(self, topic: Topic) -> Optional[Content]:
        """Check if similar content already exists."""
        # Search for similar content
        search_results = await self.knowledge_base.search(
            query=' '.join(topic.keywords),
            filters={'category': topic.category},
            limit=5
        )
        
        if not search_results:
            return None
        
        # Check similarity threshold
        for result in search_results:
            # Simple similarity check based on keyword overlap
            result_keywords = set(result.content.lower().split()[:100])  # First 100 words
            topic_keywords = set(keyword.lower() for keyword in topic.keywords)
            
            overlap = len(result_keywords.intersection(topic_keywords))
            similarity = overlap / len(topic_keywords) if topic_keywords else 0
            
            if similarity > self.similarity_threshold:
                logger.info(
                    "Similar content found",
                    similarity_score=similarity,
                    existing_content_id=result.content_id
                )
                
                # Convert search result to Content object (simplified)
                return Content(
                    title=result.title,
                    introduction=result.content[:300],
                    main_content=result.content,
                    conclusion="",
                    key_insights=[],
                    actionable_steps=[]
                )
        
        return None
    
    async def _customize_existing_content(
        self,
        existing_content: Content,
        topic: Topic
    ) -> Article:
        """Customize existing content for new topic."""
        logger.info("Customizing existing content for new topic")
        
        # Create article with existing content
        article = Article(
            id=ArticleId(),
            topic=topic,
            content=existing_content,
            sources=[],
            status=ArticleStatus.GENERATED,
            style=ContentStyle.MOTIVATIONAL_FINANCE
        )
        
        # Light customization using AI
        customization_prompt = f"""
        Adapt this financial content for the topic: {', '.join(topic.keywords)}
        
        Original content: {existing_content.title}
        {existing_content.full_text()[:1000]}...
        
        Please:
        1. Update the title to focus on the new topic
        2. Modify the introduction to be more relevant
        3. Add 2-3 new actionable steps related to the topic
        4. Maintain the original quality and style
        """
        
        try:
            customized_text = await self.ai_generator.secondary_model.generate_content(
                customization_prompt,
                max_tokens=800
            )
            
            # Parse customized content (simplified)
            lines = customized_text.split('\n')
            if lines:
                article.content.title = lines[0].strip()
                article.content.introduction = '\n'.join(lines[1:3])
                
                # Extract new actionable steps
                new_steps = []
                for line in lines:
                    if any(marker in line for marker in ['1.', '2.', '3.', '•', '-']):
                        new_steps.append(line.strip())
                
                if new_steps:
                    article.content.actionable_steps.extend(new_steps[:3])
            
            # Estimate cost
            estimated_cost = 0.002  # Lower cost for customization
            self.daily_stats['total_cost'] += estimated_cost
            
        except Exception as e:
            logger.warning("Content customization failed, using original", error=str(e))
        
        return article
    
    async def _generate_new_content(self, topic: Topic) -> Article:
        """Generate completely new content for the topic."""
        logger.info("Generating new content", keywords=topic.keywords)
        
        # Select content style based on topic
        style = self._select_content_style(topic)
        
        # Get source materials for context
        source_materials = await self._get_source_materials(topic)
        
        # Generate content
        content = await self.ai_generator.generate_article_content(
            topic=topic,
            style=style,
            source_materials=source_materials
        )
        
        # Create article
        article = Article(
            id=ArticleId(),
            topic=topic,
            content=content,
            sources=[material.source_id for material in source_materials],
            status=ArticleStatus.GENERATED,
            style=style
        )
        
        # Update cost statistics
        estimated_cost = 0.015  # Higher cost for new generation
        self.daily_stats['total_cost'] += estimated_cost
        
        return article
    
    def _select_content_style(self, topic: Topic) -> ContentStyle:
        """Select appropriate content style based on topic."""
        keyword_styles = {
            'investment': ContentStyle.PRACTICAL_WISDOM,
            'savings': ContentStyle.PRACTICAL_WISDOM,
            'budget': ContentStyle.PRACTICAL_WISDOM,
            'retirement': ContentStyle.HISTORICAL_INSIGHTS,
            'debt': ContentStyle.MOTIVATIONAL_FINANCE,
            'cryptocurrency': ContentStyle.PHILOSOPHICAL_MONEY,
            'economy': ContentStyle.HISTORICAL_INSIGHTS
        }
        
        for keyword in topic.keywords:
            if keyword.lower() in keyword_styles:
                return keyword_styles[keyword.lower()]
        
        return ContentStyle.MOTIVATIONAL_FINANCE  # Default
    
    async def _get_source_materials(self, topic: Topic) -> List:
        """Get relevant source materials for context."""
        # Search knowledge base for related raw content
        search_results = await self.knowledge_base.search(
            query=' '.join(topic.keywords),
            filters={'content_type': 'raw'},
            limit=5
        )
        
        # Convert to RawContent objects (simplified)
        source_materials = []
        for result in search_results[:3]:  # Limit to top 3 for cost efficiency
            # This is a simplified conversion - in production, store/retrieve actual RawContent objects
            from app.models.domain import RawContent, SourceId
            raw_content = RawContent(
                id=result.content_id,
                source_id=SourceId.from_string(result.source_info.get('source_id', 'unknown')),
                title=result.title,
                content=result.content,
                url=result.source_info.get('url', ''),
                metadata=result.metadata,
                collected_at=result.created_at
            )
            source_materials.append(raw_content)
        
        return source_materials
    
    async def _ensure_quality(self, article: Article) -> Article:
        """Ensure article meets quality standards."""
        if not article.content:
            raise ValueError("Article has no content to assess")
        
        # Assess quality
        quality_metrics = await self.quality_assessor.assess(article.content)
        article.quality_metrics = quality_metrics
        article.status = ArticleStatus.QUALITY_CHECK
        
        self.daily_stats['quality_checks'] += 1
        
        # Check if quality meets threshold
        if quality_metrics.overall_score < self.quality_threshold:
            logger.warning(
                "Article quality below threshold",
                quality_score=quality_metrics.overall_score,
                threshold=self.quality_threshold
            )
            
            # Attempt regeneration with feedback
            if self.daily_stats['quality_checks'] <= self.max_regeneration_attempts:
                feedback = await self.quality_assessor.get_improvement_suggestions(article.content)
                
                improved_content = await self.ai_generator.regenerate_with_feedback(
                    article.content,
                    feedback,
                    article.topic,
                    article.style
                )
                
                article.content = improved_content
                
                # Re-assess quality
                new_quality_metrics = await self.quality_assessor.assess(improved_content)
                article.quality_metrics = new_quality_metrics
                
                self.daily_stats['quality_checks'] += 1
                self.daily_stats['total_cost'] += 0.010  # Additional cost for regeneration
                
                logger.info(
                    "Content regenerated",
                    original_score=quality_metrics.overall_score,
                    new_score=new_quality_metrics.overall_score
                )
        
        # Approve if quality is sufficient
        if article.quality_metrics.overall_score >= self.quality_threshold:
            article.approve_for_publishing()
            logger.info(
                "Article approved for publishing",
                quality_score=article.quality_metrics.overall_score
            )
        else:
            logger.error(
                "Article failed quality assurance after regeneration attempts",
                final_score=article.quality_metrics.overall_score
            )
        
        return article
    
    async def _store_content(self, article: Article) -> None:
        """Store article content in knowledge base."""
        if not article.content or not article.quality_metrics:
            return
        
        success = await self.knowledge_base.store_processed_content(
            article_id=article.id,
            content=article.content,
            topic=article.topic,
            style=article.style,
            quality_score=article.quality_metrics.overall_score
        )
        
        if success:
            logger.info("Article stored in knowledge base", article_id=article.id.value)
        else:
            logger.error("Failed to store article", article_id=article.id.value)
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get current workflow statistics."""
        return {
            **self.daily_stats,
            'quality_threshold': self.quality_threshold,
            'similarity_threshold': self.similarity_threshold,
            'cost_optimization': {
                'cache_hit_rate': f"{(self.daily_stats['cache_hits'] / max(1, self.daily_stats['content_generated'])) * 100:.1f}%",
                'estimated_daily_cost': f"${self.daily_stats['total_cost']:.3f}"
            }
        }


class ContentScheduler:
    """Scheduler for automated content generation."""
    
    def __init__(self, workflow: ContentGenerationWorkflow):
        self.workflow = workflow
        self.is_running = False
        self.scheduled_time = "06:00"  # 6 AM daily generation
    
    async def start_daily_schedule(self):
        """Start the daily content generation schedule."""
        self.is_running = True
        logger.info("Content scheduler started", scheduled_time=self.scheduled_time)
        
        while self.is_running:
            try:
                # Calculate time until next generation
                now = datetime.now()
                hour, minute = map(int, self.scheduled_time.split(':'))
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # If time has passed today, schedule for tomorrow
                if next_run <= now:
                    next_run += timedelta(days=1)
                
                wait_seconds = (next_run - now).total_seconds()
                logger.info(
                    "Next content generation scheduled",
                    next_run=next_run.isoformat(),
                    wait_seconds=wait_seconds
                )
                
                # Wait until scheduled time
                await asyncio.sleep(wait_seconds)
                
                # Execute daily generation
                if self.is_running:  # Check if still running after wait
                    result = await self.workflow.run_daily_generation()
                    
                    if result.success:
                        logger.info(
                            "Scheduled content generation completed",
                            article_id=result.article.id.value if result.article else None,
                            cost=result.cost_estimate
                        )
                    else:
                        logger.error(
                            "Scheduled content generation failed",
                            error=result.error_message
                        )
                
            except Exception as e:
                logger.error("Scheduler error", error=str(e))
                # Wait 1 hour before retrying on error
                await asyncio.sleep(3600)
    
    async def generate_now(self) -> WorkflowResult:
        """Trigger immediate content generation."""
        logger.info("Manual content generation triggered")
        return await self.workflow.run_daily_generation()
    
    def stop(self):
        """Stop the scheduler."""
        self.is_running = False
        logger.info("Content scheduler stopped")