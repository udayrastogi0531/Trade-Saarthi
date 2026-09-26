"""Market Data Engine — live/historical OHLCV with caching and normalization."""

import asyncio
import json

import pandas as pd

from backend.app.config import get_settings
from backend.app.core.exceptions import MarketDataError
from backend.app.core.logging import get_logger
from backend.app.modules.market_data.providers.base import BaseMarketDataProvider
from backend.app.modules.market_data.providers.kite import KiteMarketDataProvider
from backend.app.modules.market_data.providers.mock import MockMarketDataProvider
from backend.app.modules.market_data.providers.yfinance import YFinanceMarketDataProvider
from backend.app.schemas.market import CandleRequest, MultiTimeframeRequest
from backend.app.services.redis_client import cache_get, cache_set

logger = get_logger(__name__)


class MarketDataEngine:
  def __init__(self, provider: BaseMarketDataProvider | None = None) -> None:
    settings = get_settings()
    if provider is not None:
      self._provider = provider
    elif settings.market_data_provider == "kite":
      self._provider = KiteMarketDataProvider()
    elif settings.market_data_provider == "yfinance":
      self._provider = YFinanceMarketDataProvider()
    else:
      self._provider = MockMarketDataProvider()
    self._settings = settings

  def _cache_key(self, request: CandleRequest) -> str:
    return f"ohlcv:{request.exchange}:{request.symbol}:{request.interval}:{request.limit}"

  async def get_candles(self, request: CandleRequest, use_cache: bool = True) -> pd.DataFrame:
    key = self._cache_key(request)
    if use_cache:
      cached = await cache_get(key)
      if cached:
        logger.debug("market_data_cache_hit", key=key)
        records = json.loads(cached)
        return pd.DataFrame(records)

    try:
      df = await self._provider.fetch_ohlcv(request)
    except Exception as exc:
      logger.error("market_data_fetch_error", symbol=request.symbol, error=str(exc))
      raise MarketDataError(str(exc)) from exc

    if df.empty or len(df) < 50:
      raise MarketDataError(f"Insufficient data for {request.symbol}")

    ttl = 60 if request.interval in ("1m", "5m") else 300
    if use_cache:
      await cache_set(key, df.to_json(orient="records", date_format="iso"), ttl_seconds=ttl)

    logger.info(
      "market_data_fetched",
      symbol=request.symbol,
      interval=request.interval,
      rows=len(df),
    )
    return df

  async def get_multi_timeframe(
    self, request: MultiTimeframeRequest
  ) -> dict[str, pd.DataFrame]:
    async def fetch_one(interval: str) -> tuple[str, pd.DataFrame]:
      candle_req = CandleRequest(
        symbol=request.symbol,
        exchange=request.exchange,
        interval=interval,
        limit=200,
      )
      df = await self.get_candles(candle_req)
      return interval, df

    pairs = await asyncio.gather(*[fetch_one(iv) for iv in request.intervals])
    return dict(pairs)
