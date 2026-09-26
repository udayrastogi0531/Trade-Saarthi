"""In-process scanner scheduler — uses distributed ScannerService."""

from backend.app.core.logging import get_logger
from backend.app.db.session import AsyncSessionLocal
from backend.app.services.scanner_service import ScannerService

logger = get_logger(__name__)


async def run_scheduled_scan() -> None:
  try:
    async with AsyncSessionLocal() as db:
      service = ScannerService()
      summary = await service.run_scan(db, watchlist_name="default")
      await db.commit()
      logger.info(
        "scheduled_scan_complete",
        run_id=summary.run_id,
        approved=summary.approved,
        total=summary.total,
      )
  except Exception as exc:
    logger.error("scheduled_scan_failed", error=str(exc))
