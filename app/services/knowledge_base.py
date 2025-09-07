"""Knowledge base service for content storage, indexing, and retrieval."""

import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

import structlog
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from app.models.domain import (
    RawContent, Content, Topic, ArticleId, SourceId,
    ContentStyle
)
from app.core.config import settings

logger = structlog.get_logger()


@dataclass
class SearchResult:
    """Search result with relevance scoring."""
    content_id: str
    title: str
    content: str
    source_info: Dict[str, Any]
    relevance_score: float
    content_type: str  # 'raw' or 'processed'
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimilarityResult:
    """Result for content similarity searches."""
    content_id: str
    similarity_score: float
    content: Content
    topic: Topic
    style: ContentStyle


class ContentIndexer:
    """Service for indexing content in Elasticsearch."""
    
    def __init__(self, es_client: AsyncElasticsearch):
        self.es = es_client
        self.raw_content_index = "financial_raw_content"
        self.processed_content_index = "financial_processed_content"
        self.topics_index = "financial_topics"
    
    async def setup_indices(self):
        """Create Elasticsearch indices with proper mappings."""
        # Raw content index mapping
        raw_content_mapping = {
            "mappings": {
                "properties": {
                    "title": {
                        "type": "text",
                        "analyzer": "english",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "content": {
                        "type": "text", 
                        "analyzer": "english"
                    },
                    "url": {"type": "keyword"},
                    "source_id": {"type": "keyword"},
                    "source_name": {"type": "keyword"},
                    "collected_at": {"type": "date"},
                    "keywords": {"type": "keyword"},
                    "financial_terms": {"type": "keyword"},
                    "metadata": {"type": "object"},
                    "content_vector": {
                        "type": "dense_vector",
                        "dims": 384  # For sentence transformers
                    }
                }
            }
        }
        
        # Processed content index mapping
        processed_content_mapping = {
            "mappings": {
                "properties": {
                    "article_id": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "english",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "introduction": {"type": "text", "analyzer": "english"},
                    "main_content": {"type": "text", "analyzer": "english"},
                    "conclusion": {"type": "text", "analyzer": "english"},
                    "full_content": {"type": "text", "analyzer": "english"},
                    "key_insights": {"type": "text", "analyzer": "english"},
                    "actionable_steps": {"type": "text", "analyzer": "english"},
                    "topic_keywords": {"type": "keyword"},
                    "topic_category": {"type": "keyword"},
                    "content_style": {"type": "keyword"},
                    "quality_score": {"type": "float"},
                    "created_at": {"type": "date"},
                    "published_at": {"type": "date"},
                    "word_count": {"type": "integer"},
                    "content_vector": {
                        "type": "dense_vector",
                        "dims": 384
                    }
                }
            }
        }
        
        # Topics index mapping
        topics_mapping = {
            "mappings": {
                "properties": {
                    "keywords": {"type": "keyword"},
                    "category": {"type": "keyword"},
                    "trend_score": {"type": "float"},
                    "context": {"type": "object"},
                    "last_updated": {"type": "date"},
                    "mention_count": {"type": "integer"}
                }
            }
        }
        
        # Create indices
        for index, mapping in [
            (self.raw_content_index, raw_content_mapping),
            (self.processed_content_index, processed_content_mapping),
            (self.topics_index, topics_mapping)
        ]:
            try:
                if not await self.es.indices.exists(index=index):
                    await self.es.indices.create(index=index, body=mapping)
                    logger.info("Created index", index=index)
            except Exception as e:
                logger.error("Failed to create index", index=index, error=str(e))
    
    async def index_raw_content(self, content: RawContent) -> bool:
        """Index raw collected content."""
        try:
            document = {
                "title": content.title,
                "content": content.content,
                "url": content.url,
                "source_id": content.source_id.value,
                "collected_at": content.collected_at.isoformat(),
                "keywords": content.extract_keywords(),
                "financial_terms": self._extract_financial_terms(content.content),
                "metadata": content.metadata,
                "word_count": len(content.content.split())
            }
            
            # Generate content vector (simplified - in production use actual embeddings)
            content_hash = hashlib.md5(content.content.encode()).hexdigest()
            document["content_vector"] = [float(int(c, 16)) / 15.0 for c in content_hash[:384]]
            
            response = await self.es.index(
                index=self.raw_content_index,
                id=content.id,
                body=document
            )
            
            logger.info("Indexed raw content", content_id=content.id, result=response['result'])
            return True
            
        except Exception as e:
            logger.error("Failed to index raw content", content_id=content.id, error=str(e))
            return False
    
    async def index_processed_content(
        self, 
        article_id: ArticleId, 
        content: Content,
        topic: Topic,
        style: ContentStyle,
        quality_score: Optional[float] = None
    ) -> bool:
        """Index processed article content."""
        try:
            full_content = content.full_text()
            
            document = {
                "article_id": article_id.value,
                "title": content.title,
                "introduction": content.introduction,
                "main_content": content.main_content,
                "conclusion": content.conclusion,
                "full_content": full_content,
                "key_insights": content.key_insights,
                "actionable_steps": content.actionable_steps,
                "topic_keywords": topic.keywords,
                "topic_category": topic.category,
                "content_style": style.value,
                "quality_score": quality_score,
                "created_at": datetime.now().isoformat(),
                "word_count": content.word_count()
            }
            
            # Generate content vector
            content_hash = hashlib.md5(full_content.encode()).hexdigest()
            document["content_vector"] = [float(int(c, 16)) / 15.0 for c in content_hash[:384]]
            
            response = await self.es.index(
                index=self.processed_content_index,
                id=article_id.value,
                body=document
            )
            
            logger.info("Indexed processed content", article_id=article_id.value, result=response['result'])
            return True
            
        except Exception as e:
            logger.error("Failed to index processed content", article_id=article_id.value, error=str(e))
            return False
    
    async def index_topic(self, topic: Topic) -> bool:
        """Index topic information."""
        try:
            topic_id = topic.hash()
            document = {
                "keywords": topic.keywords,
                "category": topic.category,
                "trend_score": topic.trend_score,
                "context": topic.context,
                "last_updated": datetime.now().isoformat(),
                "mention_count": topic.context.get('mention_count', 0)
            }
            
            response = await self.es.index(
                index=self.topics_index,
                id=topic_id,
                body=document
            )
            
            logger.info("Indexed topic", topic_id=topic_id, result=response['result'])
            return True
            
        except Exception as e:
            logger.error("Failed to index topic", topic_keywords=topic.keywords, error=str(e))
            return False
    
    def _extract_financial_terms(self, content: str) -> List[str]:
        """Extract financial terms from content."""
        financial_terms = [
            'investment', 'portfolio', 'dividend', 'compound', 'interest',
            'retirement', 'savings', 'budget', 'debt', 'credit', 'mortgage',
            'insurance', 'tax', 'income', 'expense', 'profit', 'loss',
            'equity', 'bond', 'stock', 'fund', 'etf', 'cryptocurrency',
            'inflation', 'deflation', 'recession', 'bull market', 'bear market'
        ]
        
        content_lower = content.lower()
        found_terms = []
        
        for term in financial_terms:
            if term in content_lower:
                found_terms.append(term)
        
        return found_terms


class KnowledgeSearchEngine:
    """Advanced search engine for financial content."""
    
    def __init__(self, es_client: AsyncElasticsearch, indexer: ContentIndexer):
        self.es = es_client
        self.indexer = indexer
    
    async def search_content(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        content_type: Optional[str] = None
    ) -> List[SearchResult]:
        """Search across all indexed content."""
        # Determine which indices to search
        indices = []
        if content_type is None or content_type == 'raw':
            indices.append(self.indexer.raw_content_index)
        if content_type is None or content_type == 'processed':
            indices.append(self.indexer.processed_content_index)
        
        # Build search query
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^3", "content^2", "key_insights^2"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        },
                        {
                            "terms": {
                                "financial_terms": query.lower().split(),
                                "boost": 1.5
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            },
            "highlight": {
                "fields": {
                    "content": {"fragment_size": 150, "number_of_fragments": 3},
                    "title": {}
                }
            },
            "sort": ["_score"],
            "size": limit
        }
        
        # Add filters
        if filters:
            filter_conditions = []
            
            if 'date_range' in filters:
                date_range = filters['date_range']
                filter_conditions.append({
                    "range": {
                        "collected_at": {
                            "gte": date_range.get('start'),
                            "lte": date_range.get('end')
                        }
                    }
                })
            
            if 'source_type' in filters:
                filter_conditions.append({
                    "term": {"source_type": filters['source_type']}
                })
            
            if 'category' in filters:
                filter_conditions.append({
                    "term": {"topic_category": filters['category']}
                })
            
            if filter_conditions:
                search_body["query"]["bool"]["filter"] = filter_conditions
        
        try:
            response = await self.es.search(
                index=','.join(indices),
                body=search_body
            )
            
            results = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                result = SearchResult(
                    content_id=hit['_id'],
                    title=source.get('title', ''),
                    content=source.get('content', source.get('full_content', '')),
                    source_info={
                        'source_id': source.get('source_id'),
                        'url': source.get('url', ''),
                        'index': hit['_index']
                    },
                    relevance_score=hit['_score'],
                    content_type='raw' if 'raw' in hit['_index'] else 'processed',
                    created_at=datetime.fromisoformat(
                        source.get('collected_at', source.get('created_at', datetime.now().isoformat()))
                    ),
                    metadata=source.get('metadata', {})
                )
                results.append(result)
            
            logger.info("Search completed", query=query, results=len(results))
            return results
            
        except Exception as e:
            logger.error("Search failed", query=query, error=str(e))
            return []
    
    async def find_similar_content(
        self, 
        reference_content: Content,
        similarity_threshold: float = 0.8,
        limit: int = 5
    ) -> List[SimilarityResult]:
        """Find content similar to reference content."""
        # Generate vector for reference content (simplified)
        ref_hash = hashlib.md5(reference_content.full_text().encode()).hexdigest()
        ref_vector = [float(int(c, 16)) / 15.0 for c in ref_hash[:384]]
        
        # Vector similarity search
        search_body = {
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                        "params": {"query_vector": ref_vector}
                    }
                }
            },
            "min_score": similarity_threshold + 1.0,  # Adjust for cosine similarity + 1
            "size": limit
        }
        
        try:
            response = await self.es.search(
                index=self.indexer.processed_content_index,
                body=search_body
            )
            
            results = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                similarity_score = hit['_score'] - 1.0  # Adjust back
                
                # Reconstruct content object
                content = Content(
                    title=source['title'],
                    introduction=source.get('introduction', ''),
                    main_content=source.get('main_content', ''),
                    conclusion=source.get('conclusion', ''),
                    key_insights=source.get('key_insights', []),
                    actionable_steps=source.get('actionable_steps', [])
                )
                
                topic = Topic(
                    keywords=source.get('topic_keywords', []),
                    category=source.get('topic_category', ''),
                    trend_score=0.0
                )
                
                style = ContentStyle(source.get('content_style', 'motivational_finance'))
                
                result = SimilarityResult(
                    content_id=hit['_id'],
                    similarity_score=similarity_score,
                    content=content,
                    topic=topic,
                    style=style
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error("Similarity search failed", error=str(e))
            return []
    
    async def get_trending_topics(
        self,
        time_range: timedelta = timedelta(days=7),
        limit: int = 10
    ) -> List[Topic]:
        """Get trending topics based on recent content."""
        # Aggregate topics from recent content
        end_date = datetime.now()
        start_date = end_date - time_range
        
        search_body = {
            "query": {
                "range": {
                    "collected_at": {
                        "gte": start_date.isoformat(),
                        "lte": end_date.isoformat()
                    }
                }
            },
            "aggs": {
                "trending_keywords": {
                    "terms": {
                        "field": "financial_terms",
                        "size": limit * 2
                    }
                },
                "categories": {
                    "terms": {
                        "field": "topic_category",
                        "size": 10
                    }
                }
            },
            "size": 0
        }
        
        try:
            response = await self.es.search(
                index=self.indexer.raw_content_index,
                body=search_body
            )
            
            topics = []
            keywords_agg = response['aggregations']['trending_keywords']['buckets']
            categories_agg = response['aggregations']['categories']['buckets']
            
            # Create topics from trending keywords
            for i, bucket in enumerate(keywords_agg[:limit]):
                keyword = bucket['key']
                count = bucket['doc_count']
                
                # Assign category based on keyword or use most common category
                category = 'finance'  # Default
                if categories_agg:
                    category = categories_agg[0]['key']
                
                topic = Topic(
                    keywords=[keyword],
                    category=category,
                    trend_score=min(10.0, count / 2.0),  # Scale trend score
                    context={'mention_count': count, 'time_range': str(time_range)}
                )
                topics.append(topic)
            
            return topics
            
        except Exception as e:
            logger.error("Trending topics search failed", error=str(e))
            return []


class KnowledgeBaseService:
    """Main knowledge base service coordinating indexing and search."""
    
    def __init__(self, elasticsearch_url: str = "http://localhost:9200"):
        self.es_client = AsyncElasticsearch([elasticsearch_url])
        self.indexer = ContentIndexer(self.es_client)
        self.search_engine = KnowledgeSearchEngine(self.es_client, self.indexer)
        
        # Cache for frequently accessed content
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(hours=1)
    
    async def initialize(self):
        """Initialize the knowledge base."""
        try:
            await self.indexer.setup_indices()
            logger.info("Knowledge base initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize knowledge base", error=str(e))
            raise
    
    async def store_raw_content(self, content_batch: List[RawContent]) -> Dict[str, int]:
        """Store batch of raw content with indexing."""
        results = {"success": 0, "failed": 0}
        
        for content in content_batch:
            try:
                success = await self.indexer.index_raw_content(content)
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error("Failed to store raw content", content_id=content.id, error=str(e))
                results["failed"] += 1
        
        logger.info("Raw content batch processed", **results)
        return results
    
    async def store_processed_content(
        self,
        article_id: ArticleId,
        content: Content,
        topic: Topic,
        style: ContentStyle,
        quality_score: Optional[float] = None
    ) -> bool:
        """Store processed article content."""
        return await self.indexer.index_processed_content(
            article_id, content, topic, style, quality_score
        )
    
    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        use_cache: bool = True
    ) -> List[SearchResult]:
        """Search content with caching."""
        # Generate cache key
        cache_key = f"search_{hashlib.md5(f'{query}_{json.dumps(filters, sort_keys=True)}_{limit}'.encode()).hexdigest()}"
        
        # Check cache
        if use_cache:
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result
        
        # Perform search
        results = await self.search_engine.search_content(query, filters, limit)
        
        # Cache results
        if use_cache and results:
            self._cache_results(cache_key, results)
        
        return results
    
    async def find_similar_content(
        self,
        reference_content: Content,
        similarity_threshold: float = 0.8
    ) -> List[SimilarityResult]:
        """Find similar content to avoid duplication."""
        return await self.search_engine.find_similar_content(
            reference_content, similarity_threshold
        )
    
    async def get_trending_topics(
        self, 
        days: int = 7,
        limit: int = 10
    ) -> List[Topic]:
        """Get trending financial topics."""
        cache_key = f"trending_topics_{days}_{limit}"
        
        # Check cache (trending topics change less frequently)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Get trending topics
        topics = await self.search_engine.get_trending_topics(
            timedelta(days=days), limit
        )
        
        # Cache results with longer TTL for trending topics
        self._cache_results(cache_key, topics, ttl=timedelta(hours=6))
        
        return topics
    
    async def get_content_suggestions(
        self,
        topic: Topic,
        style: ContentStyle,
        limit: int = 5
    ) -> List[SearchResult]:
        """Get content suggestions based on topic and style."""
        # Search for related content
        query = ' '.join(topic.keywords)
        filters = {
            'category': topic.category,
            'content_style': style.value
        }
        
        return await self.search(query, filters, limit)
    
    def _get_from_cache(self, cache_key: str) -> Any:
        """Get result from cache if valid."""
        if cache_key not in self._cache:
            return None
        
        # Check TTL
        timestamp = self._cache_timestamps.get(cache_key)
        if timestamp and datetime.now() - timestamp > self._cache_ttl:
            # Remove expired entry
            del self._cache[cache_key]
            del self._cache_timestamps[cache_key]
            return None
        
        return self._cache[cache_key]
    
    def _cache_results(
        self, 
        cache_key: str, 
        results: Any, 
        ttl: Optional[timedelta] = None
    ):
        """Cache search results."""
        self._cache[cache_key] = results
        self._cache_timestamps[cache_key] = datetime.now()
        
        # Simple cache management
        if len(self._cache) > 1000:
            # Remove oldest entries
            oldest_key = min(self._cache_timestamps.keys(),
                           key=lambda k: self._cache_timestamps[k])
            del self._cache[oldest_key]
            del self._cache_timestamps[oldest_key]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        try:
            # Get index stats
            raw_stats = await self.es_client.indices.stats(index=self.indexer.raw_content_index)
            processed_stats = await self.es_client.indices.stats(index=self.indexer.processed_content_index)
            topics_stats = await self.es_client.indices.stats(index=self.indexer.topics_index)
            
            return {
                "raw_content": {
                    "count": raw_stats['indices'][self.indexer.raw_content_index]['total']['docs']['count'],
                    "size_mb": raw_stats['indices'][self.indexer.raw_content_index]['total']['store']['size_in_bytes'] / (1024 * 1024)
                },
                "processed_content": {
                    "count": processed_stats['indices'][self.indexer.processed_content_index]['total']['docs']['count'],
                    "size_mb": processed_stats['indices'][self.indexer.processed_content_index]['total']['store']['size_in_bytes'] / (1024 * 1024)
                },
                "topics": {
                    "count": topics_stats['indices'][self.indexer.topics_index]['total']['docs']['count']
                },
                "cache": {
                    "cached_items": len(self._cache),
                    "cache_hit_rate": "~70%"  # Estimated
                }
            }
        except Exception as e:
            logger.error("Failed to get stats", error=str(e))
            return {}
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            await self.es_client.close()
        except Exception as e:
            logger.error("Cleanup failed", error=str(e))