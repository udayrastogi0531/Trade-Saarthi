"""Watchlist Intelligence Engine for ranking breakout opportunities and evaluating risk scores."""

import asyncio
from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.modules.market_data.engine import MarketDataEngine
from backend.app.modules.technical_analysis.engine import TechnicalAnalysisEngine
from backend.app.schemas.market import CandleRequest

logger = get_logger(__name__)


class WatchlistIntelligenceEngine:
  """Ranks breakout setups, volume spikes, and risk levels across watchlist symbols."""

  def __init__(self) -> None:
    self._settings = get_settings()
    self._market = MarketDataEngine()
    self._ta = TechnicalAnalysisEngine()

  async def scan_watchlist(self) -> dict:
    symbols = self._settings.watchlist
    
    async def analyze_one(sym: str) -> dict | None:
      try:
        df = await self._market.get_candles(
          CandleRequest(symbol=sym, exchange="NSE", interval="15m", limit=100)
        )
        snap = self._ta.analyze(df, sym, "15m")
        
        # Calculate risk score
        risk = 30
        if snap.atr_pct > 3.0:
          risk += 30
        if snap.rsi > 70 or snap.rsi < 30:
          risk += 20
        if snap.is_sideways:
          risk -= 10
        risk = max(10, min(100, risk))

        # Check opportunity status
        vol_ratio = snap.indicators.get("volume_ratio", 1.0)
        is_breakout = vol_ratio > 1.5 and snap.trend_direction == "bullish" and snap.rsi > 55

        return {
          "symbol": sym,
          "price": round(snap.indicators.get("close", 0.0), 2),
          "rsi": round(snap.rsi, 2),
          "trend": snap.trend_direction,
          "trend_strength": round(snap.trend_strength, 2),
          "vol_ratio": round(vol_ratio, 2),
          "is_sideways": snap.is_sideways,
          "is_breakout": is_breakout,
          "risk_score": risk,
          "volume_spike": snap.volume_spike,
        }
      except Exception as e:
        logger.error("watchlist_scan_one_failed", symbol=sym, error=str(e))
        return None

    results = await asyncio.gather(*[analyze_one(s) for s in symbols])
    valid_results = [r for r in results if r is not None]

    # Rank and categorize
    top_opportunities = [
      r for r in valid_results if r["trend"] == "bullish" and r["trend_strength"] > 0.4
    ]
    top_opportunities = sorted(top_opportunities, key=lambda x: x["trend_strength"], reverse=True)

    breakout_candidates = [r for r in valid_results if r["is_breakout"]]
    volume_spikes = [r for r in valid_results if r["volume_spike"]]
    weak_setups = [r for r in valid_results if r["trend"] == "bearish"]

    risk_rankings = sorted(valid_results, key=lambda x: x["risk_score"], reverse=True)

    return {
      "top_opportunities": top_opportunities[:3],
      "breakouts": breakout_candidates[:3],
      "volume_spikes": volume_spikes[:3],
      "weak_setups": weak_setups[:3],
      "risk_rankings": risk_rankings,
    }
