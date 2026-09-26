"""AI Market Intelligence Panel API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.modules.intelligence.panel import IntelligencePanel
from backend.app.modules.learning.engine import LearningEngine
from backend.app.modules.market_data.engine import MarketDataEngine
from backend.app.modules.market_structure.engine import MarketStructureEngine
from backend.app.modules.technical_analysis.engine import TechnicalAnalysisEngine
from backend.app.schemas.market import CandleRequest

router = APIRouter(prefix="/intelligence", tags=["Market Intelligence"])


@router.get("/panel")
async def intelligence_panel(
  account_id: int = Query(1),
  db: AsyncSession = Depends(get_db),
) -> dict:
  panel = IntelligencePanel()
  return await panel.build(db, account_id)


@router.get("/structure/{symbol}")
async def market_structure(symbol: str, db: AsyncSession = Depends(get_db)) -> dict:
  market = MarketDataEngine()
  df = await market.get_candles(
    CandleRequest(symbol=symbol.upper(), exchange="NSE", interval="15m", limit=150)
  )
  snap = TechnicalAnalysisEngine().analyze(df, symbol.upper(), "15m")
  analysis = MarketStructureEngine().analyze(df, symbol.upper(), "15m")
  return {"technical": {"rsi": snap.rsi, "trend": snap.trend_direction}, "structure": analysis.to_dict()}


@router.get("/learning/rankings")
async def setup_rankings(
  regime: str | None = None,
  db: AsyncSession = Depends(get_db),
) -> dict:
  engine = LearningEngine()
  return {"rankings": await engine.rank_setups(db, regime)}


@router.get("/news")
async def get_news(symbol: str = Query("RELIANCE")) -> list[dict]:
  from backend.app.modules.intelligence.news import NewsIntelligenceEngine
  engine = NewsIntelligenceEngine()
  return await engine.fetch_stock_news(symbol)


@router.get("/watchlist-opportunities")
async def get_watchlist_opportunities() -> dict:
  from backend.app.modules.scanner.watchlist_intelligence import WatchlistIntelligenceEngine
  engine = WatchlistIntelligenceEngine()
  return await engine.scan_watchlist()


@router.get("/alerts")
async def get_active_alerts() -> dict:
  from backend.app.modules.scanner.watchlist_intelligence import WatchlistIntelligenceEngine
  from backend.app.modules.telegram.alerts import ActiveAlertManager
  
  scanner = WatchlistIntelligenceEngine()
  watchlist_data = await scanner.scan_watchlist()
  
  flat_items = []
  # Collect all analyzed symbols to evaluate alerts
  seen = set()
  for category in ("breakouts", "volume_spikes", "risk_rankings", "top_opportunities"):
    for item in watchlist_data.get(category, []):
      sym = item.get("symbol")
      if sym not in seen:
        seen.add(sym)
        flat_items.append(item)

  manager = ActiveAlertManager()
  active_alerts = manager.identify_alerts(flat_items)

  voice_msg = "Market stability support zones par trade kar raha hai."
  voice_file_path = None
  if active_alerts:
    # Use first active alert as priority voice broadcast
    voice_msg = active_alerts[0]["voice_text"]
    voice_file_path = manager.generate_voice_alert(voice_msg, "alert.mp3")
  else:
    voice_file_path = manager.generate_voice_alert(voice_msg, "alert.mp3")

  return {
    "alerts": active_alerts,
    "voice_text": voice_msg,
    "audio_available": voice_file_path is not None,
    "relative_audio_path": "static/alert.mp3" if voice_file_path else None
  }
