"""Redis caching utilities for user data.

This module provides async functions for caching and retrieving user
data in Redis, using a cache-aside pattern to optimize frequent
user lookups and reduce database load.
"""

import json
from db import redis_client

CACHE_TTL = 1800  # 30 minutes

CACHE_KEY_USER = 'user:{user_id}'


async def cache_user(user_id: int, user_data: dict) -> None:
    """Cache user data in Redis with a TTL.

    Args:
        user_id: The user's unique identifier.
        user_data: Dictionary of user data to cache (will be JSON-serialized).
    """
    key = CACHE_KEY_USER.format(user_id=user_id)
    await redis_client.setex(key, CACHE_TTL, json.dumps(user_data, default=str))


async def get_cached_user(user_id: int) -> dict | None:
    """Retrieve cached user data from Redis.

    Args:
        user_id: The user's unique identifier.

    Returns:
        dict | None: The cached user data dictionary if found, None otherwise.
    """
    key = CACHE_KEY_USER.format(user_id=user_id)
    data = await redis_client.get(key)
    if data is None:
        return None
    return json.loads(data)


async def invalidate_user_cache(user_id: int) -> None:
    """Remove cached user data from Redis.

    Used to ensure cache consistency when user data is updated.

    Args:
        user_id: The user's unique identifier.
    """
    key = CACHE_KEY_USER.format(user_id=user_id)
    await redis_client.delete(key)