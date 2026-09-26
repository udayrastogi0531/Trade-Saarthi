"""Execution validation — slippage, latency, partial fills, spread-aware simulation."""

import random
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models import ExecutionQualityLog

logger = get_logger(__name__)


@dataclass
class SimulatedFill:
  fill_price: float
  slippage_bps: float
  latency_ms: int
  partial_fill: bool
  rejected: bool
  rejection_reason: str | None
  spread_bps: float


@dataclass
class ExecutionAnalytics:
  avg_slippage_bps: float
  avg_latency_ms: float
  failed_order_rate: float
  partial_fill_rate: float
  fill_quality_score: float
  sample_size: int


class ExecutionSimulationEngine:
  """Realistic execution simulation and quality tracking."""

  def __init__(self) -> None:
    self._settings = get_settings()

  def simulate_order(
    self,
    symbol: str,
    direction: str,
    expected_price: float,
    quantity: int,
    spread_bps: float = 5.0,
    broker_down: bool = False,
  ) -> SimulatedFill:
    if broker_down:
      return SimulatedFill(
        expected_price, 0, 0, False, True, "Broker downtime simulated", spread_bps
      )

    latency_ms = random.randint(50, 400)
    slip_bps = random.gauss(self._settings.execution_max_slippage_pct * 10, 3)
    slip_bps = max(0, min(slip_bps, 50))
    slip_dir = 1 if direction == "BUY" else -1
    fill = expected_price * (1 + slip_dir * slip_bps / 10000)

    rejected = random.random() < 0.02
    partial = not rejected and random.random() < 0.08

    return SimulatedFill(
      fill_price=round(fill, 4),
      slippage_bps=round(slip_bps, 2),
      latency_ms=latency_ms,
      partial_fill=partial,
      rejected=rejected,
      rejection_reason="Order rejected by simulated broker" if rejected else None,
      spread_bps=spread_bps,
    )

  async def log_fill(
    self,
    db: AsyncSession,
    fill: SimulatedFill,
    symbol: str,
    expected_price: float,
    trade_id: UUID | None = None,
  ) -> ExecutionQualityLog:
    row = ExecutionQualityLog(
      trade_id=trade_id,
      symbol=symbol,
      expected_price=Decimal(str(expected_price)),
      fill_price=Decimal(str(fill.fill_price)),
      slippage_bps=Decimal(str(fill.slippage_bps)),
      latency_ms=fill.latency_ms,
      partial_fill=fill.partial_fill,
      rejected=fill.rejected,
      rejection_reason=fill.rejection_reason,
      spread_bps=Decimal(str(fill.spread_bps)),
      simulated=True,
    )
    db.add(row)
    await db.flush()
    return row

  async def get_analytics(self, db: AsyncSession, limit: int = 200) -> ExecutionAnalytics:
    result = await db.execute(
      select(ExecutionQualityLog).order_by(ExecutionQualityLog.created_at.desc()).limit(limit)
    )
    logs = list(result.scalars().all())
    if not logs:
      return ExecutionAnalytics(0, 0, 0, 0, 100, 0)

    slippages = [float(l.slippage_bps or 0) for l in logs if not l.rejected]
    latencies = [l.latency_ms or 0 for l in logs if not l.rejected]
    failed = sum(1 for l in logs if l.rejected)
    partial = sum(1 for l in logs if l.partial_fill)

    avg_slip = sum(slippages) / len(slippages) if slippages else 0
    quality = max(0, 100 - avg_slip * 2 - failed / len(logs) * 50)

    return ExecutionAnalytics(
      avg_slippage_bps=round(avg_slip, 2),
      avg_latency_ms=round(sum(latencies) / len(latencies), 0) if latencies else 0,
      failed_order_rate=round(failed / len(logs) * 100, 2),
      partial_fill_rate=round(partial / len(logs) * 100, 2),
      fill_quality_score=round(quality, 2),
      sample_size=len(logs),
    )
