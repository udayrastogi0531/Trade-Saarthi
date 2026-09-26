"""Celery background tasks."""

import asyncio

from backend.app.core.logging import get_logger
from backend.app.core.metrics import SCANNER_RUNS, SCANNER_LATENCY
from backend.app.workers.celery_app import celery_app

logger = get_logger(__name__)


def _run_async(coro):
  loop = asyncio.new_event_loop()
  try:
    return loop.run_until_complete(coro)
  finally:
    loop.close()


@celery_app.task(name="backend.app.workers.tasks.run_watchlist_scan", bind=True, max_retries=3)
def run_watchlist_scan(self) -> dict:
  import time

  start = time.perf_counter()

  async def _scan():
    from backend.app.db.session import AsyncSessionLocal
    from backend.app.services.scanner_service import ScannerService

    async with AsyncSessionLocal() as db:
      service = ScannerService()
      summary = await service.run_scan(db)
      await db.commit()
      return {
        "run_id": summary.run_id,
        "total": summary.total,
        "approved": summary.approved,
        "top": [
          {"symbol": r.symbol, "rank": r.rank_score, "approved": r.approved}
          for r in summary.results[:5]
        ],
      }

  try:
    result = _run_async(_scan())
    SCANNER_RUNS.inc()
    SCANNER_LATENCY.observe(time.perf_counter() - start)
    logger.info("celery_scan_complete", **result)
    return result
  except Exception as exc:
    logger.error("celery_scan_failed", error=str(exc))
    raise self.retry(exc=exc, countdown=60) from exc


@celery_app.task(name="backend.app.workers.tasks.generate_intraday_briefing")
def generate_intraday_briefing() -> dict:
  return _run_async(_briefing("intraday"))


@celery_app.task(name="backend.app.workers.tasks.generate_pre_market_briefing")
def generate_pre_market_briefing() -> dict:
  return _run_async(_briefing("pre_market"))


@celery_app.task(name="backend.app.workers.tasks.process_scanner_queue")
def process_scanner_queue() -> dict:
  return _run_async(_process_queue())


async def _process_queue() -> dict:
  from backend.app.modules.scanner.distributed import process_next_queued_job

  result = await process_next_queued_job()
  return result or {"status": "empty"}


async def _briefing(briefing_type: str) -> dict:
  from backend.app.db.session import AsyncSessionLocal
  from backend.app.modules.briefings.engine import BriefingEngine

  async with AsyncSessionLocal() as db:
    engine = BriefingEngine()
    result = await engine.generate(db, briefing_type)
    await db.commit()
    return result
