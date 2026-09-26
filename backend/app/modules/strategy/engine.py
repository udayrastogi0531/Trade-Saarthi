"""Strategy Engine — setup detection and trade validation."""

from dataclasses import dataclass

import pandas as pd

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.modules.technical_analysis.engine import TechnicalAnalysisEngine, TechnicalSnapshot
from backend.app.schemas.trade import TradeSetup

logger = get_logger(__name__)


@dataclass
class StrategyResult:
  approved: bool
  setup: TradeSetup | None
  setup_type: str
  rejection_reasons: list[str]
  technical_summary: dict
  direction: str | None = None


class StrategyEngine:
  """
  Detects high-probability setups and rejects low-quality trades.
  Enforces: trend, volume, min RR, volatility filter, no sideways markets.
  """

  def __init__(self) -> None:
    self._ta = TechnicalAnalysisEngine()
    self._settings = get_settings()

  def evaluate(
    self,
    symbol: str,
    df: pd.DataFrame,
    timeframe: str,
    mtf_snapshots: dict[str, TechnicalSnapshot] | None = None,
  ) -> StrategyResult:
    snap = self._ta.analyze(df, symbol, timeframe)
    rejection: list[str] = []

    if snap.is_sideways:
      rejection.append("Sideways market — no clear trend")

    if snap.atr_pct < 0.3:
      rejection.append("Volatility too low for meaningful moves")
    elif snap.atr_pct > 8.0:
      rejection.append("Volatility too high — elevated risk")

    setup_type, direction, entry, sl, target = self._detect_setup(df, snap)

    if not setup_type:
      rejection.append("No valid setup detected")
      return StrategyResult(False, None, "none", rejection, self._summary(snap))

    risk = abs(entry - sl)
    reward = abs(target - entry)
    rr = reward / risk if risk > 0 else 0

    if rr < self._settings.min_risk_reward:
      rejection.append(f"Risk-reward {rr:.2f} below minimum {self._settings.min_risk_reward}")

    if not snap.volume_spike and setup_type in ("breakout", "momentum"):
      rejection.append("Volume confirmation missing for breakout/momentum")

    if direction == "BUY" and snap.trend_direction != "bullish":
      rejection.append("BUY rejected — trend not bullish")
    if direction == "SELL" and snap.trend_direction != "bearish":
      rejection.append("SELL rejected — trend not bearish")

    if setup_type == "breakout" and self._weak_breakout(df, direction):
      rejection.append("Weak breakout — price failed to hold above/below level")

    if mtf_snapshots:
      confirmed, mtf_reasons = self._ta.multi_timeframe_confirm(mtf_snapshots, direction.lower())
      if not confirmed:
        rejection.extend(mtf_reasons)

    confidence = self._compute_confidence(snap, setup_type, rr, len(rejection))

    if rejection:
      return StrategyResult(
        approved=False,
        setup=None,
        setup_type=setup_type,
        rejection_reasons=rejection,
        technical_summary=self._summary(snap),
        direction=direction,
      )

    setup = TradeSetup(
      symbol=symbol,
      direction=direction,
      entry=round(entry, 2),
      stop_loss=round(sl, 2),
      target=round(target, 2),
      risk_reward=round(rr, 2),
      position_size=0,
      position_value=0.0,
      risk_amount=0.0,
      confidence=confidence,
      setup_type=setup_type,
      timeframe=timeframe,
    )

    logger.info(
      "strategy_setup_detected",
      symbol=symbol,
      setup_type=setup_type,
      direction=direction,
      rr=rr,
      confidence=confidence,
    )

    return StrategyResult(
      approved=True,
      setup=setup,
      setup_type=setup_type,
      rejection_reasons=[],
      technical_summary=self._summary(snap),
      direction=direction,
    )

  def _detect_setup(
    self, df: pd.DataFrame, snap: TechnicalSnapshot
  ) -> tuple[str | None, str | None, float, float, float]:
    close = float(df["close"].iloc[-1])
    atr = snap.atr
    high_20 = float(df["high"].iloc[-21:-1].max())
    low_20 = float(df["low"].iloc[-21:-1].min())

    # Breakout
    if close > high_20 and snap.volume_spike and snap.rsi < 75:
      entry = close
      sl = close - 1.5 * atr
      target = close + 3.0 * atr
      return "breakout", "BUY", entry, sl, target

    if close < low_20 and snap.volume_spike and snap.rsi > 25:
      entry = close
      sl = close + 1.5 * atr
      target = close - 3.0 * atr
      return "breakout", "SELL", entry, sl, target

    # Pullback to EMA in trend
    if snap.trend_direction == "bullish" and close > snap.ema_21:
      if abs(close - snap.ema_21) < atr * 0.5 and snap.macd_hist > 0:
        entry = close
        sl = snap.ema_50
        target = close + 2.5 * atr
        return "pullback", "BUY", entry, sl, target

    if snap.trend_direction == "bearish" and close < snap.ema_21:
      if abs(close - snap.ema_21) < atr * 0.5 and snap.macd_hist < 0:
        entry = close
        sl = snap.ema_50
        target = close - 2.5 * atr
        return "pullback", "SELL", entry, sl, target

    # Momentum continuation
    if snap.trend_strength > 0.5 and snap.macd_hist > 0 and 50 < snap.rsi < 70:
      entry = close
      sl = close - atr
      target = close + 2 * atr
      return "momentum", "BUY", entry, sl, target

    if snap.trend_strength > 0.5 and snap.macd_hist < 0 and 30 < snap.rsi < 50:
      entry = close
      sl = close + atr
      target = close - 2 * atr
      return "momentum", "SELL", entry, sl, target

    # Reversal at BB extremes
    if close <= snap.bb_lower and snap.rsi < 35:
      entry = close
      sl = close - 1.2 * atr
      target = snap.bb_mid
      return "reversal", "BUY", entry, sl, target

    if close >= snap.bb_upper and snap.rsi > 65:
      entry = close
      sl = close + 1.2 * atr
      target = snap.bb_mid
      return "reversal", "SELL", entry, sl, target

    return None, None, 0.0, 0.0, 0.0

  @staticmethod
  def _weak_breakout(df: pd.DataFrame, direction: str) -> bool:
    if len(df) < 3:
      return True
    last = df.iloc[-1]
    prev = df.iloc[-2]
    if direction == "BUY":
      return last["close"] < prev["high"]
    return last["close"] > prev["low"]

  @staticmethod
  def _compute_confidence(
    snap: TechnicalSnapshot, setup_type: str, rr: float, rejection_count: int
  ) -> float:
    base = 50.0
    base += snap.trend_strength * 20
    if snap.volume_spike:
      base += 10
    base += min(15, (rr - 2) * 5)
    type_bonus = {"breakout": 8, "pullback": 12, "momentum": 6, "reversal": 4}
    base += type_bonus.get(setup_type, 0)
    if 40 < snap.rsi < 60:
      base += 5
    base -= rejection_count * 10
    return round(max(0, min(95, base)), 1)

  @staticmethod
  def _summary(snap: TechnicalSnapshot) -> dict:
    return {
      "rsi": snap.rsi,
      "trend": snap.trend_direction,
      "trend_strength": snap.trend_strength,
      "volume_spike": snap.volume_spike,
      "is_sideways": snap.is_sideways,
      "atr_pct": snap.atr_pct,
      "macd_hist": snap.macd_hist,
    }
