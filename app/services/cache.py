"""Multi-layer caching service for cost optimization and performance."""

import json
import hashlib
import pickle
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

import aioredis
import structlog

from app.core.config import settings

logger = structlog.get_logger()


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    data: Any
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    size_bytes: int = 0
    metadata: Dict[str, Any] = None


class CacheBackend(ABC):
    """Abstract cache backend interface."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        pass
    
    @abstractmethod
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set key-value with optional TTL in seconds."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        pass


class RedisBackend(CacheBackend):
    """Redis cache backend implementation."""
    
    def __init__(self, redis_url: str = None, db: int = 0):
        self.redis_url = redis_url or settings.redis.url
        self.db = db
        self.redis: Optional[aioredis.Redis] = None
    
    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if not self.redis:
            self.redis = aioredis.from_url(
                self.redis_url,
                db=self.db,
                encoding='utf-8',
                decode_responses=False  # We'll handle serialization ourselves
            )
        return self.redis
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        try:
            redis = await self._get_redis()
            data = await redis.get(key)
            
            if data is None:
                return None
            
            # Increment hit count
            await redis.hincrby(f"{key}:meta", "hit_count", 1)
            await redis.hset(f"{key}:meta", "last_accessed", datetime.now().isoformat())
            
            # Deserialize data
            return pickle.loads(data)
            
        except Exception as e:
            logger.warning("Redis get failed", key=key, error=str(e))
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in Redis."""
        try:
            redis = await self._get_redis()
            
            # Serialize data
            serialized_data = pickle.dumps(value)
            
            # Store main data
            if ttl:
                await redis.setex(key, ttl, serialized_data)
            else:
                await redis.set(key, serialized_data)
            
            # Store metadata
            metadata = {
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(seconds=ttl)).isoformat() if ttl else "",
                "hit_count": 0,
                "size_bytes": len(serialized_data),
                "last_accessed": datetime.now().isoformat()
            }
            
            await redis.hset(f"{key}:meta", mapping=metadata)
            if ttl:
                await redis.expire(f"{key}:meta", ttl)
            
            return True
            
        except Exception as e:
            logger.error("Redis set failed", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            redis = await self._get_redis()
            deleted = await redis.delete(key, f"{key}:meta")
            return deleted > 0
        except Exception as e:
            logger.error("Redis delete failed", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            redis = await self._get_redis()
            return await redis.exists(key) > 0
        except Exception as e:
            logger.warning("Redis exists check failed", key=key, error=str(e))
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        try:
            redis = await self._get_redis()
            keys = await redis.keys(pattern)
            if keys:
                return await redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error("Redis pattern clear failed", pattern=pattern, error=str(e))
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        try:
            redis = await self._get_redis()
            info = await redis.info()
            
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) / 
                    max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)) * 100, 2
                )
            }
        except Exception as e:
            logger.error("Failed to get Redis stats", error=str(e))
            return {}
    
    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()


class MemoryBackend(CacheBackend):
    """In-memory cache backend for development/testing."""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        entry = self.cache.get(key)
        if not entry:
            return None
        
        # Check expiration
        if entry.expires_at and datetime.now() > entry.expires_at:
            del self.cache[key]
            return None
        
        # Update hit count
        entry.hit_count += 1
        return entry.data
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in memory cache."""
        # Evict if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_lru()
        
        expires_at = datetime.now() + timedelta(seconds=ttl) if ttl else None
        
        self.cache[key] = CacheEntry(
            key=key,
            data=value,
            created_at=datetime.now(),
            expires_at=expires_at,
            size_bytes=len(str(value).encode())
        )
        
        return True
    
    def _evict_lru(self):
        """Evict least recently used item."""
        if not self.cache:
            return
        
        # Simple LRU: remove oldest entry
        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].created_at)
        del self.cache[oldest_key]
    
    async def delete(self, key: str) -> bool:
        """Delete key from memory cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in memory cache."""
        entry = self.cache.get(key)
        if not entry:
            return False
        
        # Check expiration
        if entry.expires_at and datetime.now() > entry.expires_at:
            del self.cache[key]
            return False
        
        return True
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern."""
        import re
        pattern_regex = re.compile(pattern.replace('*', '.*'))
        
        keys_to_delete = [
            key for key in self.cache.keys() 
            if pattern_regex.match(key)
        ]
        
        for key in keys_to_delete:
            del self.cache[key]
        
        return len(keys_to_delete)


