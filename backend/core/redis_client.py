"""
ArogyaMitra AI - Redis Client
Singleton Redis connection for caching.
"""

import redis.asyncio as redis
from backend.config import settings

_redis_client = None


def get_redis_client():
    """Get or create the Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return _redis_client
