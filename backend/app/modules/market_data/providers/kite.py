"""Zerodha Kite Connect market data provider (requires kiteconnect package)."""

import pandas as pd

from backend.app.config import get_settings
from backend.app.core.exceptions import MarketDataError
from backend.app.core.logging import get_logger
from backend.app.modules.market_data.providers.base import BaseMarketDataProvider
from backend.app.services.broker_tokens import BrokerTokenService
from backend.app.db.session import AsyncSessionLocal
from backend.app.schemas.market import CandleRequest

logger = get_logger(__name__)


class KiteMarketDataProvider(BaseMarketDataProvider):
  """
  Production integration point for Zerodha Kite Connect.
  Install: pip install kiteconnect
  Set KITE_API_KEY, KITE_ACCESS_TOKEN in environment.
  """

  def __init__(self) -> None:
    self._settings = get_settings()
    if not self._settings.kite_api_key:
      raise MarketDataError("Kite API key not configured")
    self._kite = None
    self._access_token: str | None = None

  async def _get_access_token(self) -> str:
    if self._access_token:
      return self._access_token
    if self._settings.kite_access_token:
      self._access_token = self._settings.kite_access_token
      return self._access_token

    async with AsyncSessionLocal() as db:
      token = await BrokerTokenService().get_latest(db, "kite")
      if token:
        self._access_token = token.access_token
        return self._access_token
    raise MarketDataError("Kite access token not available")

  async def _get_client(self):
    try:
      from kiteconnect import KiteConnect
    except ImportError as exc:
      raise MarketDataError("kiteconnect package not installed") from exc

    if self._kite is None:
      kite = KiteConnect(api_key=self._settings.kite_api_key)
      access_token = await self._get_access_token()
      kite.set_access_token(access_token)
      self._kite = kite
    return self._kite

  async def fetch_ohlcv(self, request: CandleRequest) -> pd.DataFrame:
    kite = await self._get_client()
    interval_map = {"1m": "minute", "5m": "5minute", "15m": "15minute", "1h": "60minute", "1d": "day"}
    instrument_token = await self._resolve_instrument_token(request.symbol, request.exchange)

    from datetime import datetime, timedelta

    to_date = datetime.now()
    from_date = to_date - timedelta(days=min(request.limit, 60))

    try:
      candles = kite.historical_data(
        instrument_token,
        from_date,
        to_date,
        interval_map[request.interval],
      )
    except Exception as exc:
      logger.error("kite_fetch_failed", symbol=request.symbol, error=str(exc))
      raise MarketDataError(f"Kite historical fetch failed: {exc}") from exc

    df = pd.DataFrame(candles)
    if df.empty:
      raise MarketDataError(f"No data returned for {request.symbol}")

    df = df.rename(columns={"date": "timestamp"})
    return df[["timestamp", "open", "high", "low", "close", "volume"]]

  async def _resolve_instrument_token(self, symbol: str, exchange: str) -> int:
    kite = await self._get_client()
    instruments = kite.instruments(exchange)
    for inst in instruments:
      if inst["tradingsymbol"] == symbol.upper():
        return inst["instrument_token"]
    raise MarketDataError(f"Instrument not found: {symbol} on {exchange}")

  async def subscribe_quotes(self, symbols: list[str]) -> None:
    logger.info("kite_websocket_subscribe", symbols=symbols)
