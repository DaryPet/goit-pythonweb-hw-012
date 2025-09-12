import redis.asyncio as aioredis
from src.conf.config import settings

redis_client = aioredis.from_url(settings.REDIS_URL)
"""The main asynchronous Redis client instance."""


async def get_redis_client():
    """
    Returns the asynchronous Redis client instance.

    This function serves as a dependency for FastAPI endpoints that need
    to access the Redis database.

    Returns:
        redis.asyncio.Redis: The Redis client instance.
    """
    return redis_client
