"""Data quality & reliability — refuse trading on bad feeds."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models import DataQualityEvent

logger = get_logger(__name__)


@dataclass
class DataQualityReport:
  symbol: str
  healthy: bool
  confidence_penalty: float
  issues: list[str]
  events: list[dict]

  def to_dict(self) -> dict:
    return {
      "symbol": self.symbol,
      "healthy": self.healthy,
      "confidence_penalty": self.confidence_penalty,
      "issues": self.issues,
    }


class DataQualityEngine:
  """Institutional data validation before signal generation."""

  def __init__(self) -> None:
    self._settings = get_settings()
    self._last_heartbeat: dict[str, datetime] = {}

  def validate_candles(
    self,
    df: pd.DataFrame,
    symbol: str,
    interval_minutes: int = 15,
  ) -> DataQualityReport:
    issues: list[str] = []
    penalty = 0.0

    if df is None or df.empty:
      return DataQualityReport(symbol, False, 1.0, ["Empty candle dataframe"], [])

    if len(df) < 50:
      issues.append(f"Insufficient bars ({len(df)}) — minimum 50 required")
      penalty += 0.3

    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing_cols = required - set(df.columns)
    if missing_cols:
      issues.append(f"Missing columns: {missing_cols}")
      penalty = 1.0

    if "timestamp" in df.columns:
      gaps = self._detect_gaps(df, interval_minutes)
      if gaps:
        issues.append(f"Detected {len(gaps)} candle gaps")
        penalty += min(0.5, len(gaps) * 0.05)

      last_ts = pd.to_datetime(df["timestamp"].iloc[-1])
      if hasattr(last_ts, "tzinfo") and last_ts.tzinfo:
        last_ts = last_ts.replace(tzinfo=None)
      age = (datetime.utcnow() - last_ts.to_pydatetime()).total_seconds()
      if age > self._settings.stale_data_threshold_seconds:
        issues.append(f"Stale data — last candle {int(age)}s old")
        penalty += 0.4

    integrity = self._integrity_check(df)
    issues.extend(integrity)
    penalty += len(integrity) * 0.1

    if self._settings.enforce_nse_market_hours and self._settings.nse_enabled:
      if not self._nse_regular_session():
        issues.append("Outside NSE regular session — live-style validation downgrade")
        penalty += 0.15

    healthy = len(issues) == 0 or (penalty < 0.5 and "Empty" not in str(issues))
    if self._settings.block_signals_on_bad_data and penalty >= 0.5:
      healthy = False

    self._last_heartbeat[symbol] = datetime.utcnow()
    return DataQualityReport(symbol, healthy, min(1.0, penalty), issues, [])

  @staticmethod
  def _nse_regular_session() -> bool:
    try:
      now = datetime.now(ZoneInfo("Asia/Kolkata"))
    except Exception:
      return True
    if now.weekday() >= 5:
      return False
    minutes = now.hour * 60 + now.minute
    return (9 * 60 + 15) <= minutes <= (15 * 60 + 30)

  async def record_event(
    self,
    db: AsyncSession,
    symbol: str,
    event_type: str,
    severity: str,
    details: dict,
    provider: str | None = None,
    feed_healthy: bool = True,
  ) -> None:
    if not self._settings.data_quality_enabled:
      return
    db.add(
      DataQualityEvent(
        symbol=symbol,
        provider=provider or self._settings.market_data_provider,
        event_type=event_type,
        severity=severity,
        details=details,
        feed_healthy=feed_healthy,
      )
    )
    await db.flush()

  def record_heartbeat(self, symbol: str) -> None:
    self._last_heartbeat[symbol] = datetime.utcnow()

  def websocket_healthy(self, symbol: str) -> bool:
    last = self._last_heartbeat.get(symbol)
    if not last:
      return True
    return (datetime.utcnow() - last).total_seconds() < self._settings.stale_data_threshold_seconds

  @staticmethod
  def _detect_gaps(df: pd.DataFrame, interval_minutes: int) -> list:
    ts = pd.to_datetime(df["timestamp"]).sort_values()
    if len(ts) < 2:
      return []
    expected = timedelta(minutes=interval_minutes * 1.5)
    gaps = []
    for i in range(1, len(ts)):
      delta = ts.iloc[i] - ts.iloc[i - 1]
      if delta > expected:
        gaps.append({"from": str(ts.iloc[i - 1]), "to": str(ts.iloc[i])})
    return gaps

  @staticmethod
  def _integrity_check(df: pd.DataFrame) -> list[str]:
    issues = []
    if (df["high"] < df["low"]).any():
      issues.append("OHLC integrity: high < low detected")
    if (df["close"] > df["high"]).any() or (df["close"] < df["low"]).any():
      issues.append("OHLC integrity: close outside high/low range")
    if (df["volume"] < 0).any():
      issues.append("Negative volume detected")
    return issues
