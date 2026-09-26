"""Redis connection for caching — degrades gracefully when unavailable."""

import json
import time
from typing import Any

import redis.asyncio as redis
from redis.asyncio import Redis

from backend.app.config import get_settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)

_client: Redis | None = None
_redis_available: bool | None = None
_last_redis_connect_attempt: float = 0.0
REDIS_RECONNECT_INTERVAL_SEC: float = 30.0
_memory_cache: dict[str, tuple[str, float]] = {}


def _memory_get(key: str) -> str | None:
  entry = _memory_cache.get(key)
  if not entry:
    return None
  value, expires_at = entry
  if time.time() > expires_at:
    _memory_cache.pop(key, None)
    return None
  return value


def _memory_set(key: str, value: str, ttl_seconds: int) -> None:
  _memory_cache[key] = (value, time.time() + ttl_seconds)


async def _close_redis_client() -> None:
  global _client, _redis_available
  if _client is not None:
    try:
      await _client.aclose()
    except Exception as exc:
      logger.debug("redis_close_failed", error=str(exc))
  _client = None
  _redis_available = None


async def get_redis() -> Redis | None:
  global _client, _redis_available, _last_redis_connect_attempt
  now = time.time()
  if _redis_available is False:
    if now - _last_redis_connect_attempt < REDIS_RECONNECT_INTERVAL_SEC:
      return None
    _redis_available = None

  if _client is None:
    settings = get_settings()
    _last_redis_connect_attempt = now
    try:
      _client = redis.from_url(settings.redis_url, decode_responses=True)
      await _client.ping()
      _redis_available = True
    except Exception as exc:
      logger.warning("redis_unavailable", error=str(exc))
      _redis_available = False
      _client = None
      return None
  else:
    try:
      await _client.ping()
    except Exception as exc:
      logger.warning("redis_ping_failed_resetting", error=str(exc))
      await _close_redis_client()
      return None
  return _client


async def cache_get(key: str) -> str | None:
  client = await get_redis()
  if client is not None:
    try:
      value = await client.get(key)
      if value is not None:
        return value
    except Exception as exc:
      logger.warning("redis_get_failed", key=key, error=str(exc))
      await _close_redis_client()
  return _memory_get(key)


async def cache_set(key: str, value: str, ttl_seconds: int = 300) -> None:
  client = await get_redis()
  if client is not None:
    try:
      await client.setex(key, ttl_seconds, value)
      return
    except Exception as exc:
      logger.warning("redis_set_failed", key=key, error=str(exc))
      await _close_redis_client()
  _memory_set(key, value, ttl_seconds)


async def cache_json_get(key: str) -> Any | None:
  raw = await cache_get(key)
  if raw is None:
    return None
  return json.loads(raw)


async def cache_json_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
  await cache_set(key, json.dumps(value, default=str), ttl_seconds)
