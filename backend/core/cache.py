"""
ArogyaMitra AI - Cache Layer
Redis-backed TTL cache implementation per PRODUCTION_BACKEND.md §4.3.
Falls back to no-op if Redis is not available (local dev).
"""

import json
import logging
from typing import Optional, Any
from backend.core.redis_client import get_redis_client
from backend.core.logger import logger

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = {
    "risk_score": 300,
    "clinical_params": 180,
    "reminders_today": 60,
    "family_profiles": 600,
    "active_model": 3600,
    "drug_interactions": 300,
}


class ArogyaCache:
    """Redis-backed cache with TTL support."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self._redis_available = redis_client is not None
    
    def _key(self, cache_name: str, key: str) -> str:
        """Generate full cache key with namespace."""
        return f"arogya:{cache_name}:{key}"
    
    async def get(self, cache_name: str, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._redis_available:
            logger.debug(f"[Cache] DISABLED | {cache_name} | {key}")
            return None
        try:
            raw = await self.redis.get(self._key(cache_name, key))
            if raw is None:
                logger.debug(f"[Cache] MISS | {cache_name} | {key}")
                return None
            logger.debug(f"[Cache] HIT | {cache_name} | {key}")
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"[Cache] ERROR on get: {e}")
            return None
    
    async def set(self, cache_name: str, key: str, value: Any) -> None:
        """Set value in cache with TTL."""
        if not self._redis_available:
            logger.debug(f"[Cache] DISABLED | {cache_name} | {key}")
            return
        try:
            ttl = CACHE_TTL_SECONDS.get(cache_name, 300)
            await self.redis.setex(self._key(cache_name, key), ttl, json.dumps(value))
            logger.debug(f"[Cache] SET | {cache_name} | {key} | ttl={ttl}s")
        except Exception as e:
            logger.warning(f"[Cache] ERROR on set: {e}")
    
    async def invalidate(self, cache_name: str, key: str) -> None:
        """Invalidate a specific cache key."""
        if not self._redis_available:
            return
        try:
            await self.redis.delete(self._key(cache_name, key))
            logger.debug(f"[Cache] INVALIDATE | {cache_name} | {key}")
        except Exception as e:
            logger.warning(f"[Cache] ERROR on invalidate: {e}")
    
    async def invalidate_user(self, user_id: str) -> None:
        """Invalidate all cache keys for a specific user."""
        if not self._redis_available:
            return
        try:
            pattern = f"arogya:*:*{user_id}*"
            async for k in self.redis.scan_iter(match=pattern):
                await self.redis.delete(k)
            logger.debug(f"[Cache] INVALIDATE_USER | {user_id}")
        except Exception as e:
            logger.warning(f"[Cache] ERROR on invalidate_user: {e}")


def get_cache() -> ArogyaCache:
    """Dependency for getting cache instance."""
    try:
        redis_client = get_redis_client()
        return ArogyaCache(redis_client)
    except Exception as e:
        logger.warning(f"[Cache] Redis not available, caching disabled: {e}")
        return ArogyaCache(None)
