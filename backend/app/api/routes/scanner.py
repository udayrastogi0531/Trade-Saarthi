"""Distributed watchlist scanner API."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.db.models import ScannerRun
from backend.app.db.session import get_db
from backend.app.modules.scanner.queue import ScannerJobQueue
from backend.app.modules.scanner.watchlist_service import WatchlistService
from backend.app.services.scanner_service import ScannerService

router = APIRouter(prefix="/scanner", tags=["Scanner"])


class ScanRequest(BaseModel):
  symbols: list[str] | None = None
  account_id: int = 1
  watchlist_name: str = "default"
  async_job: bool = False


class WatchlistUpsert(BaseModel):
  name: str = Field(default="default", max_length=64)
  symbols: list[str]
  scan_interval_minutes: int = Field(default=3, ge=1, le=60)
  is_active: bool = True


@router.post("/run")
async def run_scanner(
  request: ScanRequest,
  db: AsyncSession = Depends(get_db),
) -> dict:
  """
  Run distributed market intelligence scan.

  Full pipeline per symbol: market data → TA → strategy → risk → AI →
  signal quality → structure → learning calibration → ranking → alerts.
  """
  service = ScannerService()

  if request.async_job:
    job_id = await service.enqueue_scan(
      request.symbols, request.account_id, request.watchlist_name
    )
    return {"status": "queued", "job_id": job_id}

  summary = await service.run_scan(
    db,
    request.symbols,
    request.account_id,
    request.watchlist_name,
  )

  health = await _run_health(db, summary.run_id)
  return _format_summary(summary, health)


@router.get("/jobs/{job_id}")
async def get_scan_job(job_id: str) -> dict:
  job = await ScannerJobQueue().get_job(job_id)
  if not job:
    raise HTTPException(status_code=404, detail="Job not found")
  return job


@router.get("/health")
async def scanner_health(
  limit: int = Query(10, le=50),
  db: AsyncSession = Depends(get_db),
) -> dict:
  """Scanner health monitoring — recent run latency and status."""
  result = await db.execute(
    select(ScannerRun).order_by(ScannerRun.started_at.desc()).limit(limit)
  )
  runs = result.scalars().all()
  if not runs:
    return {"status": "unknown", "runs": [], "message": "No scanner runs yet"}

  latest = runs[0]
  degraded_threshold = get_settings().scanner_health_degraded_latency_ms
  return {
    "status": latest.health_status,
    "latest_run_id": str(latest.run_id),
    "avg_latency_ms": float(latest.avg_latency_ms or 0),
    "degraded_threshold_ms": degraded_threshold,
    "runs": [
      {
        "run_id": str(r.run_id),
        "health": r.health_status,
        "symbols": r.symbols_scanned,
        "approved": r.approved_count,
        "avg_latency_ms": float(r.avg_latency_ms or 0),
        "errors": r.errors or [],
        "started_at": r.started_at.isoformat() if r.started_at else None,
      }
      for r in runs
    ],
  }


@router.get("/watchlist")
async def get_watchlist(db: AsyncSession = Depends(get_db)) -> dict:
  wl = WatchlistService()
  items = await wl.list_watchlists(db)
  settings = get_settings()
  return {
    "env_fallback": settings.watchlist,
    "interval_minutes": settings.scanner_interval_minutes,
    "watchlists": items,
  }


@router.put("/watchlist")
async def upsert_watchlist(
  body: WatchlistUpsert,
  db: AsyncSession = Depends(get_db),
) -> dict:
  row = await WatchlistService().upsert(
    db, body.name, body.symbols, body.scan_interval_minutes, body.is_active
  )
  return {"id": row.id, "name": row.name, "symbols": row.symbols}


@router.get("/feed")
async def scanner_signal_feed(
  limit: int = Query(10, le=50),
  approved_only: bool = Query(True),
  db: AsyncSession = Depends(get_db),
) -> dict:
  """Top ranked scanner results for dashboard feed."""
  from backend.app.db.models import ScannerLog

  query = select(ScannerLog).order_by(ScannerLog.rank_score.desc()).limit(limit)
  if approved_only:
    query = query.where(ScannerLog.approved.is_(True))
  result = await db.execute(query)
  logs = result.scalars().all()
  return {
    "items": [
      {
        "symbol": l.symbol,
        "approved": l.approved,
        "rank_score": float(l.rank_score or 0),
        "quality_score": float(l.quality_score or 0),
        "regime": l.regime,
        "structure_score": float(l.structure_score or 0),
        "duration_ms": l.duration_ms,
        "rejection_reasons": l.rejection_reasons,
        "created_at": l.created_at.isoformat(),
      }
      for l in logs
    ]
  }


async def _run_health(db: AsyncSession, run_id: str) -> str:
  result = await db.execute(
    select(ScannerRun).where(ScannerRun.run_id == uuid.UUID(run_id))
  )
  run = result.scalar_one_or_none()
  return run.health_status if run else "unknown"


def _format_summary(summary, health: str) -> dict:
  return {
    "run_id": summary.run_id,
    "total": summary.total,
    "approved": summary.approved,
    "health": health,
    "results": [
      {
        "symbol": r.symbol,
        "approved": r.approved,
        "rank_score": r.rank_score,
        "duration_ms": r.duration_ms,
        "error": r.error,
        "setup": r.response.setup.model_dump() if r.response and r.response.setup else None,
        "rejection_reasons": r.response.rejection_reasons if r.response else [],
        "ai_summary": (
          r.response.ai_reasoning.explanation
          if r.response and r.response.ai_reasoning
          else None
        ),
      }
      for r in summary.results
    ],
  }


@router.get("/buy-candidates")
async def get_buy_candidates() -> list[dict]:
  from backend.app.modules.scanner.opportunity_engine import OpportunityEngine
  engine = OpportunityEngine()
  return await engine.find_buy_candidates()


@router.get("/sell-candidates")
async def get_sell_candidates(db: AsyncSession = Depends(get_db)) -> list[dict]:
  from backend.app.modules.portfolio.kite_sync import KitePortfolioSync
  from backend.app.modules.scanner.opportunity_engine import OpportunityEngine
  
  sync = KitePortfolioSync()
  portfolio_data = await sync.fetch_portfolio(db)
  
  engine = OpportunityEngine()
  return await engine.find_sell_candidates(portfolio_data.get("holdings", []))
