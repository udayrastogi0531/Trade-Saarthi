"""Institutional market structure analysis — BOS, CHOCH, liquidity, FVG, order blocks."""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from backend.app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class StructureAnalysis:
  symbol: str
  timeframe: str
  trend_direction: str
  trend_quality: float
  structure_confidence: float
  bos_detected: bool
  choch_detected: bool
  liquidity_sweep: bool
  fake_breakout_risk: float
  consolidation: bool
  support_zones: list[float] = field(default_factory=list)
  resistance_zones: list[float] = field(default_factory=list)
  order_blocks: list[dict] = field(default_factory=list)
  fair_value_gaps: list[dict] = field(default_factory=list)
  explanation: str = ""
  continuation_probability: float = 0.5

  def to_dict(self) -> dict:
    return {
      "symbol": self.symbol,
      "timeframe": self.timeframe,
      "trend_direction": self.trend_direction,
      "trend_quality": self.trend_quality,
      "structure_confidence": self.structure_confidence,
      "bos_detected": self.bos_detected,
      "choch_detected": self.choch_detected,
      "liquidity_sweep": self.liquidity_sweep,
      "fake_breakout_risk": self.fake_breakout_risk,
      "consolidation": self.consolidation,
      "support_zones": self.support_zones,
      "resistance_zones": self.resistance_zones,
      "order_blocks": self.order_blocks,
      "fair_value_gaps": self.fair_value_gaps,
      "explanation": self.explanation,
      "continuation_probability": self.continuation_probability,
    }


