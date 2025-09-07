"""Data collection service for gathering financial content from multiple sources."""

import asyncio
import json
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, AsyncIterator
from urllib.parse import urljoin, urlparse

import aiohttp
import httpx
from bs4 import BeautifulSoup
import structlog

from app.models.domain import (
    DataSource, RawContent, SourceType, SourceId, 
    Topic
)
from app.core.config import settings

logger = structlog.get_logger()


class CollectionStrategy(ABC):
    """Base strategy for collecting data from different source types."""
    
    @abstractmethod
    async def collect(self, source: DataSource) -> List[RawContent]:
        """Collect content from the specified source."""
        pass
    
    @abstractmethod
    def can_handle(self, source_type: SourceType) -> bool:
        """Check if this strategy can handle the given source type."""
        pass


class WebScrapingStrategy(CollectionStrategy):
    """Strategy for scraping web content from financial websites."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.collected_urls = set()  # Avoid duplicates in single run
    
    def can_handle(self, source_type: SourceType) -> bool:
        return source_type == SourceType.WEB
    
    async def _create_session(self) -> aiohttp.ClientSession:
        """Create HTTP session with proper headers and timeouts."""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=settings.scraping.timeout)
            headers = {
                'User-Agent': settings.scraping.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(limit=settings.scraping.max_concurrent_requests)
            )
        return self.session
    
    async def collect(self, source: DataSource) -> List[RawContent]:
        """Scrape content from web source."""
        session = await self._create_session()
        collected_content = []
        
        try:
            # Get article URLs from the source
            article_urls = await self._discover_article_urls(session, source)
            
            # Process articles with rate limiting
            semaphore = asyncio.Semaphore(settings.scraping.max_concurrent_requests)
            
            tasks = [
                self._scrape_article_with_semaphore(session, url, source, semaphore)
                for url in article_urls[:20]  # Limit to 20 articles per run
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, RawContent):
                    collected_content.append(result)
                elif isinstance(result, Exception):
                    logger.warning("Failed to scrape article", error=str(result))
            
            logger.info(
                "Web scraping completed", 
                source=source.name, 
                collected=len(collected_content),
                discovered_urls=len(article_urls)
            )
            
        except Exception as e:
            logger.error("Web scraping failed", source=source.name, error=str(e))
        
        return collected_content
    
    async def _discover_article_urls(
        self, 
        session: aiohttp.ClientSession, 
        source: DataSource
    ) -> List[str]:
        """Discover article URLs from the source's main page or RSS feed."""
        urls = set()
        
        try:
            async with session.get(source.base_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Common patterns for financial content links
                    selectors = source.config.get('article_selectors', [
                        'a[href*="/article"]',
                        'a[href*="/news"]', 
                        'a[href*="/opinion"]',
                        'a[href*="/analysis"]',
                        '.article-link',
                        '.news-link'
                    ])
                    
                    for selector in selectors:
                        links = soup.select(selector)
                        for link in links:
                            href = link.get('href')
                            if href:
                                full_url = urljoin(source.base_url, href)
                                if self._is_financial_article_url(full_url):
                                    urls.add(full_url)
                    
        except Exception as e:
            logger.warning("Failed to discover URLs", source=source.name, error=str(e))
        
        return list(urls)
    
    def _is_financial_article_url(self, url: str) -> bool:
        """Check if URL likely contains financial content."""
        financial_keywords = [
            'finance', 'money', 'investment', 'trading', 'market',
            'economy', 'business', 'wealth', 'saving', 'budget'
        ]
        url_lower = url.lower()
        return any(keyword in url_lower for keyword in financial_keywords)
    
    async def _scrape_article_with_semaphore(
        self,
        session: aiohttp.ClientSession,
        url: str,
        source: DataSource,
        semaphore: asyncio.Semaphore
    ) -> Optional[RawContent]:
        """Scrape single article with rate limiting."""
        async with semaphore:
            # Rate limiting
            await asyncio.sleep(settings.scraping.request_delay)
            return await self._scrape_article(session, url, source)
    
    async def _scrape_article(
        self,
        session: aiohttp.ClientSession, 
        url: str,
        source: DataSource
    ) -> Optional[RawContent]:
        """Scrape content from a single article URL."""
        if url in self.collected_urls:
            return None
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract title
                    title = self._extract_title(soup)
                    if not title:
                        return None
                    
                    # Extract main content
                    content = self._extract_content(soup, source.config)
                    if not content or len(content.split()) < 100:  # Skip short articles
                        return None
                    
                    # Extract metadata
                    metadata = self._extract_metadata(soup, response.headers)
                    
                    # Create content ID
                    content_id = hashlib.md5(f"{url}_{title}".encode()).hexdigest()
                    
                    self.collected_urls.add(url)
                    
                    return RawContent(
                        id=content_id,
                        source_id=source.id,
                        title=title,
                        content=content,
                        url=url,
                        metadata=metadata,
                        collected_at=datetime.now()
                    )
                    
        except Exception as e:
            logger.warning("Failed to scrape article", url=url, error=str(e))
        
        return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title from HTML."""
        title_selectors = ['h1', 'title', '.article-title', '.entry-title']
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup, config: Dict[str, Any]) -> str:
        """Extract main article content from HTML."""
        # Custom content selectors from source config
        content_selectors = config.get('content_selectors', [
            '.article-content',
            '.entry-content', 
            '.post-content',
            'article',
            '.content'
        ])
        
        # Remove unwanted elements
        for unwanted in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            unwanted.decompose()
        
        content_parts = []
        
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True, separator=' ')
                if text and len(text) > 50:  # Skip very short paragraphs
                    content_parts.append(text)
        
        # If no specific selectors work, try to extract from paragraphs
        if not content_parts:
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 30:
                    content_parts.append(text)
        
        return '\n\n'.join(content_parts)
    
    def _extract_metadata(
        self, 
        soup: BeautifulSoup, 
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Extract metadata from article HTML and response headers."""
        metadata = {
            'scraped_at': datetime.now().isoformat(),
            'content_type': headers.get('content-type', ''),
        }
        
        # Extract publish date
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publish-date"]',
            '.publish-date',
            '.article-date',
            'time[datetime]'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_value = element.get('content') or element.get('datetime') or element.get_text()
                if date_value:
                    metadata['published_date'] = date_value
                    break
        
        # Extract author
        author_selectors = [
            'meta[name="author"]',
            '.author',
            '.byline',
            '[rel="author"]'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get('content') or element.get_text(strip=True)
                if author:
                    metadata['author'] = author
                    break
        
        # Extract tags/categories
        tag_selectors = [
            'meta[name="keywords"]',
            '.tags a',
            '.categories a'
        ]
        
        tags = []
        for selector in tag_selectors:
            elements = soup.select(selector)
            for element in elements:
                tag = element.get('content') or element.get_text(strip=True)
                if tag:
                    tags.append(tag)
        
        if tags:
            metadata['tags'] = tags[:10]  # Limit tags
        
        return metadata
    
    async def close(self):
        """Clean up resources."""
        if self.session and not self.session.closed:
            await self.session.close()


class SocialMediaStrategy(CollectionStrategy):
    """Strategy for collecting from social media APIs (Twitter, Reddit, etc.)."""
    
    def can_handle(self, source_type: SourceType) -> bool:
        return source_type == SourceType.SOCIAL
    
    async def collect(self, source: DataSource) -> List[RawContent]:
        """Collect from social media sources."""
        # Implementation would depend on specific API
        # For now, return empty list
        logger.info("Social media collection not yet implemented", source=source.name)
        return []


class DataCollectionService:
    """Main service for orchestrating data collection from multiple sources."""
    
    def __init__(self):
        self.strategies = [
            WebScrapingStrategy(),
            SocialMediaStrategy(),
        ]
        self.active_sources: List[DataSource] = []
    
    def register_source(self, source: DataSource) -> None:
        """Register a new data source."""
        if source.can_collect():
            self.active_sources.append(source)
            logger.info("Data source registered", name=source.name, type=source.source_type)
    
    async def collect_from_all_sources(self) -> List[RawContent]:
        """Collect content from all registered sources."""
        all_content = []
        
        for source in self.active_sources:
            try:
                strategy = self._get_strategy(source.source_type)
                if strategy:
                    content = await strategy.collect(source)
                    all_content.extend(content)
                    
                    # Update source metadata
                    source.last_collected = datetime.now()
                    source.collection_count += len(content)
                    
            except Exception as e:
                logger.error("Collection failed", source=source.name, error=str(e))
                # Update success rate
                source.success_rate = max(0.0, source.success_rate - 0.1)
        
        logger.info("Collection completed", total_content=len(all_content))
        return all_content
    
    async def collect_trending_topics(self) -> List[Topic]:
        """Analyze collected content to identify trending financial topics."""
        # This is a simplified implementation
        # In production, you'd use more sophisticated NLP analysis
        
        keyword_counts = {}
        financial_keywords = [
            'bitcoin', 'cryptocurrency', 'inflation', 'interest rates',
            'stock market', 'real estate', 'retirement', 'investing',
            'savings', 'debt', 'portfolio', 'dividends', 'bonds'
        ]
        
        # Collect recent content
        recent_content = await self.collect_from_all_sources()
        
        for content in recent_content:
            text = f"{content.title} {content.content}".lower()
            for keyword in financial_keywords:
                if keyword in text:
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Convert to topics with trend scores
        topics = []
        for keyword, count in keyword_counts.items():
            if count > 2:  # Minimum threshold
                topics.append(Topic(
                    keywords=[keyword],
                    category="finance",
                    trend_score=min(10.0, count / 2.0),  # Scale to 0-10
                    context={'mention_count': count}
                ))
        
        # Sort by trend score
        topics.sort(key=lambda t: t.trend_score, reverse=True)
        
        return topics[:10]  # Return top 10 trending topics
    
    def _get_strategy(self, source_type: SourceType) -> Optional[CollectionStrategy]:
        """Get appropriate collection strategy for source type."""
        for strategy in self.strategies:
            if strategy.can_handle(source_type):
                return strategy
        return None
    
    async def cleanup(self):
        """Clean up resources."""
        for strategy in self.strategies:
            if hasattr(strategy, 'close'):
                await strategy.close()


# Factory for creating pre-configured data sources
class DataSourceFactory:
    """Factory for creating pre-configured financial data sources."""
    
    @staticmethod
    def create_investopedia_source() -> DataSource:
        return DataSource(
            id=SourceId(),
            name="Investopedia Articles",
            source_type=SourceType.WEB,
            base_url="https://www.investopedia.com/articles/",
            config={
                'article_selectors': [
                    'a[href*="/articles/"]',
                    '.comp_title-link'
                ],
                'content_selectors': [
                    '.comp_article-body',
                    '.article-content'
                ]
            }
        )
    
    @staticmethod
    def create_bloomberg_source() -> DataSource:
        return DataSource(
            id=SourceId(),
            name="Bloomberg Opinion",
            source_type=SourceType.WEB, 
            base_url="https://www.bloomberg.com/opinion",
            config={
                'article_selectors': [
                    'a[href*="/opinion/"]',
                    '.story-list-story__headline-link'
                ],
                'content_selectors': [
                    '.body-content',
                    '.article-body'
                ]
            }
        )
    
    @staticmethod
    def create_cnbc_source() -> DataSource:
        return DataSource(
            id=SourceId(),
            name="CNBC Personal Finance",
            source_type=SourceType.WEB,
            base_url="https://www.cnbc.com/personal-finance/",
            config={
                'article_selectors': [
                    'a[href*="/personal-finance/"]',
                    '.Card-title a'
                ],
                'content_selectors': [
                    '.ArticleBody-articleBody',
                    '.InlineArticleBody-container'
                ]
            }
        )
    
    @classmethod
    def create_default_sources(cls) -> List[DataSource]:
        """Create list of default financial data sources."""
        return [
            cls.create_investopedia_source(),
            cls.create_bloomberg_source(),
            cls.create_cnbc_source(),
        ]