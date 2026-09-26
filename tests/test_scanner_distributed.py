from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.config import get_settings
from backend.app.modules.scanner.queue import ScannerJobQueue
from backend.app.modules.scanner.watchlist_service import WatchlistService


@pytest.mark.asyncio
async def test_watchlist_env_fallback():
  """When no DB row exists, symbols fall back to configured watchlist."""
  mock_result = MagicMock()
  mock_result.scalar_one_or_none.return_value = None
  db = AsyncMock()
  db.execute = AsyncMock(return_value=mock_result)

  symbols = await WatchlistService().get_active_symbols(db, "missing")
  assert symbols == get_settings().watchlist


@pytest.mark.asyncio
async def test_watchlist_upsert_and_symbols():
  from backend.app.db.session import AsyncSessionLocal

  try:
    async with AsyncSessionLocal() as db:
      svc = WatchlistService()
      await svc.upsert(db, "test_wl", ["RELIANCE", "TCS"], scan_interval_minutes=5)
      symbols = await svc.get_active_symbols(db, "test_wl")
      await db.commit()
  except (ConnectionRefusedError, OSError) as exc:
    pytest.skip(f"Postgres not available: {exc}")

  assert "RELIANCE" in symbols
  assert "TCS" in symbols


@pytest.mark.asyncio
async def test_scanner_job_enqueue():
  queue = ScannerJobQueue()
  job_id = await queue.enqueue(["INFY"], account_id=1, watchlist_name="default")
  assert job_id
  job = await queue.get_job(job_id)
  assert job is not None
  assert job["status"] == "pending"