class CacheManager:
    """Multi-layer cache manager with intelligent routing."""
    
    def __init__(self):
        # Initialize backends
        self.redis_backend = RedisBackend(db=settings.redis.cache_db)
        self.memory_backend = MemoryBackend(max_size=1000)
        
        # Cache layers configuration
        self.layers = {
            # Fast in-memory cache for frequently accessed items
            "memory": {
                "backend": self.memory_backend,
                "ttl": 300,  # 5 minutes
                "max_size": 1000
            },
            # Redis for distributed caching
            "redis": {
                "backend": self.redis_backend,
                "ttl": 3600,  # 1 hour
                "max_size": None
            }
        }
        
        # Cache key prefixes for different data types
        self.key_prefixes = {
            "ai_content": "ai:content:",
            "trending_topics": "trends:",
            "search_results": "search:",
            "article_content": "article:",
            "source_data": "source:",
            "quality_assessment": "quality:",
        }
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0
        }
    
    def _generate_key(self, cache_type: str, identifier: str) -> str:
        """Generate cache key with prefix."""
        prefix = self.key_prefixes.get(cache_type, "general:")
        # Hash long identifiers to keep keys manageable
        if len(identifier) > 100:
            identifier = hashlib.md5(identifier.encode()).hexdigest()
        return f"{prefix}{identifier}"
    
    async def get(
        self, 
        cache_type: str, 
        identifier: str,
        layer: str = "memory"
    ) -> Optional[Any]:
        """Get value from cache with layer preference."""
        key = self._generate_key(cache_type, identifier)
        backend = self.layers[layer]["backend"]
        
        try:
            value = await backend.get(key)
            if value is not None:
                self.stats["hits"] += 1
                logger.debug("Cache hit", key=key, layer=layer)
                return value
            else:
                self.stats["misses"] += 1
                logger.debug("Cache miss", key=key, layer=layer)
                return None
                
        except Exception as e:
            logger.warning("Cache get failed", key=key, layer=layer, error=str(e))
            self.stats["misses"] += 1
            return None
    
    async def get_multi_layer(
        self, 
        cache_type: str, 
        identifier: str
    ) -> Optional[Any]:
        """Get value from multiple cache layers (memory -> redis)."""
        # Try memory cache first
        value = await self.get(cache_type, identifier, "memory")
        if value is not None:
            return value
        
        # Try Redis cache
        value = await self.get(cache_type, identifier, "redis")
        if value is not None:
            # Promote to memory cache for faster future access
            await self.set(cache_type, identifier, value, "memory")
            return value
        
        return None
    
    async def set(
        self,
        cache_type: str,
        identifier: str,
        value: Any,
        layer: str = "redis",
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache layer."""
        key = self._generate_key(cache_type, identifier)
        backend = self.layers[layer]["backend"]
        
        # Use default TTL if not specified
        if ttl is None:
            ttl = self.layers[layer]["ttl"]
        
        try:
            success = await backend.set(key, value, ttl)
            if success:
                self.stats["sets"] += 1
                logger.debug("Cache set", key=key, layer=layer, ttl=ttl)
            return success
            
        except Exception as e:
            logger.error("Cache set failed", key=key, layer=layer, error=str(e))
            return False
    
    async def set_multi_layer(
        self,
        cache_type: str,
        identifier: str,
        value: Any,
        memory_ttl: int = 300,
        redis_ttl: int = 3600
    ) -> bool:
        """Set value in multiple cache layers."""
        # Set in both layers
        memory_success = await self.set(cache_type, identifier, value, "memory", memory_ttl)
        redis_success = await self.set(cache_type, identifier, value, "redis", redis_ttl)
        
        return memory_success or redis_success  # Success if at least one succeeds
    
    async def delete(self, cache_type: str, identifier: str) -> bool:
        """Delete from all cache layers."""
        key = self._generate_key(cache_type, identifier)
        
        deleted = False
        for layer_name, layer_config in self.layers.items():
            try:
                success = await layer_config["backend"].delete(key)
                deleted = deleted or success
            except Exception as e:
                logger.warning("Cache delete failed", key=key, layer=layer_name, error=str(e))
        
        if deleted:
            self.stats["deletes"] += 1
        
        return deleted
    
    async def clear_pattern(
        self, 
        cache_type: str, 
        pattern: str = "*"
    ) -> Dict[str, int]:
        """Clear cache entries matching pattern."""
        full_pattern = self._generate_key(cache_type, pattern)
        results = {}
        
        for layer_name, layer_config in self.layers.items():
            try:
                count = await layer_config["backend"].clear_pattern(full_pattern)
                results[layer_name] = count
            except Exception as e:
                logger.error("Cache clear failed", pattern=full_pattern, layer=layer_name, error=str(e))
                results[layer_name] = 0
        
        return results
    
    async def cache_ai_content(
        self, 
        topic_hash: str, 
        content_style: str,
        content: Any,
        cost_saved: float = 0.0
    ) -> bool:
        """Cache AI-generated content with cost tracking."""
        identifier = f"{topic_hash}:{content_style}"
        
        # Add cost metadata
        cached_content = {
            "content": content,
            "cached_at": datetime.now().isoformat(),
            "cost_saved": cost_saved,
            "cache_type": "ai_content"
        }
        
        # Cache for 7 days (long TTL for expensive AI content)
        return await self.set_multi_layer(
            "ai_content", 
            identifier, 
            cached_content,
            memory_ttl=1800,  # 30 minutes in memory
            redis_ttl=7 * 24 * 3600  # 7 days in Redis
        )
    
    async def cache_trending_topics(
        self, 
        date_key: str, 
        topics: List[Any]
    ) -> bool:
        """Cache trending topics analysis."""
        return await self.set_multi_layer(
            "trending_topics",
            date_key,
            topics,
            memory_ttl=1800,  # 30 minutes in memory
            redis_ttl=6 * 3600  # 6 hours in Redis
        )
    
    async def cache_search_results(
        self,
        query_hash: str,
        results: List[Any]
    ) -> bool:
        """Cache search results."""
        return await self.set_multi_layer(
            "search_results",
            query_hash,
            results,
            memory_ttl=600,   # 10 minutes in memory
            redis_ttl=3600    # 1 hour in Redis
        )
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        total_operations = sum([
            self.stats["hits"], 
            self.stats["misses"], 
            self.stats["sets"], 
            self.stats["deletes"]
        ])
        
        hit_rate = (
            self.stats["hits"] / max(1, self.stats["hits"] + self.stats["misses"]) * 100
        )
        
        base_stats = {
            "operations": {
                "total": total_operations,
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "sets": self.stats["sets"],
                "deletes": self.stats["deletes"],
                "hit_rate_percent": round(hit_rate, 2)
            }
        }
        
        # Get Redis stats if available
        try:
            redis_stats = await self.redis_backend.get_stats()
            base_stats["redis"] = redis_stats
        except Exception as e:
            logger.warning("Failed to get Redis stats", error=str(e))
        
        # Memory cache stats
        base_stats["memory"] = {
            "cached_items": len(self.memory_backend.cache),
            "max_size": self.memory_backend.max_size,
            "utilization_percent": round(
                len(self.memory_backend.cache) / self.memory_backend.max_size * 100, 2
            )
        }
        
        return base_stats
    
    async def optimize_cache(self) -> Dict[str, Any]:
        """Perform cache optimization and cleanup."""
        optimization_results = {
            "expired_cleaned": 0,
            "lru_evicted": 0,
            "cost_saved_estimate": 0.0
        }
        
        try:
            # Clear expired entries
            expired_patterns = [
                "ai:content:*",
                "trends:*", 
                "search:*"
            ]
            
            for pattern in expired_patterns:
                cleared = await self.redis_backend.clear_pattern(f"{pattern}:expired")
                optimization_results["expired_cleaned"] += cleared.get("redis", 0)
            
            # Estimate cost savings from cache hits
            # Assuming $0.01 per AI content generation avoided
            ai_content_hits = self.stats["hits"] * 0.7  # Estimate 70% are AI content
            optimization_results["cost_saved_estimate"] = ai_content_hits * 0.01
            
            logger.info("Cache optimization completed", **optimization_results)
            
        except Exception as e:
            logger.error("Cache optimization failed", error=str(e))
        
        return optimization_results
    
    async def cleanup(self):
        """Cleanup cache connections."""
        try:
            await self.redis_backend.close()
        except Exception as e:
            logger.error("Failed to cleanup cache", error=str(e))


# Global cache manager instance
cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance."""
    global cache_manager
    if cache_manager is None:
        cache_manager = CacheManager()
    return cache_manager