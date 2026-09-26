"""Opportunity Engine for ranking Top Buy Candidates and Top Exit/Sell Candidates."""

import asyncio
from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.modules.portfolio.health_score import StockHealthScore
from backend.app.modules.portfolio.assistant import PortfolioAssistantEngine

logger = get_logger(__name__)


class OpportunityEngine:
  """Ranks breakout buy candidates vs flagging broken portfolio holdings."""

  def __init__(self) -> None:
    self._settings = get_settings()
    self._health = StockHealthScore()
    self._assistant = PortfolioAssistantEngine()

  async def find_buy_candidates(self) -> list[dict]:
    watchlist = self._settings.watchlist
    
    async def get_health(sym: str) -> dict | None:
      try:
        h = await self._health.calculate_score(sym)
        # Fetch status recommendation
        position_analysis = await self._assistant.analyze_position(sym, 1, 100.0)
        h["status"] = position_analysis.get("status", "HOLD")
        h["confidence"] = position_analysis.get("confidence", 70)
        h["reason"] = position_analysis.get("reason_summary", "")
        return h
      except Exception as e:
        logger.error("buy_engine_scan_failed", symbol=sym, error=str(e))
        return None

    results = await asyncio.gather(*[get_health(s) for s in watchlist])
    valid = [r for r in results if r is not None]

    # Filter candidates suitable for buying (Health Score >= 70 or recommendation status BUY)
    buys = [r for r in valid if r["health_score"] >= 65 or r["status"] == "BUY"]
    buys = sorted(buys, key=lambda x: x["health_score"], reverse=True)
    return buys

  async def find_sell_candidates(self, holdings_list: list[dict]) -> list[dict]:
    sells = []
    
    async def check_sell(h: dict) -> dict | None:
      try:
        sym = h["symbol"]
        qty = h["quantity"]
        avg_price = h["avg_buy_price"]
        
        # Analyze using assistant
        analysis = await self._assistant.analyze_position(sym, qty, avg_price)
        health_info = await self._health.calculate_score(sym)
        
        # We flag for reduce/sell if health score is low (< 50) or status is REDUCE/EXIT
        if health_info["health_score"] < 50 or analysis["status"] in ("REDUCE", "EXIT"):
          return {
            "symbol": sym,
            "status": analysis["status"],
            "health_score": health_info["health_score"],
            "pnl": h["pnl"],
            "pnl_pct": h["pnl_pct"],
            "reason": analysis["reason_summary"]
          }
      except Exception as e:
        logger.error("sell_engine_check_failed", symbol=h.get("symbol"), error=str(e))
      return None

    results = await asyncio.gather(*[check_sell(item) for item in holdings_list])
    sells = [r for r in results if r is not None]
    
    # Sort sells by worst health score first (lowest health_score)
    sells = sorted(sells, key=lambda x: x["health_score"])
    return sells