class MarketStructureEngine:
  """Detect SMC/ICT-style structure for trade quality filtering."""

  def analyze(self, df: pd.DataFrame, symbol: str, timeframe: str = "15m") -> StructureAnalysis:
    if len(df) < 60:
      raise ValueError("Need 60+ bars for structure analysis")

    high, low, close, open_ = df["high"], df["low"], df["close"], df["open"]
    n = len(df)

    swing_highs = self._swing_points(high, 5, "high")
    swing_lows = self._swing_points(low, 5, "low")

    trend_dir, trend_quality = self._trend_structure(close, swing_highs, swing_lows)
    bos = self._detect_bos(close, swing_highs, swing_lows, trend_dir)
    choch = self._detect_choch(close, swing_highs, swing_lows, trend_dir)
    liquidity_sweep = self._liquidity_sweep(high, low, close, swing_highs, swing_lows)
    supports, resistances = self._sr_zones(df)
    fvgs = self._fair_value_gaps(df)
    order_blocks = self._order_blocks(df, trend_dir)
    consolidation = self._is_consolidation(close)
    fake_risk = self._fake_breakout_risk(close, high, low, bos, liquidity_sweep)

    confidence = self._structure_confidence(
      trend_quality, bos, choch, liquidity_sweep, fake_risk, consolidation
    )
    continuation = max(0.1, min(0.9, trend_quality * 0.5 + (0.2 if bos else 0) - fake_risk * 0.3))

    explanation = self._build_explanation(
      trend_dir, bos, choch, liquidity_sweep, fake_risk, consolidation, confidence
    )

    return StructureAnalysis(
      symbol=symbol,
      timeframe=timeframe,
      trend_direction=trend_dir,
      trend_quality=round(trend_quality, 3),
      structure_confidence=round(confidence, 2),
      bos_detected=bos,
      choch_detected=choch,
      liquidity_sweep=liquidity_sweep,
      fake_breakout_risk=round(fake_risk, 3),
      consolidation=consolidation,
      support_zones=supports[:3],
      resistance_zones=resistances[:3],
      order_blocks=order_blocks[:2],
      fair_value_gaps=fvgs[:2],
      explanation=explanation,
      continuation_probability=round(continuation, 3),
    )

  def is_breakout_valid(self, analysis: StructureAnalysis, direction: str) -> tuple[bool, str]:
    if analysis.fake_breakout_risk > 0.65:
      return False, "High fake breakout probability from structure"
    if analysis.consolidation and not analysis.bos_detected:
      return False, "Consolidation without BOS confirmation"
    if direction == "BUY" and analysis.trend_direction == "bearish" and analysis.choch_detected:
      return False, "CHOCH against bullish trade"
    if direction == "SELL" and analysis.trend_direction == "bullish" and analysis.choch_detected:
      return False, "CHOCH against bearish trade"
    if analysis.structure_confidence < 50:
      return False, "Structure confidence too low"
    return True, "Structure supports setup"

  @staticmethod
  def _swing_points(series: pd.Series, window: int, kind: str) -> list[tuple[int, float]]:
    points = []
    for i in range(window, len(series) - window):
      seg = series.iloc[i - window : i + window + 1]
      if kind == "high" and series.iloc[i] == seg.max():
        points.append((i, float(series.iloc[i])))
      elif kind == "low" and series.iloc[i] == seg.min():
        points.append((i, float(series.iloc[i])))
    return points[-6:]

  @staticmethod
  def _trend_structure(
    close: pd.Series, swing_highs: list, swing_lows: list
  ) -> tuple[str, float]:
    if len(swing_highs) < 2 or len(swing_lows) < 2:
      return "neutral", 0.3
    hh = swing_highs[-1][1] > swing_highs[-2][1]
    hl = swing_lows[-1][1] > swing_lows[-2][1]
    lh = swing_highs[-1][1] < swing_highs[-2][1]
    ll = swing_lows[-1][1] < swing_lows[-2][1]
    if hh and hl:
      return "bullish", 0.75
    if lh and ll:
      return "bearish", 0.75
    return "neutral", 0.35

  @staticmethod
  def _detect_bos(
    close: pd.Series, swing_highs: list, swing_lows: list, trend: str
  ) -> bool:
    price = float(close.iloc[-1])
    if trend == "bullish" and swing_highs:
      return price > swing_highs[-1][1] * 1.001
    if trend == "bearish" and swing_lows:
      return price < swing_lows[-1][1] * 0.999
    return False

  @staticmethod
  def _detect_choch(
    close: pd.Series, swing_highs: list, swing_lows: list, trend: str
  ) -> bool:
    price = float(close.iloc[-1])
    if trend == "bullish" and swing_lows and len(swing_lows) >= 2:
      return price < swing_lows[-2][1]
    if trend == "bearish" and swing_highs and len(swing_highs) >= 2:
      return price > swing_highs[-2][1]
    return False

  @staticmethod
  def _liquidity_sweep(
    high: pd.Series, low: pd.Series, close: pd.Series, swing_highs: list, swing_lows: list
  ) -> bool:
    if not swing_highs and not swing_lows:
      return False
    last = len(close) - 1
    if swing_highs:
      level = swing_highs[-1][1]
      if float(high.iloc[last]) > level and float(close.iloc[last]) < level:
        return True
    if swing_lows:
      level = swing_lows[-1][1]
      if float(low.iloc[last]) < level and float(close.iloc[last]) > level:
        return True
    return False

  @staticmethod
  def _sr_zones(df: pd.DataFrame, lookback: int = 50) -> tuple[list[float], list[float]]:
    seg = df.iloc[-lookback:]
    lows = seg["low"].nsmallest(3).tolist()
    highs = seg["high"].nlargest(3).tolist()
    return sorted(set(round(x, 2) for x in lows)), sorted(set(round(x, 2) for x in highs), reverse=True)

  @staticmethod
  def _fair_value_gaps(df: pd.DataFrame) -> list[dict]:
    gaps = []
    for i in range(2, len(df)):
      prev_high = df["high"].iloc[i - 2]
      prev_low = df["low"].iloc[i - 2]
      curr_low = df["low"].iloc[i]
      curr_high = df["high"].iloc[i]
      if curr_low > prev_high:
        gaps.append({"type": "bullish_fvg", "top": float(curr_low), "bottom": float(prev_high)})
      elif curr_high < prev_low:
        gaps.append({"type": "bearish_fvg", "top": float(prev_low), "bottom": float(curr_high)})
    return gaps[-3:]

  @staticmethod
  def _order_blocks(df: pd.DataFrame, trend: str) -> list[dict]:
    blocks = []
    for i in range(len(df) - 10, len(df) - 1):
      body = abs(df["close"].iloc[i] - df["open"].iloc[i])
      range_ = df["high"].iloc[i] - df["low"].iloc[i]
      if range_ <= 0:
        continue
      if body / range_ > 0.6:
        if trend == "bullish" and df["close"].iloc[i] > df["open"].iloc[i]:
          blocks.append({"type": "bullish_ob", "low": float(df["low"].iloc[i]), "high": float(df["high"].iloc[i])})
        elif trend == "bearish" and df["close"].iloc[i] < df["open"].iloc[i]:
          blocks.append({"type": "bearish_ob", "low": float(df["low"].iloc[i]), "high": float(df["high"].iloc[i])})
    return blocks

  @staticmethod
  def _is_consolidation(close: pd.Series, lookback: int = 20) -> bool:
    seg = close.iloc[-lookback:]
    return float((seg.max() - seg.min()) / seg.mean() * 100) < 2.5

  @staticmethod
  def _fake_breakout_risk(
    close: pd.Series, high: pd.Series, low: pd.Series, bos: bool, sweep: bool
  ) -> float:
    risk = 0.3
    if sweep:
      risk += 0.25
    if bos and float(close.iloc[-1]) < float(high.iloc[-3:-1].max()):
      risk += 0.15
    vol = close.pct_change().tail(10).std()
    if vol and vol > 0.02:
      risk += 0.1
    return min(1.0, risk)

  @staticmethod
  def _structure_confidence(
    trend_q: float, bos: bool, choch: bool, sweep: bool, fake_risk: float, consol: bool
  ) -> float:
    score = trend_q * 50
    if bos:
      score += 15
    if choch:
      score -= 10
    if sweep and not fake_risk > 0.6:
      score += 10
    score -= fake_risk * 25
    if consol:
      score -= 8
    return max(0, min(100, score))

  @staticmethod
  def _build_explanation(
    trend: str, bos: bool, choch: bool, sweep: bool, fake_risk: float, consol: bool, conf: float
  ) -> str:
    parts = [f"Trend structure is {trend}."]
    if bos:
      parts.append("Break of structure (BOS) detected.")
    if choch:
      parts.append("Change of character (CHOCH) — potential reversal risk.")
    if sweep:
      parts.append("Liquidity sweep observed near swing levels.")
    if fake_risk > 0.55:
      parts.append(f"Elevated fake breakout risk ({fake_risk:.0%}).")
    if consol:
      parts.append("Price in consolidation — wait for expansion.")
    parts.append(f"Structure confidence: {conf:.0f}%.")
    return " ".join(parts)
