"""Redis-backed scanner job queue for distributed workers."""

import json
import uuid
from datetime import datetime
from typing import Any

from backend.app.core.logging import get_logger
from backend.app.services.redis_client import cache_get, cache_set, get_redis

logger = get_logger(__name__)

QUEUE_KEY = "scanner:job_queue"
JOB_PREFIX = "scanner:job:"
JOB_TTL = 86400
_memory_queue: list[str] = []


class ScannerJobQueue:
  async def enqueue(
    self,
    symbols: list[str] | None,
    account_id: int = 1,
    watchlist_name: str = "default",
  ) -> str:
    job_id = str(uuid.uuid4())
    payload = {
      "job_id": job_id,
      "symbols": symbols,
      "account_id": account_id,
      "watchlist_name": watchlist_name,
      "enqueued_at": datetime.utcnow().isoformat(),
      "status": "pending",
    }
    client = await get_redis()
    if client:
      await client.lpush(QUEUE_KEY, job_id)
    else:
      _memory_queue.insert(0, job_id)
    await cache_set(f"{JOB_PREFIX}{job_id}", json.dumps(payload), ttl_seconds=JOB_TTL)
    logger.info("scanner_job_enqueued", job_id=job_id)
    return job_id

  async def dequeue(self) -> dict[str, Any] | None:
    client = await get_redis()
    job_id = None
    if client:
      raw = await client.brpop(QUEUE_KEY, timeout=1)
      if raw:
        job_id = raw[1] if isinstance(raw, (list, tuple)) else raw
    elif _memory_queue:
      job_id = _memory_queue.pop()
    if not job_id:
      return None
    data = await cache_get(f"{JOB_PREFIX}{job_id}")
    if not data:
      return None
    return json.loads(data)

  async def update_status(self, job_id: str, status: str, result: dict | None = None) -> None:
    raw = await cache_get(f"{JOB_PREFIX}{job_id}")
    if not raw:
      return
    payload = json.loads(raw)
    payload["status"] = status
    if result:
      payload["result"] = result
    payload["updated_at"] = datetime.utcnow().isoformat()
    await cache_set(f"{JOB_PREFIX}{job_id}", json.dumps(payload, default=str), ttl_seconds=JOB_TTL)

  async def get_job(self, job_id: str) -> dict[str, Any] | None:
    raw = await cache_get(f"{JOB_PREFIX}{job_id}")
    return json.loads(raw) if raw else None
