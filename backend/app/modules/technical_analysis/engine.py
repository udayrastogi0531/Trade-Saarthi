"""Technical Analysis Engine — indicators and multi-timeframe confirmation."""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import ta

from backend.app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TechnicalSnapshot:
  symbol: str
  timeframe: str
  rsi: float
  macd: float
  macd_signal: float
  macd_hist: float
  ema_9: float
  ema_21: float
  ema_50: float
  sma_20: float
  vwap: float
  atr: float
  bb_upper: float
  bb_lower: float
  bb_mid: float
  volume_spike: bool
  trend_strength: float
  trend_direction: str
  is_sideways: bool
  atr_pct: float
  indicators: dict = field(default_factory=dict)


class TechnicalAnalysisEngine:
  """Computes institutional-grade technical indicators on OHLCV data."""

  def analyze(self, df: pd.DataFrame, symbol: str, timeframe: str) -> TechnicalSnapshot:
    if len(df) < 50:
      raise ValueError("Need at least 50 bars for technical analysis")

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    rsi = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]
    macd_ind = ta.trend.MACD(close)
    macd = macd_ind.macd().iloc[-1]
    macd_signal = macd_ind.macd_signal().iloc[-1]
    macd_hist = macd_ind.macd_diff().iloc[-1]

    ema_9 = ta.trend.EMAIndicator(close, window=9).ema_indicator().iloc[-1]
    ema_21 = ta.trend.EMAIndicator(close, window=21).ema_indicator().iloc[-1]
    ema_50 = ta.trend.EMAIndicator(close, window=50).ema_indicator().iloc[-1]
    sma_20 = ta.trend.SMAIndicator(close, window=20).sma_indicator().iloc[-1]

    vwap = self._compute_vwap(df)
    atr = ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range().iloc[-1]
    bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
    bb_upper = bb.bollinger_hband().iloc[-1]
    bb_lower = bb.bollinger_lband().iloc[-1]
    bb_mid = bb.bollinger_mavg().iloc[-1]

    vol_ma = volume.rolling(20).mean().iloc[-1]
    volume_spike = bool(volume.iloc[-1] > vol_ma * 1.5) if vol_ma > 0 else False

    trend_strength, trend_direction = self._trend_strength(close, ema_9, ema_21, ema_50)
    is_sideways = self._detect_sideways(close, atr)
    atr_pct = (atr / close.iloc[-1]) * 100 if close.iloc[-1] else 0

    return TechnicalSnapshot(
      symbol=symbol,
      timeframe=timeframe,
      rsi=float(rsi),
      macd=float(macd),
      macd_signal=float(macd_signal),
      macd_hist=float(macd_hist),
      ema_9=float(ema_9),
      ema_21=float(ema_21),
      ema_50=float(ema_50),
      sma_20=float(sma_20),
      vwap=float(vwap),
      atr=float(atr),
      bb_upper=float(bb_upper),
      bb_lower=float(bb_lower),
      bb_mid=float(bb_mid),
      volume_spike=volume_spike,
      trend_strength=trend_strength,
      trend_direction=trend_direction,
      is_sideways=is_sideways,
      atr_pct=float(atr_pct),
      indicators={
        "close": float(close.iloc[-1]),
        "volume_ratio": float(volume.iloc[-1] / vol_ma) if vol_ma > 0 else 1.0,
      },
    )

  def multi_timeframe_confirm(
    self, snapshots: dict[str, TechnicalSnapshot], direction: str
  ) -> tuple[bool, list[str]]:
    """Confirm trend alignment across timeframes."""
    reasons: list[str] = []
    aligned = 0
    for tf, snap in snapshots.items():
      if snap.is_sideways:
        reasons.append(f"{tf}: sideways market")
        continue
      if snap.trend_direction == direction:
        aligned += 1
      else:
        reasons.append(f"{tf}: trend is {snap.trend_direction}, need {direction}")

    required = max(2, len(snapshots) - 1)
    confirmed = aligned >= required
    if confirmed:
      reasons.append(f"Multi-TF alignment: {aligned}/{len(snapshots)} timeframes")
    return confirmed, reasons

  @staticmethod
  def _compute_vwap(df: pd.DataFrame) -> float:
    typical = (df["high"] + df["low"] + df["close"]) / 3
    cum_vol = df["volume"].cumsum()
    cum_tp_vol = (typical * df["volume"]).cumsum()
    vwap_series = cum_tp_vol / cum_vol.replace(0, np.nan)
    return float(vwap_series.iloc[-1])

  @staticmethod
  def _trend_strength(close: pd.Series, ema9: float, ema21: float, ema50: float) -> tuple[float, str]:
    price = close.iloc[-1]
    if ema9 > ema21 > ema50 and price > ema9:
      strength = min(1.0, (price - ema50) / ema50 * 10) if ema50 else 0.5
      return max(0.3, strength), "bullish"
    if ema9 < ema21 < ema50 and price < ema9:
      strength = min(1.0, (ema50 - price) / ema50 * 10) if ema50 else 0.5
      return max(0.3, strength), "bearish"
    return 0.2, "neutral"

  @staticmethod
  def _detect_sideways(close: pd.Series, atr: float, lookback: int = 20) -> bool:
    segment = close.iloc[-lookback:]
    range_pct = (segment.max() - segment.min()) / segment.mean() * 100 if segment.mean() else 0
    atr_pct = (atr / close.iloc[-1]) * 100 if close.iloc[-1] else 0
    return range_pct < atr_pct * 1.5 and range_pct < 3.0
