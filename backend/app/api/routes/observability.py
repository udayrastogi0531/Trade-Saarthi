"""System health, observability & capital safety APIs."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app import __version__
from backend.app.config import get_settings
from backend.app.db.models import DataQualityEvent, ScannerRun
from backend.app.db.session import get_db
from backend.app.modules.execution.simulation import ExecutionSimulationEngine
from backend.app.modules.safety.capital import CapitalSafetyFramework
from backend.app.core.metrics import SCANNER_QUEUE_DEPTH
from backend.app.modules.scanner.queue import QUEUE_KEY
from backend.app.services.redis_client import get_redis

router = APIRouter(prefix="/observability", tags=["Observability"])


class DeploymentStageRequest(BaseModel):
  account_id: int = 1
  stage: str
  max_capital: float | None = None


class EmergencyShutdownRequest(BaseModel):
  account_id: int = 1
  reason: str


@router.get("/health")
async def system_health(db: AsyncSession = Depends(get_db)) -> dict:
  settings = get_settings()
  redis_ok = False
  queue_depth: int | None = None
  try:
    client = await get_redis()
    if client:
      await client.ping()
      redis_ok = True
      try:
        depth = int(await client.llen(QUEUE_KEY))
        SCANNER_QUEUE_DEPTH.set(float(depth))
        queue_depth = depth
      except Exception:
        SCANNER_QUEUE_DEPTH.set(0)
  except Exception:
    pass

  scanner = await db.execute(
    select(ScannerRun).order_by(ScannerRun.started_at.desc()).limit(1)
  )
  last_scan = scanner.scalar_one_or_none()

  dq = await db.execute(
    select(DataQualityEvent)
    .where(DataQualityEvent.feed_healthy.is_(False))
    .order_by(DataQualityEvent.created_at.desc())
    .limit(5)
  )
  dq_issues = list(dq.scalars().all())

  exec_analytics = await ExecutionSimulationEngine().get_analytics(db)

  alerts: list[str] = []
  if last_scan and last_scan.health_status in ("degraded", "unhealthy"):
    alerts.append(f"scanner:{last_scan.health_status}")
  if queue_depth is not None and queue_depth > 50:
    alerts.append("scanner_queue_backlog")
  if exec_analytics.failed_order_rate > 5:
    alerts.append("elevated_execution_failures")
  if dq_issues:
    alerts.append("data_quality_feed_issues")

  return {
    "status": "ok" if redis_ok and not dq_issues else "degraded",
    "version": __version__,
    "redis": redis_ok,
    "scanner_health": last_scan.health_status if last_scan else "unknown",
    "scanner_last_latency_ms": float(last_scan.avg_latency_ms or 0) if last_scan else None,
    "data_quality_issues": len(dq_issues),
    "data_quality_recent": [
      {
        "symbol": e.symbol,
        "event_type": e.event_type,
        "severity": e.severity,
        "feed_healthy": e.feed_healthy,
        "created_at": e.created_at.isoformat() if e.created_at else None,
      }
      for e in dq_issues
    ],
    "execution_quality_score": exec_analytics.fill_quality_score,
    "conservative_mode": settings.conservative_mode,
    "paper_trading": settings.paper_trading,
    "execution_enabled": settings.execution_enabled,
    "scanner_queue_depth": queue_depth,
    "operational_alerts": alerts,
    "governance": {
      "architecture_frozen": True,
      "mode": "operation_validation_research",
    },
    "disclaimer": "Monitoring only — not a guarantee of system profitability",
  }


@router.get("/data-quality")
async def data_quality_status(
  limit: int = Query(10, le=50),
  db: AsyncSession = Depends(get_db),
) -> dict:
  """Recent data-quality events for operational visibility."""
  result = await db.execute(
    select(DataQualityEvent).order_by(DataQualityEvent.created_at.desc()).limit(limit)
  )
  events = list(result.scalars().all())
  unhealthy = [e for e in events if not e.feed_healthy]
  return {
    "feed_healthy": len(unhealthy) == 0,
    "unhealthy_count": len(unhealthy),
    "events": [
      {
        "symbol": e.symbol,
        "provider": e.provider,
        "event_type": e.event_type,
        "severity": e.severity,
        "feed_healthy": e.feed_healthy,
        "details": e.details,
        "created_at": e.created_at.isoformat() if e.created_at else None,
      }
      for e in events
    ],
    "disclaimer": "Unhealthy feeds should reduce confidence and block unsafe signals when configured",
  }


@router.get("/execution-quality")
async def execution_quality(db: AsyncSession = Depends(get_db)) -> dict:
  analytics = await ExecutionSimulationEngine().get_analytics(db)
  return analytics.__dict__


@router.get("/capital-safety")
async def capital_safety(
  account_id: int = Query(1),
  db: AsyncSession = Depends(get_db),
) -> dict:
  state = await CapitalSafetyFramework().get_or_create_state(db, account_id)
  can_live, reasons = await CapitalSafetyFramework().can_execute_live(db, account_id)
  return {
    "deployment_stage": state.deployment_stage,
    "emergency_shutdown": state.emergency_shutdown,
    "human_approval_required": state.human_approval_required,
    "max_live_capital": float(state.max_live_capital or 0),
    "can_execute_live": can_live,
    "blockers": reasons,
  }


@router.post("/capital-safety/stage")
async def set_deployment_stage(
  request: DeploymentStageRequest,
  db: AsyncSession = Depends(get_db),
) -> dict:
  state = await CapitalSafetyFramework().set_deployment_stage(
    db, request.account_id, request.stage, request.max_capital
  )
  return {"deployment_stage": state.deployment_stage, "max_live_capital": float(state.max_live_capital or 0)}


@router.post("/capital-safety/emergency-shutdown")
async def emergency_shutdown(
  request: EmergencyShutdownRequest,
  db: AsyncSession = Depends(get_db),
) -> dict:
  state = await CapitalSafetyFramework().emergency_shutdown(
    db, request.account_id, request.reason
  )
  return {"emergency_shutdown": state.emergency_shutdown, "reason": state.shutdown_reason}
