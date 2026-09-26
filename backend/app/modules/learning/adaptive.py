"""Long-term edge tracking and confidence recalibration."""

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import EdgeTracking, SignalOutcome
from backend.app.modules.learning.engine import LearningEngine


class AdaptiveLearningEngine(LearningEngine):
  """Extended learning with edge deterioration tracking."""

  async def update_edge_tracking(
    self,
    db: AsyncSession,
    setup_type: str,
    regime: str | None = None,
    window_days: int = 30,
  ) -> EdgeTracking:
    since = datetime.utcnow() - timedelta(days=window_days)
    result = await db.execute(
      select(SignalOutcome).where(
        SignalOutcome.setup_type == setup_type,
        SignalOutcome.recorded_at >= since,
      )
    )
    outcomes = list(result.scalars().all())

    existing = await db.execute(
      select(EdgeTracking).where(
        EdgeTracking.setup_type == setup_type,
        EdgeTracking.regime == regime,
      )
    )
    row = existing.scalar_one_or_none()
    if not row:
      row = EdgeTracking(setup_type=setup_type, regime=regime, window_days=window_days)
      db.add(row)

    if not outcomes:
      row.edge_status = "insufficient_data"
      row.sample_size = 0
      return row

    wins = sum(1 for o in outcomes if o.outcome == "win" or (o.pnl and float(o.pnl) > 0))
    wr = wins / len(outcomes) * 100
    pnls = [float(o.pnl) for o in outcomes if o.pnl is not None]
    exp = sum(1 if p > 0 else -1 for p in pnls) / len(pnls) if pnls else 0

    row.sample_size = len(outcomes)
    row.rolling_win_rate = Decimal(str(round(wr, 4)))
    row.rolling_expectancy = Decimal(str(round(exp, 4)))

    if wr < 40 and len(outcomes) >= 10:
      row.edge_status = "degraded"
    elif wr > 55 and len(outcomes) >= 10:
      row.edge_status = "healthy"
    else:
      row.edge_status = "neutral"

    row.updated_at = datetime.utcnow()
    await db.flush()
    return row

  async def recalibrate_with_edge(
    self,
    db: AsyncSession,
    setup_type: str,
    regime: str,
    raw_confidence: float,
  ) -> tuple[float, str | None]:
    calibrated, note = await self.calibrate_confidence(db, setup_type, regime, raw_confidence)
    await self.update_edge_tracking(db, setup_type, regime)
    result = await db.execute(
      select(EdgeTracking).where(
        EdgeTracking.setup_type == setup_type,
        EdgeTracking.regime == regime,
      )
    )
    edge = result.scalar_one_or_none()
    if edge and edge.edge_status == "degraded":
      calibrated *= 0.85
      note = (note or "") + " Edge degraded — confidence reduced."
    return round(calibrated, 2), note
