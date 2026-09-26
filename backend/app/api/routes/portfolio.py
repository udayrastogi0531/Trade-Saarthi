"""Portfolio intelligence API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.modules.market_data.engine import MarketDataEngine
from backend.app.modules.portfolio.engine import PortfolioIntelligenceEngine
from backend.app.schemas.market import CandleRequest

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/analysis")
async def portfolio_analysis(
  account_id: int = Query(1),
  symbols: str = Query("RELIANCE,TCS,INFY"),
  persist: bool = Query(False),
  db: AsyncSession = Depends(get_db),
) -> dict:
  sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
  returns: dict[str, list[float]] = {}
  market = MarketDataEngine()
  for sym in sym_list:
    try:
      df = await market.get_candles(
        CandleRequest(symbol=sym, exchange="NSE", interval="15m", limit=100)
      )
      if len(df) > 10:
        returns[sym] = df["close"].pct_change().dropna().tolist()[-50:]
    except Exception:
      pass

  engine = PortfolioIntelligenceEngine()
  report = await engine.analyze(db, account_id, returns or None)
  if persist:
    await engine.persist(db, report)
  return report.to_dict()


@router.get("/heatmap")
async def portfolio_heatmap(
  account_id: int = Query(1),
  db: AsyncSession = Depends(get_db),
) -> dict:
  report = await PortfolioIntelligenceEngine().analyze(db, account_id)
  return {
    "sector_exposure": report.sector_exposure,
    "portfolio_heat": report.portfolio_heat,
    "risk_score": report.risk_score,
    "concentration_risk": report.concentration_risk,
  }


@router.post("/analyze-position")
async def analyze_position(payload: dict) -> dict:
  symbol = payload.get("symbol", "RELIANCE").upper()
  quantity = int(payload.get("quantity", 10))
  avg_buy_price = float(payload.get("avg_buy_price", 2800.0))
  exchange = payload.get("exchange", "NSE")

  from backend.app.modules.portfolio.assistant import PortfolioAssistantEngine
  from backend.app.modules.market_data.option_chain import OptionChainEngine
  from backend.app.modules.intelligence.news import NewsIntelligenceEngine
  from backend.app.modules.ai_reasoning.father_mode import FatherModeEngine

  assistant = PortfolioAssistantEngine()
  position_analysis = await assistant.analyze_position(symbol, quantity, avg_buy_price, exchange)

  spot = position_analysis.get("current_price", avg_buy_price)
  oc_engine = OptionChainEngine()
  option_chain = oc_engine.calculate_option_chain(symbol, spot)

  news_engine = NewsIntelligenceEngine()
  news = await news_engine.fetch_stock_news(symbol, limit=3)

  father_engine = FatherModeEngine()
  father_explanation = await father_engine.generate_explanation(
    symbol,
    {
      "rsi": position_analysis["technical_data"]["rsi"],
      "trend": position_analysis["technical_data"]["trend"],
      "trend_strength": position_analysis["technical_data"]["trend_strength"],
      "atr_pct": position_analysis["technical_data"]["atr_pct"],
      "close": spot,
    },
    option_chain,
    news
  )

  position_analysis["father_mode"] = father_explanation
  position_analysis["news"] = news
  position_analysis["option_chain_summary"] = {
    "pcr": option_chain.get("pcr", 1.0),
    "support": option_chain.get("support", 0.0),
    "resistance": option_chain.get("resistance", 0.0),
    "max_pain": option_chain.get("max_pain", 0.0),
  }

  return position_analysis


@router.get("")
async def get_portfolio(db: AsyncSession = Depends(get_db)) -> dict:
  from backend.app.modules.portfolio.kite_sync import KitePortfolioSync
  sync = KitePortfolioSync()
  return await sync.fetch_portfolio(db)


@router.get("/margins")
async def get_portfolio_margins(db: AsyncSession = Depends(get_db)) -> dict:
  from backend.app.config import get_settings
  import logging
  
  logger = logging.getLogger(__name__)
  settings = get_settings()
  
  if settings.broker_mode == "kite":
    access_token = settings.kite_access_token
    try:
      from backend.app.services.broker_tokens import BrokerTokenService
      token_service = BrokerTokenService()
      db_token = await token_service.get_latest(db, "kite")
      if db_token and db_token.access_token:
        access_token = db_token.access_token
    except Exception:
      pass
      
    if access_token:
      try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=settings.kite_api_key)
        kite.set_access_token(access_token)
        margins = kite.margins()
        
        equity = margins.get("equity", {})
        cash = float(equity.get("available", {}).get("cash", 0.0) or equity.get("net", 0.0) or 0.0)
        utilized = float(equity.get("utilised", {}).get("debits", 0.0) or 0.0)
        
        return {
          "source": "kite",
          "available_cash": cash,
          "margin_utilized": utilized,
          "buying_power": cash,
          "currency": "INR"
        }
      except Exception as e:
        logger.error(f"failed_to_fetch_kite_margins: {e}")
  
  capital = float(settings.default_account_capital)
  return {
    "source": "mock",
    "available_cash": capital,
    "margin_utilized": 0.0,
    "buying_power": capital,
    "currency": "INR",
    "note": "Using paper account capital. Complete Zerodha Kite login to view actual balances."
  }


@router.get("/holdings/analysis")
async def get_portfolio_analysis(db: AsyncSession = Depends(get_db)) -> dict:
  from backend.app.modules.portfolio.kite_sync import KitePortfolioSync
  from backend.app.modules.portfolio.assistant import PortfolioAssistantEngine
  
  sync = KitePortfolioSync()
  portfolio_data = await sync.fetch_portfolio(db)
  
  assistant = PortfolioAssistantEngine()
  analyzed_holdings = []
  
  for h in portfolio_data.get("holdings", []):
    analysis = await assistant.analyze_position(
      symbol=h["symbol"],
      quantity=h["quantity"],
      avg_buy_price=h["avg_buy_price"]
    )
    # Merge Kite holdings metrics
    analysis["invested_value"] = h["invested_value"]
    analysis["current_value"] = h["current_value"]
    analysis["pnl"] = h["pnl"]
    analysis["pnl_pct"] = h["pnl_pct"]
    analyzed_holdings.append(analysis)
    
  return {
    "holdings": analyzed_holdings,
    "summary": portfolio_data["summary"]
  }


@router.get("/health")
async def get_portfolio_health(symbol: str = Query("RELIANCE")) -> dict:
  from backend.app.modules.portfolio.health_score import StockHealthScore
  score = StockHealthScore()
  return await score.calculate_score(symbol.upper())
