from typing import Optional

from app.config import REDIS_URL

_redis_client = None


def get_redis_client():
    """
    Lazily create and return an async Redis client.
    Import is delayed so the app can start even if redis package is not installed
    and Redis is not used yet.
    """
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio as redis  # type: ignore
        except Exception as exc:
            raise RuntimeError(
                "Redis client is not available. Install the 'redis' package to use Redis features."
            ) from exc

        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


async def close_redis_client() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None

