import redis.asyncio as aioredis
from app.config.settings import settings
from app.utils.logger import logger

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Singleton async Redis connection pool."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await _redis_client.ping()
            logger.info("[Redis] Successfully connected to Redis pool.")
        except Exception as e:
            logger.error(f"[Redis] Failed to connect: {e}")
            raise
    return _redis_client


async def close_redis():
    """Graceful shutdown for Redis client."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("[Redis] Connection closed.")
