"""Trade Journal & Analytics — institutional performance tracking."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import get_logger
from backend.app.db.models import Trade, TradeJournal

logger = get_logger(__name__)


class JournalAnalyticsEngine:
  async def record_trade_entry(
    self,
    db: AsyncSession,
    trade_id: UUID,
    setup_type: str,
    strategy_name: str,
    ai_confidence: float,
    quality_score: float,
    market_regime: str,
    metadata: dict | None = None,
  ) -> TradeJournal:
    entry = TradeJournal(
      trade_id=trade_id,
      setup_type=setup_type,
      strategy_name=strategy_name,
      ai_confidence=Decimal(str(ai_confidence)),
      quality_score=Decimal(str(quality_score)),
      market_regime=market_regime,
      metadata=metadata or {},
    )
    db.add(entry)
    await db.flush()
    return entry

  async def close_trade_journal(
    self,
    db: AsyncSession,
    trade_id: UUID,
    exit_price: float,
    emotional_override: bool = False,
  ) -> TradeJournal | None:
    result = await db.execute(
      select(TradeJournal).where(TradeJournal.trade_id == trade_id)
    )
    journal = result.scalar_one_or_none()
    trade_result = await db.execute(select(Trade).where(Trade.id == trade_id))
    trade = trade_result.scalar_one_or_none()
    if not journal or not trade or not trade.entry_price:
      return None

    entry = float(trade.entry_price)
    qty = trade.quantity
    if trade.direction == "BUY":
      mfe = max(0, (exit_price - entry) * qty)
      mae = max(0, (entry - exit_price) * qty)
      pnl = (exit_price - entry) * qty
    else:
      mfe = max(0, (entry - exit_price) * qty)
      mae = max(0, (exit_price - entry) * qty)
      pnl = (entry - exit_price) * qty

    journal.mfe = Decimal(str(round(mfe, 2)))
    journal.mae = Decimal(str(round(mae, 2)))
    journal.outcome = "win" if pnl > 0 else ("loss" if pnl < 0 else "breakeven")
    journal.emotional_override = emotional_override
    return journal

  async def get_advanced_analytics(self, db: AsyncSession, account_id: int = 1) -> dict:
    base = await self.get_analytics(db, account_id)
    result = await db.execute(
      select(TradeJournal, Trade)
      .join(Trade, TradeJournal.trade_id == Trade.id)
      .where(Trade.account_id == account_id)
    )
    rows = result.all()
    durations = [j.duration_minutes for j, _ in rows if j.duration_minutes]
    overrides = sum(1 for j, _ in rows if j.emotional_override)
    base["advanced"] = {
      "avg_duration_minutes": round(sum(durations) / len(durations), 1) if durations else 0,
      "emotional_overrides": overrides,
      "execution_quality_breakdown": {},
      "heatmap_by_setup": base.get("by_setup", {}),
    }
    return base

  async def get_analytics(self, db: AsyncSession, account_id: int = 1) -> dict:
    result = await db.execute(
      select(TradeJournal, Trade)
      .join(Trade, TradeJournal.trade_id == Trade.id)
      .where(Trade.account_id == account_id)
    )
    rows = result.all()

    if not rows:
      return self._empty_analytics()

    by_setup: dict[str, list] = {}
    by_regime: dict[str, list] = {}
    outcomes = []

    for journal, trade in rows:
      setup = journal.setup_type or "unknown"
      regime = journal.market_regime or "unknown"
      won = journal.outcome == "win"
      outcomes.append(won)
      by_setup.setdefault(setup, []).append(won)
      by_regime.setdefault(regime, []).append(won)

    def win_rate(wins: list[bool]) -> float:
      return round(sum(wins) / len(wins) * 100, 2) if wins else 0

    return {
      "total_journal_entries": len(rows),
      "overall_win_rate": win_rate(outcomes),
      "by_setup": {
        k: {"win_rate": win_rate(v), "trades": len(v)} for k, v in by_setup.items()
      },
      "by_regime": {
        k: {"win_rate": win_rate(v), "trades": len(v)} for k, v in by_regime.items()
      },
      "best_setups": sorted(
        by_setup.items(), key=lambda x: win_rate(x[1]), reverse=True
      )[:3],
      "worst_regimes": sorted(
        by_regime.items(), key=lambda x: win_rate(x[1])
      )[:3],
    }

  @staticmethod
  def _empty_analytics() -> dict:
    return {
      "total_journal_entries": 0,
      "overall_win_rate": 0,
      "by_setup": {},
      "by_regime": {},
      "best_setups": [],
      "worst_regimes": [],
    }
