"""Abstract market data provider."""

from abc import ABC, abstractmethod

import pandas as pd

from backend.app.schemas.market import CandleRequest


class BaseMarketDataProvider(ABC):
  @abstractmethod
  async def fetch_ohlcv(self, request: CandleRequest) -> pd.DataFrame:
    """Return normalized OHLCV DataFrame with columns: timestamp, open, high, low, close, volume."""

  @abstractmethod
  async def subscribe_quotes(self, symbols: list[str]) -> None:
    """WebSocket subscription hook — override for live feeds."""
