"""Deep regime research — extended classification and profitability tracking."""

from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import get_logger
from backend.app.db.models import RegimePerformance
from backend.app.modules.market_regime.engine import MarketRegime, RegimeEngine, RegimeType
from backend.app.modules.technical_analysis.engine import TechnicalSnapshot

logger = get_logger(__name__)


class ExtendedRegime(str, Enum):
  BULLISH_TREND = "bullish_trend"
  BEARISH_TREND = "bearish_trend"
  SIDEWAYS = "sideways"
  CHOPPY = "choppy"
  LOW_VOLATILITY = "low_volatility"
  HIGH_VOLATILITY = "high_volatility"
  NEWS_DRIVEN = "news_driven"
  PANIC = "panic"


@dataclass
class RegimeResearchResult:
  base_regime: MarketRegime
  extended_regime: ExtendedRegime
  confidence_multiplier: float
  position_size_multiplier: float
  allowed_setups: list[str]
  research_notes: list[str]


class RegimeResearchEngine(RegimeEngine):
  """Extended regime detection with profitability-aware adjustments."""

  EXTENDED_SETUP_MAP: dict[ExtendedRegime, list[str]] = {
    ExtendedRegime.BULLISH_TREND: ["breakout", "momentum", "pullback"],
    ExtendedRegime.BEARISH_TREND: ["reversal", "momentum"],
    ExtendedRegime.SIDEWAYS: ["reversal", "pullback"],
    ExtendedRegime.CHOPPY: [],
    ExtendedRegime.LOW_VOLATILITY: [],
    ExtendedRegime.HIGH_VOLATILITY: ["momentum"],
    ExtendedRegime.NEWS_DRIVEN: [],
    ExtendedRegime.PANIC: [],
  }

  SIZE_MAP: dict[ExtendedRegime, float] = {
    ExtendedRegime.BULLISH_TREND: 1.0,
    ExtendedRegime.BEARISH_TREND: 0.6,
    ExtendedRegime.SIDEWAYS: 0.7,
    ExtendedRegime.CHOPPY: 0.0,
    ExtendedRegime.LOW_VOLATILITY: 0.0,
    ExtendedRegime.HIGH_VOLATILITY: 0.4,
    ExtendedRegime.NEWS_DRIVEN: 0.2,
    ExtendedRegime.PANIC: 0.0,
  }

  def research(
    self,
    df: pd.DataFrame,
    symbol: str,
    snap: TechnicalSnapshot | None = None,
  ) -> RegimeResearchResult:
    base = self.detect(df, symbol, snap)
    extended = self._to_extended(base, df, snap)
    notes = []

    if extended == ExtendedRegime.CHOPPY:
      notes.append("Reduce breakout signals in choppy conditions")
    if extended == ExtendedRegime.HIGH_VOLATILITY:
      notes.append("Reduce position sizing during extreme volatility")
    if extended == ExtendedRegime.PANIC:
      notes.append("Panic regime — capital preservation mode; avoid new risk")

    return RegimeResearchResult(
      base_regime=base,
      extended_regime=extended,
      confidence_multiplier=0.85 if extended in (ExtendedRegime.CHOPPY, ExtendedRegime.HIGH_VOLATILITY) else 1.0,
      position_size_multiplier=self.SIZE_MAP.get(extended, 0.5),
      allowed_setups=self.EXTENDED_SETUP_MAP.get(extended, []),
      research_notes=notes,
    )

  def _to_extended(self, base: MarketRegime, df: pd.DataFrame, snap: TechnicalSnapshot | None) -> ExtendedRegime:
    close = df["close"]
    returns = close.pct_change().dropna()
    atr_pct = snap.atr_pct if snap else 2.0
    trend = snap.trend_direction if snap else "neutral"

    if atr_pct > 6 and len(returns) > 5 and float(returns.tail(5).std() * 100) > 4:
      return ExtendedRegime.PANIC
    if base.regime == RegimeType.VOLATILE or atr_pct > 4:
      return ExtendedRegime.HIGH_VOLATILITY
    if base.regime == RegimeType.LOW_VOLATILITY:
      return ExtendedRegime.LOW_VOLATILITY
    if base.regime == RegimeType.CHOPPY:
      return ExtendedRegime.CHOPPY
    if base.regime == RegimeType.NEWS_DRIVEN:
      return ExtendedRegime.NEWS_DRIVEN
    if base.regime == RegimeType.RANGING:
      return ExtendedRegime.SIDEWAYS
    if trend == "bullish":
      return ExtendedRegime.BULLISH_TREND
    if trend == "bearish":
      return ExtendedRegime.BEARISH_TREND
    return ExtendedRegime.SIDEWAYS

  async def update_regime_performance(
    self,
    db: AsyncSession,
    setup_type: str,
    regime: str,
    pnl: float,
    strategy_name: str = "default",
  ) -> None:
    result = await db.execute(
      select(RegimePerformance).where(
        RegimePerformance.setup_type == setup_type,
        RegimePerformance.regime == regime,
        RegimePerformance.strategy_name == strategy_name,
      )
    )
    row = result.scalar_one_or_none()
    if not row:
      row = RegimePerformance(
        strategy_name=strategy_name,
        setup_type=setup_type,
        regime=regime,
        trade_count=0,
      )
      db.add(row)

    row.trade_count += 1
    wins = int(float(row.win_rate or 0) / 100 * (row.trade_count - 1))
    if pnl > 0:
      wins += 1
    row.win_rate = round(wins / row.trade_count * 100, 4)
    prev_exp = float(row.expectancy or 0)
    row.expectancy = round((prev_exp * (row.trade_count - 1) + (1 if pnl > 0 else -1)) / row.trade_count, 4)
    row.avg_pnl = round((float(row.avg_pnl or 0) * (row.trade_count - 1) + pnl) / row.trade_count, 4)

    if row.trade_count >= 10 and float(row.win_rate or 0) < 40:
      row.confidence_adjustment = -0.15
    elif row.trade_count >= 10 and float(row.win_rate or 0) > 55:
      row.confidence_adjustment = 0.05

  async def get_regime_heatmap(self, db: AsyncSession) -> list[dict]:
    result = await db.execute(select(RegimePerformance))
    return [
      {
        "setup_type": r.setup_type,
        "regime": r.regime,
        "win_rate": float(r.win_rate or 0),
        "expectancy": float(r.expectancy or 0),
        "trade_count": r.trade_count,
        "confidence_adjustment": float(r.confidence_adjustment or 0),
      }
      for r in result.scalars().all()
    ]
