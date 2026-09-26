"""Mock market data for development and paper trading."""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.app.modules.market_data.providers.base import BaseMarketDataProvider
from backend.app.schemas.market import CandleRequest


class MockMarketDataProvider(BaseMarketDataProvider):
  """Generates realistic synthetic OHLCV for NSE symbols."""

  _SEED_PRICES: dict[str, float] = {
    "RELIANCE": 2890.0,
    "TCS": 4150.0,
    "INFY": 1920.0,
    "HDFCBANK": 1680.0,
    "NIFTY": 24500.0,
  }

  @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
  async def fetch_ohlcv(self, request: CandleRequest) -> pd.DataFrame:
    base = self._SEED_PRICES.get(request.symbol.upper(), 1000.0)
    n = request.limit
    interval_minutes = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}[request.interval]
    end = datetime.utcnow().replace(second=0, microsecond=0)
    timestamps = [end - timedelta(minutes=interval_minutes * i) for i in range(n)][::-1]

    rng = np.random.default_rng(hash(request.symbol) % 2**32)
    returns = rng.normal(0, 0.002, n)
    closes = base * np.cumprod(1 + returns)
    opens = np.roll(closes, 1)
    opens[0] = base
    highs = np.maximum(opens, closes) * (1 + rng.uniform(0, 0.003, n))
    lows = np.minimum(opens, closes) * (1 - rng.uniform(0, 0.003, n))
    volumes = rng.integers(50_000, 500_000, n).astype(float)

    df = pd.DataFrame(
      {
        "timestamp": timestamps,
        "open": opens.round(2),
        "high": highs.round(2),
        "low": lows.round(2),
        "close": closes.round(2),
        "volume": volumes,
      }
    )
    return self._normalize(df)

  async def subscribe_quotes(self, symbols: list[str]) -> None:
    pass

  @staticmethod
  def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    for col in ("open", "high", "low", "close", "volume"):
      df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna()
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df
