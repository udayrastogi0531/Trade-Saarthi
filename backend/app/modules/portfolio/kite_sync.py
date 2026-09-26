"""Kite Portfolio Sync Engine with real-time Yahoo Finance price updates and mock fallbacks."""

import pandas as pd
from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.modules.market_data.engine import MarketDataEngine
from backend.app.schemas.market import CandleRequest

from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class KitePortfolioSync:
  """Synchronizes holdings and positions from Zerodha Kite with active price fallbacks."""

  def __init__(self) -> None:
    self._settings = get_settings()
    self._market = MarketDataEngine()

  async def fetch_portfolio(self, db: AsyncSession = None) -> dict:
    holdings = []
    positions = []
    
    access_token = self._settings.kite_access_token
    if db is not None:
      try:
        from backend.app.services.broker_tokens import BrokerTokenService
        token_service = BrokerTokenService()
        db_token = await token_service.get_latest(db, "kite")
        if db_token and db_token.access_token:
          access_token = db_token.access_token
          logger.info("kite_sync_using_db_access_token")
      except Exception as token_err:
        logger.error("kite_sync_token_retrieval_failed", error=str(token_err))

    # Try fetching live Kite holdings if connected
    if self._settings.broker_mode == "kite" and access_token:
      try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=self._settings.kite_api_key)
        kite.set_access_token(access_token)
        
        raw_holdings = kite.holdings()
        for h in raw_holdings:
          sym = h.get("tradingsymbol", "")
          qty = h.get("quantity", 0)
          avg_price = h.get("average_price", 0.0)
          
          # Fetch real-time price from yfinance fallback
          current_price = await self._get_live_price(sym)
          if current_price == 0.0:
            current_price = h.get("last_price", avg_price)

          invested = avg_price * qty
          current_val = current_price * qty
          pnl = current_val - invested
          pnl_pct = (pnl / invested * 100) if invested > 0 else 0.0

          holdings.append({
            "symbol": sym,
            "quantity": qty,
            "avg_buy_price": round(avg_price, 2),
            "current_price": round(current_price, 2),
            "invested_value": round(invested, 2),
            "current_value": round(current_val, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2)
          })
        
        raw_positions = kite.positions().get("net", [])
        for p in raw_positions:
          positions.append({
            "symbol": p.get("tradingsymbol", ""),
            "quantity": p.get("quantity", 0),
            "avg_buy_price": p.get("average_price", 0.0),
            "last_price": p.get("last_price", 0.0),
            "pnl": p.get("pnl", 0.0),
          })
          
      except Exception as e:
        logger.error("kite_live_sync_failed_using_fallback", error=str(e))
        holdings = await self._get_mock_holdings()
    else:
      # Use mock holdings directly for development mode
      holdings = await self._get_mock_holdings()

    # Calculate portfolio aggregates
    total_invested = sum(h["invested_value"] for h in holdings)
    total_current = sum(h["current_value"] for h in holdings)
    total_pnl = total_current - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0

    return {
      "holdings": holdings,
      "positions": positions,
      "summary": {
        "total_invested_value": round(total_invested, 2),
        "total_current_value": round(total_current, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl_pct, 2)
      }
    }

  async def _get_live_price(self, symbol: str) -> float:
    try:
      df = await self._market.get_candles(
        CandleRequest(symbol=symbol, exchange="NSE", interval="1d", limit=2)
      )
      if not df.empty:
        return float(df["close"].iloc[-1])
    except Exception:
      pass
    return 0.0

  async def _get_mock_holdings(self) -> list[dict]:
    """Generates realistic mock holdings for testing in sandbox/dev modes."""
    mock_data = [
      {"symbol": "RELIANCE", "qty": 15, "avg_price": 2810.0},
      {"symbol": "TCS", "qty": 8, "avg_price": 4120.0},
      {"symbol": "INFY", "qty": 25, "avg_price": 1950.0},
      {"symbol": "HDFCBANK", "qty": 40, "avg_price": 1690.0},
      {"symbol": "ITC", "qty": 120, "avg_price": 435.0},
    ]

    holdings = []
    for m in mock_data:
      sym = m["symbol"]
      qty = m["qty"]
      avg_price = m["avg_price"]
      
      current_price = await self._get_live_price(sym)
      if current_price == 0.0:
        current_price = avg_price * 1.02  # standard 2% profit fallback if offline

      invested = avg_price * qty
      current_val = current_price * qty
      pnl = current_val - invested
      pnl_pct = (pnl / invested * 100) if invested > 0 else 0.0

      holdings.append({
        "symbol": sym,
        "quantity": qty,
        "avg_buy_price": round(avg_price, 2),
        "current_price": round(current_price, 2),
        "invested_value": round(invested, 2),
        "current_value": round(current_val, 2),
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 2)
      })

    return holdings
