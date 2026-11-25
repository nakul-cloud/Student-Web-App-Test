from qdrant_client import AsyncQdrantClient
from app.config.settings import settings
from app.utils.logger import logger

_qdrant_client: AsyncQdrantClient | None = None


def get_qdrant_client() -> AsyncQdrantClient:
    """Singleton AsyncQdrantClient."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = AsyncQdrantClient(url=settings.qdrant_url)
        logger.info(f"[Qdrant] Initialized AsyncQdrantClient at {settings.qdrant_url}")
    return _qdrant_client


async def close_qdrant_client():
    """Close Qdrant client connection."""
    global _qdrant_client
    if _qdrant_client is not None:
        await _qdrant_client.close()
        _qdrant_client = None
        logger.info("[Qdrant] Client connection closed.")
