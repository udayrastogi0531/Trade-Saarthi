"""Market Regime Detection — adapt strategies to market conditions."""

from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd

from backend.app.core.logging import get_logger
from backend.app.modules.technical_analysis.engine import TechnicalSnapshot

logger = get_logger(__name__)


class RegimeType(str, Enum):
  TRENDING = "trending"
  RANGING = "ranging"
  CHOPPY = "choppy"
  VOLATILE = "volatile"
  LOW_VOLATILITY = "low_volatility"
  NEWS_DRIVEN = "news_driven"


@dataclass
class MarketRegime:
  symbol: str
  regime: RegimeType
  confidence: float
  metrics: dict
  allowed_setups: list[str]
  position_size_multiplier: float


class RegimeEngine:
  """Detect market regime and adapt strategy eligibility."""

  SETUP_REGIME_MAP: dict[RegimeType, list[str]] = {
    RegimeType.TRENDING: ["breakout", "momentum", "pullback"],
    RegimeType.RANGING: ["reversal", "pullback"],
    RegimeType.CHOPPY: [],
    RegimeType.VOLATILE: ["momentum"],
    RegimeType.LOW_VOLATILITY: [],
    RegimeType.NEWS_DRIVEN: [],
  }

  SIZE_MULTIPLIERS: dict[RegimeType, float] = {
    RegimeType.TRENDING: 1.0,
    RegimeType.RANGING: 0.75,
    RegimeType.CHOPPY: 0.0,
    RegimeType.VOLATILE: 0.5,
    RegimeType.LOW_VOLATILITY: 0.0,
    RegimeType.NEWS_DRIVEN: 0.25,
  }

  def detect(
    self,
    df: pd.DataFrame,
    symbol: str,
    snap: TechnicalSnapshot | None = None,
  ) -> MarketRegime:
    close = df["close"]
    volume = df["volume"]
    returns = close.pct_change().dropna()

    atr_pct = snap.atr_pct if snap else self._atr_pct(df)
    vol_ratio = float(volume.iloc[-1] / volume.rolling(20).mean().iloc[-1]) if len(volume) > 20 else 1.0
    realized_vol = float(returns.tail(20).std() * np.sqrt(252) * 100) if len(returns) > 5 else 0.0

    range_pct = self._range_pct(close, 20)
    trend_score = snap.trend_strength if snap else 0.3
    is_sideways = snap.is_sideways if snap else range_pct < 3.0

    regime, confidence = self._classify(
      atr_pct, realized_vol, vol_ratio, range_pct, trend_score, is_sideways
    )

    logger.debug("regime_detected", symbol=symbol, regime=regime.value, confidence=confidence)

    return MarketRegime(
      symbol=symbol,
      regime=regime,
      confidence=confidence,
      metrics={
        "atr_pct": round(atr_pct, 3),
        "realized_vol": round(realized_vol, 3),
        "volume_ratio": round(vol_ratio, 3),
        "range_pct": round(range_pct, 3),
        "trend_strength": round(trend_score, 3),
      },
      allowed_setups=self.SETUP_REGIME_MAP.get(regime, []),
      position_size_multiplier=self.SIZE_MULTIPLIERS.get(regime, 0.5),
    )

  def is_setup_allowed(self, regime: MarketRegime, setup_type: str) -> bool:
    if not regime.allowed_setups:
      return False
    return setup_type in regime.allowed_setups

  @staticmethod
  def _classify(
    atr_pct: float,
    realized_vol: float,
    vol_ratio: float,
    range_pct: float,
    trend_score: float,
    is_sideways: bool,
  ) -> tuple[RegimeType, float]:
    if vol_ratio > 3.0 and atr_pct > 4.0:
      return RegimeType.NEWS_DRIVEN, min(95.0, 60 + vol_ratio * 5)

    if atr_pct < 0.5:
      return RegimeType.LOW_VOLATILITY, 80.0

    if is_sideways and range_pct < 2.5 and atr_pct < 2.0:
      return RegimeType.CHOPPY, 75.0

    if is_sideways or (range_pct < 4.0 and trend_score < 0.35):
      return RegimeType.RANGING, 70.0

    if atr_pct > 5.0 or realized_vol > 40:
      return RegimeType.VOLATILE, min(90.0, 50 + atr_pct * 4)

    if trend_score >= 0.4 and not is_sideways:
      return RegimeType.TRENDING, min(95.0, 55 + trend_score * 40)

    return RegimeType.RANGING, 60.0

  @staticmethod
  def _atr_pct(df: pd.DataFrame) -> float:
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat(
      [high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1
    ).max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1]
    return float((atr / close.iloc[-1]) * 100) if close.iloc[-1] else 0.0

  @staticmethod
  def _range_pct(close: pd.Series, lookback: int) -> float:
    seg = close.iloc[-lookback:]
    return float((seg.max() - seg.min()) / seg.mean() * 100) if seg.mean() else 0.0
