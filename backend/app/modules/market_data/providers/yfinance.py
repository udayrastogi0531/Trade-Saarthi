"""Yahoo Finance market data provider."""

import asyncio
from datetime import datetime
import pandas as pd
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.app.modules.market_data.providers.base import BaseMarketDataProvider
from backend.app.schemas.market import CandleRequest


class YFinanceMarketDataProvider(BaseMarketDataProvider):
  """Fetches real-time and historical OHLCV from Yahoo Finance."""

  _INDEX_MAP: dict[str, str] = {
    "NIFTY": "^NSEI",
    "NIFTY50": "^NSEI",
    "NIFTY 50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "NIFTYBANK": "^NSEBANK",
    "NIFTY BANK": "^NSEBANK",
    "SENSEX": "^BSESN",
  }

  def _map_symbol(self, symbol: str, exchange: str) -> str:
    sym = symbol.strip().upper()
    if sym in self._INDEX_MAP:
      return self._INDEX_MAP[sym]

    if "." in sym:
      return sym  # Already mapped (e.g. RELIANCE.NS)

    if exchange.upper() == "NSE":
      return f"{sym}.NS"
    elif exchange.upper() == "BSE":
      return f"{sym}.BO"
    return sym

  @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
  async def fetch_ohlcv(self, request: CandleRequest) -> pd.DataFrame:
    ticker = self._map_symbol(request.symbol, request.exchange)
    
    # Map request intervals to yfinance intervals
    # 4h is not natively supported by yfinance, we will fetch 1h and resample
    yf_interval = request.interval
    if yf_interval == "4h":
      yf_interval = "1h"

    # Define standard periods to fetch enough candles for the limit
    if request.interval == "1m":
      period = "7d"
    elif request.interval in ("5m", "15m"):
      period = "60d"
    else:
      period = "2y"

    loop = asyncio.get_running_loop()
    
    def _fetch():
      t = yf.Ticker(ticker)
      return t.history(period=period, interval=yf_interval)

    df = await loop.run_in_executor(None, _fetch)

    if df.empty:
      return pd.DataFrame()

    # Reset index to get the timestamp (usually index is 'Date' or 'Datetime')
    df = df.reset_index()
    
    # Find timestamp column
    ts_col = None
    for col in df.columns:
      if col.lower() in ("date", "datetime", "timestamp"):
        ts_col = col
        break

    if ts_col is None:
      return pd.DataFrame()

    df = df.rename(columns={
      ts_col: "timestamp",
      "Open": "open",
      "High": "high",
      "Low": "low",
      "Close": "close",
      "Volume": "volume",
    })

    # Keep only required columns
    df = df[["timestamp", "open", "high", "low", "close", "volume"]]

    # Resample 1h to 4h if requested
    if request.interval == "4h":
      df["timestamp"] = pd.to_datetime(df["timestamp"])
      df = df.set_index("timestamp")
      df = df.resample("4H").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
      }).dropna().reset_index()

    # Normalize types
    df = self._normalize(df)

    # Slice the last request.limit candles
    if len(df) > request.limit:
      df = df.iloc[-request.limit:]

    return df

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
