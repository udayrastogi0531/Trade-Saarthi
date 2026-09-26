"""Trade Memory & Learning — adaptive confidence and setup ranking."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models import SetupPerformance, SignalOutcome

logger = get_logger(__name__)


class LearningEngine:
  """Historical performance tracking and confidence calibration."""

  def __init__(self) -> None:
    self._settings = get_settings()

  async def record_signal_outcome(
    self,
    db: AsyncSession,
    signal_id,
    setup_type: str,
    regime: str,
    ai_confidence: float,
    structure_confidence: float,
    approved: bool,
    outcome: str | None = None,
    pnl: float | None = None,
    false_breakout: bool = False,
  ) -> None:
    record = SignalOutcome(
      signal_id=signal_id,
      setup_type=setup_type,
      market_regime=regime,
      ai_confidence=Decimal(str(ai_confidence)),
      structure_confidence=Decimal(str(structure_confidence)),
      approved=approved,
      outcome=outcome,
      pnl=Decimal(str(pnl)) if pnl is not None else None,
      false_breakout=false_breakout,
    )
    db.add(record)
    await self._update_setup_performance(db, setup_type, regime, approved, pnl, false_breakout, ai_confidence)

  async def _update_setup_performance(
    self,
    db: AsyncSession,
    setup_type: str,
    regime: str,
    approved: bool,
    pnl: float | None,
    false_breakout: bool,
    ai_confidence: float,
  ) -> None:
    result = await db.execute(
      select(SetupPerformance).where(
        SetupPerformance.setup_type == setup_type,
        SetupPerformance.market_regime == regime,
      )
    )
    perf = result.scalar_one_or_none()
    if not perf:
      perf = SetupPerformance(
        setup_type=setup_type,
        market_regime=regime,
        trade_count=0,
        win_count=0,
      )
      db.add(perf)

    perf.trade_count += 1
    if pnl is not None and pnl > 0:
      perf.win_count += 1
    if false_breakout:
      fb = float(perf.false_breakout_rate or 0)
      perf.false_breakout_rate = Decimal(str(round((fb * (perf.trade_count - 1) + 1) / perf.trade_count, 4)))
    if perf.trade_count > 0:
      perf.avg_confidence = Decimal(str(round(
        (float(perf.avg_confidence or 0) * (perf.trade_count - 1) + ai_confidence) / perf.trade_count, 2
      )))
      perf.expectancy = Decimal(str(round(
        (perf.win_count / perf.trade_count) * 2 - 1, 4
      )))

  async def calibrate_confidence(
    self,
    db: AsyncSession,
    setup_type: str,
    regime: str,
    raw_confidence: float,
  ) -> tuple[float, str | None]:
    """Adjust confidence based on historical setup performance."""
    if not self._settings.adaptive_confidence_enabled:
      return raw_confidence, None

    result = await db.execute(
      select(SetupPerformance).where(
        SetupPerformance.setup_type == setup_type,
        SetupPerformance.market_regime == regime,
      )
    )
    perf = result.scalar_one_or_none()
    if not perf or perf.trade_count < 5:
      return raw_confidence, None

    win_rate = perf.win_count / perf.trade_count if perf.trade_count else 0.5
    fb_rate = float(perf.false_breakout_rate or 0)

    adjustment = 0.0
    note = None
    if win_rate < 0.4:
      adjustment -= 12
      note = f"Setup '{setup_type}' underperforms in {regime} regime (win rate {win_rate:.0%})."
    elif win_rate > 0.6:
      adjustment += 5

    if fb_rate > 0.35:
      adjustment -= 10
      note = (note or "") + f" High false breakout rate ({fb_rate:.0%}) historically."

    calibrated = max(0, min(95, raw_confidence + adjustment))
    return round(calibrated, 1), note

  async def rank_setups(self, db: AsyncSession, regime: str | None = None) -> list[dict]:
    query = select(SetupPerformance)
    if regime:
      query = query.where(SetupPerformance.market_regime == regime)
    result = await db.execute(query)
    rows = result.scalars().all()

    ranked = []
    for p in rows:
      if p.trade_count < 3:
        continue
      win_rate = p.win_count / p.trade_count * 100
      score = win_rate - float(p.false_breakout_rate or 0) * 30
      ranked.append({
        "setup_type": p.setup_type,
        "regime": p.market_regime,
        "score": round(score, 2),
        "win_rate": round(win_rate, 1),
        "trades": p.trade_count,
        "false_breakout_rate": float(p.false_breakout_rate or 0),
        "expectancy": float(p.expectancy or 0),
      })
    return sorted(ranked, key=lambda x: x["score"], reverse=True)

  async def get_learning_insight(
    self, db: AsyncSession, setup_type: str, regime: str
  ) -> str | None:
    _, note = await self.calibrate_confidence(db, setup_type, regime, 70)
    return note
