"""AI-powered content generation service with cost optimization."""

import asyncio
import hashlib
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

import structlog
from anthropic import AsyncAnthropic
import openai

from app.models.domain import (
    Topic, Content, ContentStyle, QualityMetrics,
    RawContent
)
from app.core.config import settings

logger = structlog.get_logger()


class AIModel(ABC):
    """Abstract base class for AI model integrations."""
    
    @abstractmethod
    async def generate_content(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate content using the AI model."""
        pass
    
    @property
    @abstractmethod
    def cost_per_1k_tokens(self) -> float:
        """Cost per 1000 tokens for this model."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the AI model."""
        pass


class AnthropicModel(AIModel):
    """Anthropic Claude model integration."""
    
    def __init__(self, model_name: str = "claude-3-sonnet-20240229"):
        self._model_name = model_name
        self.client = AsyncAnthropic(api_key=settings.ai.anthropic_api_key)
        self._request_count = 0
        self._daily_usage = 0
        self._last_reset = datetime.now().date()
    
    async def generate_content(
        self,
        prompt: str, 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate content using Claude."""
        # Check rate limits
        if not self._can_make_request():
            raise ValueError("Rate limit exceeded")
        
        try:
            response = await self.client.messages.create(
                model=self._model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            self._update_usage_stats()
            
            # Extract text from response
            content = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    content += block.text
            
            return content.strip()
            
        except Exception as e:
            logger.error("Anthropic API error", error=str(e), model=self._model_name)
            raise
    
    def _can_make_request(self) -> bool:
        """Check if we can make another API request."""
        # Reset daily counter if new day
        current_date = datetime.now().date()
        if current_date > self._last_reset:
            self._daily_usage = 0
            self._last_reset = current_date
        
        return self._daily_usage < settings.ai.daily_request_limit
    
    def _update_usage_stats(self):
        """Update usage statistics."""
        self._request_count += 1
        self._daily_usage += 1
    
    @property
    def cost_per_1k_tokens(self) -> float:
        return 0.015  # Approximate cost for Claude-3 Sonnet
    
    @property
    def model_name(self) -> str:
        return self._model_name


class OpenAIModel(AIModel):
    """OpenAI GPT model integration."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self._model_name = model_name
        openai.api_key = settings.ai.openai_api_key
        self._request_count = 0
    
    async def generate_content(
        self,
        prompt: str,
        max_tokens: int = 1000, 
        temperature: float = 0.7
    ) -> str:
        """Generate content using OpenAI GPT."""
        try:
            response = await openai.ChatCompletion.acreate(
                model=self._model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            self._request_count += 1
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("OpenAI API error", error=str(e), model=self._model_name)
            raise
    
    @property
    def cost_per_1k_tokens(self) -> float:
        if "gpt-4" in self._model_name:
            return 0.06  # GPT-4
        return 0.002  # GPT-3.5-turbo
    
    @property
    def model_name(self) -> str:
        return self._model_name


class ContentTemplate:
    """Template for structured content generation."""
    
    def __init__(self, style: ContentStyle):
        self.style = style
        self.structure = self._get_structure()
        self.prompts = self._get_prompts()
    
    def _get_structure(self) -> List[str]:
        """Get content structure for the style."""
        structures = {
            ContentStyle.MOTIVATIONAL_FINANCE: [
                "hook", "problem", "wisdom", "practical_steps", "inspiration"
            ],
            ContentStyle.PHILOSOPHICAL_MONEY: [
                "quote", "historical_context", "modern_application", "reflection"
            ],
            ContentStyle.PRACTICAL_WISDOM: [
                "scenario", "principle", "implementation", "results"
            ],
            ContentStyle.HISTORICAL_INSIGHTS: [
                "historical_event", "lesson", "modern_parallel", "application"
            ]
        }
        return structures.get(self.style, structures[ContentStyle.MOTIVATIONAL_FINANCE])
    
    def _get_prompts(self) -> Dict[str, str]:
        """Get prompts for each section."""
        base_prompts = {
            ContentStyle.MOTIVATIONAL_FINANCE: {
                "hook": "Create an engaging hook about {topic} that captures attention",
                "problem": "Describe a common financial problem related to {topic}",
                "wisdom": "Share profound financial wisdom about {topic}",
                "practical_steps": "Provide 3-5 actionable steps for {topic}",
                "inspiration": "End with inspiring message about {topic}"
            },
            ContentStyle.PHILOSOPHICAL_MONEY: {
                "quote": "Start with a relevant quote about {topic}",
                "historical_context": "Provide historical context for {topic}",
                "modern_application": "Apply this wisdom to modern {topic}",
                "reflection": "Conclude with thoughtful reflection on {topic}"
            },
            ContentStyle.PRACTICAL_WISDOM: {
                "scenario": "Present a realistic scenario involving {topic}",
                "principle": "Explain the underlying principle of {topic}",
                "implementation": "Show how to implement {topic} practically",
                "results": "Describe expected outcomes from {topic}"
            },
            ContentStyle.HISTORICAL_INSIGHTS: {
                "historical_event": "Describe a historical event related to {topic}",
                "lesson": "Extract the key lesson about {topic}",
                "modern_parallel": "Draw parallels to modern {topic}",
                "application": "Show how to apply this to {topic} today"
            }
        }
        return base_prompts.get(self.style, base_prompts[ContentStyle.MOTIVATIONAL_FINANCE])
    
    def generate_section_prompt(self, section: str, topic: Topic, context: str = "") -> str:
        """Generate prompt for a specific section."""
        base_prompt = self.prompts.get(section, "Write about {topic}")
        topic_str = ", ".join(topic.keywords)
        
        full_prompt = f"""
        Write a {section} section for a financial wisdom article.
        
        Topic: {topic_str}
        Category: {topic.category}
        Style: {self.style.value}
        
        {base_prompt.format(topic=topic_str)}
        
        Additional context: {context}
        
        Requirements:
        - Write in an engaging, accessible tone
        - Include practical insights
        - Keep it concise but impactful (150-250 words)
        - Focus on actionable financial wisdom
        """
        
        return full_prompt.strip()


class QualityAssessor:
    """Service for assessing content quality."""
    
    def __init__(self, ai_model: AIModel):
        self.ai_model = ai_model
    
    async def assess(self, content: Content) -> QualityMetrics:
        """Assess content quality across multiple dimensions."""
        full_text = content.full_text()
        
        # Run assessments in parallel for efficiency
        assessments = await asyncio.gather(
            self._assess_readability(full_text),
            self._assess_engagement(full_text),
            self._assess_educational_value(full_text),
            self._assess_actionability(content),
            self._assess_originality(full_text)
        )
        
        return QualityMetrics(
            readability_score=assessments[0],
            engagement_score=assessments[1],
            educational_value=assessments[2],
            actionability_score=assessments[3],
            originality_score=assessments[4]
        )
    
    async def _assess_readability(self, text: str) -> float:
        """Assess text readability (0-10 scale)."""
        prompt = f"""
        Rate the readability of this financial content on a scale of 0-10:
        
        {text[:1000]}...
        
        Consider:
        - Sentence complexity
        - Vocabulary accessibility
        - Clear structure
        - Financial jargon usage
        
        Return only a number between 0-10.
        """
        
        try:
            response = await self.ai_model.generate_content(prompt, max_tokens=10)
            return float(response.strip())
        except:
            return 7.0  # Default fallback
    
    async def _assess_engagement(self, text: str) -> float:
        """Assess content engagement potential."""
        prompt = f"""
        Rate the engagement potential of this content on a scale of 0-10:
        
        {text[:1000]}...
        
        Consider:
        - Hook effectiveness
        - Emotional resonance
        - Storytelling elements
        - Reader retention
        
        Return only a number between 0-10.
        """
        
        try:
            response = await self.ai_model.generate_content(prompt, max_tokens=10)
            return float(response.strip())
        except:
            return 7.0
    
    async def _assess_educational_value(self, text: str) -> float:
        """Assess educational value of content."""
        prompt = f"""
        Rate the educational value of this financial content on a scale of 0-10:
        
        {text[:1000]}...
        
        Consider:
        - Depth of insights
        - Learning opportunities
        - Financial literacy contribution
        - Practical knowledge
        
        Return only a number between 0-10.
        """
        
        try:
            response = await self.ai_model.generate_content(prompt, max_tokens=10)
            return float(response.strip())
        except:
            return 7.0
    
    async def _assess_actionability(self, content: Content) -> float:
        """Assess how actionable the content is."""
        # Simple heuristic based on actionable steps
        if content.actionable_steps and len(content.actionable_steps) >= 3:
            return 9.0
        elif content.actionable_steps and len(content.actionable_steps) >= 1:
            return 7.0
        else:
            return 5.0
    
    async def _assess_originality(self, text: str) -> float:
        """Assess content originality."""
        # Simplified assessment - in production use plagiarism detection
        common_phrases = [
            "financial freedom", "passive income", "compound interest",
            "diversify your portfolio", "emergency fund"
        ]
        
        text_lower = text.lower()
        common_count = sum(1 for phrase in common_phrases if phrase in text_lower)
        
        # Score inversely related to common phrase usage
        originality = max(5.0, 10.0 - (common_count * 0.5))
        return min(10.0, originality)
    
    async def get_improvement_suggestions(self, content: Content) -> List[str]:
        """Generate suggestions for content improvement."""
        prompt = f"""
        Analyze this financial content and provide 3-5 specific improvement suggestions:
        
        Title: {content.title}
        Content: {content.full_text()[:1500]}...
        
        Focus on:
        - Content structure
        - Engagement factors
        - Educational value
        - Actionability
        
        Provide concrete, actionable suggestions.
        """
        
        try:
            response = await self.ai_model.generate_content(prompt, max_tokens=500)
            # Parse suggestions (simplified)
            suggestions = [s.strip() for s in response.split('\n') if s.strip()]
            return suggestions[:5]
        except:
            return ["Consider adding more specific examples", "Include clearer action steps"]


class AIContentGenerator:
    """Main AI content generation service with cost optimization."""
    
    def __init__(self):
        # Initialize AI models with cost-efficiency strategy
        self.primary_model = AnthropicModel(settings.ai.primary_model)
        self.secondary_model = OpenAIModel(settings.ai.secondary_model)
        self.quality_assessor = QualityAssessor(self.secondary_model)
        
        # Cache for cost optimization
        self._generation_cache: Dict[str, Content] = {}
        self._cache_ttl = timedelta(days=7)
        self._cache_timestamps: Dict[str, datetime] = {}
    
    async def generate_article_content(
        self,
        topic: Topic,
        style: ContentStyle,
        source_materials: Optional[List[RawContent]] = None
    ) -> Content:
        """Generate article content with cost optimization."""
        # Check cache first
        cache_key = self._get_cache_key(topic, style)
        cached_content = self._get_from_cache(cache_key)
        
        if cached_content:
            logger.info("Using cached content", topic=topic.keywords, style=style)
            return cached_content
        
        # Generate new content
        template = ContentTemplate(style)
        context = self._build_context(source_materials)
        
        # Generate content sections
        sections = {}
        total_cost = 0.0
        
        for section in template.structure:
            prompt = template.generate_section_prompt(section, topic, context)
            
            # Use cost-efficient model selection
            model = self._select_model_for_task(section)
            
            try:
                section_content = await model.generate_content(
                    prompt=prompt,
                    max_tokens=300,
                    temperature=0.7
                )
                sections[section] = section_content
                
                # Estimate cost
                estimated_tokens = len(prompt.split()) + len(section_content.split())
                total_cost += (estimated_tokens / 1000) * model.cost_per_1k_tokens
                
            except Exception as e:
                logger.error("Section generation failed", section=section, error=str(e))
                sections[section] = f"[Content generation failed for {section}]"
        
        # Assemble final content
        content = self._assemble_content(sections, template.structure, topic)
        
        # Cache the result
        self._cache_content(cache_key, content)
        
        logger.info(
            "Content generated",
            topic=topic.keywords,
            style=style,
            estimated_cost=f"${total_cost:.4f}"
        )
        
        return content
    
    def _select_model_for_task(self, section: str) -> AIModel:
        """Select most cost-efficient model for the task."""
        # Use primary model for critical sections, secondary for others
        critical_sections = ["wisdom", "principle", "lesson"]
        
        if section in critical_sections:
            return self.primary_model
        else:
            return self.secondary_model
    
    def _build_context(self, source_materials: Optional[List[RawContent]]) -> str:
        """Build context from source materials."""
        if not source_materials:
            return ""
        
        # Extract key insights from source materials
        context_parts = []
        for material in source_materials[:3]:  # Limit to top 3 sources
            summary = material.content[:300] + "..." if len(material.content) > 300 else material.content
            context_parts.append(f"Source insight: {summary}")
        
        return "\n\n".join(context_parts)
    
    def _assemble_content(
        self, 
        sections: Dict[str, str], 
        structure: List[str],
        topic: Topic
    ) -> Content:
        """Assemble sections into final content structure."""
        # Generate title
        title = self._generate_title(topic, sections)
        
        # Map sections to content structure
        if "hook" in sections:
            introduction = sections.get("hook", "")
        else:
            introduction = list(sections.values())[0] if sections else ""
        
        # Main content combines middle sections
        main_sections = [sections.get(s, "") for s in structure[1:-1] if sections.get(s)]
        main_content = "\n\n".join(main_sections)
        
        # Conclusion
        if "inspiration" in sections:
            conclusion = sections.get("inspiration", "")
        elif "reflection" in sections:
            conclusion = sections.get("reflection", "")
        else:
            conclusion = list(sections.values())[-1] if sections else ""
        
        # Extract actionable steps (simplified)
        actionable_steps = []
        if "practical_steps" in sections:
            steps_text = sections["practical_steps"]
            # Simple parsing - in production use NLP
            lines = steps_text.split('\n')
            for line in lines:
                if any(marker in line.lower() for marker in ['1.', '2.', '•', '-', 'step']):
                    actionable_steps.append(line.strip())
        
        # Extract key insights
        key_insights = []
        if "wisdom" in sections:
            key_insights.append(sections["wisdom"][:200] + "...")
        if "principle" in sections:
            key_insights.append(sections["principle"][:200] + "...")
        
        return Content(
            title=title,
            introduction=introduction,
            main_content=main_content,
            conclusion=conclusion,
            key_insights=key_insights,
            actionable_steps=actionable_steps
        )
    
    def _generate_title(self, topic: Topic, sections: Dict[str, str]) -> str:
        """Generate compelling article title."""
        keywords = topic.keywords[:3]  # Use top 3 keywords
        
        # Template-based title generation
        templates = [
            f"The Ultimate Guide to {keywords[0].title()}",
            f"How {keywords[0].title()} Can Transform Your Financial Future",
            f"Master {keywords[0].title()}: Wisdom for Financial Success",
            f"The Power of {keywords[0].title()} in Building Wealth"
        ]
        
        # Simple selection based on category
        if topic.category == "investment":
            return templates[1]
        elif topic.category == "savings":
            return templates[3]
        else:
            return templates[0]
    
    def _get_cache_key(self, topic: Topic, style: ContentStyle) -> str:
        """Generate cache key for topic and style."""
        topic_hash = topic.hash()
        return f"content_{style.value}_{topic_hash}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Content]:
        """Retrieve content from cache if valid."""
        if cache_key not in self._generation_cache:
            return None
        
        # Check TTL
        timestamp = self._cache_timestamps.get(cache_key)
        if timestamp and datetime.now() - timestamp > self._cache_ttl:
            # Remove expired content
            del self._generation_cache[cache_key]
            del self._cache_timestamps[cache_key]
            return None
        
        return self._generation_cache[cache_key]
    
    def _cache_content(self, cache_key: str, content: Content) -> None:
        """Cache generated content."""
        self._generation_cache[cache_key] = content
        self._cache_timestamps[cache_key] = datetime.now()
        
        # Simple cache size management
        if len(self._generation_cache) > 100:
            # Remove oldest entries
            oldest_key = min(self._cache_timestamps.keys(), 
                           key=lambda k: self._cache_timestamps[k])
            del self._generation_cache[oldest_key]
            del self._cache_timestamps[oldest_key]
    
    async def regenerate_with_feedback(
        self,
        original_content: Content,
        feedback: List[str],
        topic: Topic,
        style: ContentStyle
    ) -> Content:
        """Regenerate content with improvement feedback."""
        feedback_text = "\n".join(feedback)
        
        improvement_prompt = f"""
        Improve this financial content based on the feedback:
        
        Original Content:
        Title: {original_content.title}
        {original_content.full_text()[:1000]}...
        
        Feedback for improvement:
        {feedback_text}
        
        Please rewrite the content addressing these concerns while maintaining the core message.
        """
        
        try:
            improved_text = await self.primary_model.generate_content(
                improvement_prompt,
                max_tokens=1500
            )
            
            # Parse improved content (simplified)
            lines = improved_text.split('\n')
            improved_title = lines[0] if lines else original_content.title
            improved_body = '\n'.join(lines[1:]) if len(lines) > 1 else improved_text
            
            return Content(
                title=improved_title,
                introduction=improved_body[:300] + "...",
                main_content=improved_body,
                conclusion=original_content.conclusion,
                key_insights=original_content.key_insights,
                actionable_steps=original_content.actionable_steps
            )
            
        except Exception as e:
            logger.error("Content regeneration failed", error=str(e))
            return original_content
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get AI service usage statistics."""
        return {
            "primary_model": {
                "name": self.primary_model.model_name,
                "requests": getattr(self.primary_model, '_request_count', 0),
                "daily_usage": getattr(self.primary_model, '_daily_usage', 0)
            },
            "secondary_model": {
                "name": self.secondary_model.model_name, 
                "requests": getattr(self.secondary_model, '_request_count', 0)
            },
            "cache_stats": {
                "cached_items": len(self._generation_cache),
                "cache_hit_potential": f"{len(self._generation_cache) * 70}% cost reduction"
            }
        }