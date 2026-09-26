"""Database-backed watchlist management for the distributed scanner."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models import Watchlist

logger = get_logger(__name__)


class WatchlistService:
  async def get_active_symbols(self, db: AsyncSession, name: str = "default") -> list[str]:
    result = await db.execute(
      select(Watchlist).where(Watchlist.name == name, Watchlist.is_active.is_(True))
    )
    row = result.scalar_one_or_none()
    if row and row.symbols:
      return [str(s).upper() for s in row.symbols]
    return get_settings().watchlist

  async def get_interval_minutes(self, db: AsyncSession, name: str = "default") -> int:
    result = await db.execute(select(Watchlist).where(Watchlist.name == name))
    row = result.scalar_one_or_none()
    return row.scan_interval_minutes if row else get_settings().scanner_interval_minutes

  async def list_watchlists(self, db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Watchlist).order_by(Watchlist.name))
    return [
      {
        "id": w.id,
        "name": w.name,
        "symbols": w.symbols,
        "is_active": w.is_active,
        "scan_interval_minutes": w.scan_interval_minutes,
      }
      for w in result.scalars().all()
    ]

  async def upsert(
    self,
    db: AsyncSession,
    name: str,
    symbols: list[str],
    scan_interval_minutes: int = 3,
    is_active: bool = True,
  ) -> Watchlist:
    result = await db.execute(select(Watchlist).where(Watchlist.name == name))
    row = result.scalar_one_or_none()
    clean = [s.strip().upper() for s in symbols if s.strip()]
    if row:
      row.symbols = clean
      row.scan_interval_minutes = scan_interval_minutes
      row.is_active = is_active
    else:
      row = Watchlist(
        name=name,
        symbols=clean,
        scan_interval_minutes=scan_interval_minutes,
        is_active=is_active,
      )
      db.add(row)
    await db.flush()
    logger.info("watchlist_upsert", name=name, symbols=len(clean))
    return row
