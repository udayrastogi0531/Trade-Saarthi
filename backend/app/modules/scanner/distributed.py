"""Distributed scanner worker — processes Redis queue jobs."""

from backend.app.core.logging import get_logger
from backend.app.db.session import AsyncSessionLocal
from backend.app.modules.scanner.queue import ScannerJobQueue
from backend.app.services.scanner_service import ScannerService

logger = get_logger(__name__)


async def process_next_queued_job() -> dict | None:
  """Pull one job from queue and execute. Returns None if queue empty."""
  queue = ScannerJobQueue()
  job = await queue.dequeue()
  if not job:
    return None

  service = ScannerService()
  async with AsyncSessionLocal() as db:
    try:
      result = await service.process_queued_job(db, job)
      await db.commit()
      logger.info("distributed_scan_job_done", job_id=job["job_id"])
      return result
    except Exception as exc:
      await db.rollback()
      logger.error("distributed_scan_job_failed", job_id=job.get("job_id"), error=str(exc))
      raise
