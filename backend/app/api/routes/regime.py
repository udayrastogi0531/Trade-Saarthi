from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import MarketRegimeRecord
from backend.app.db.session import get_db
from backend.app.modules.market_data.engine import MarketDataEngine
from backend.app.modules.market_regime.engine import RegimeEngine
from backend.app.modules.technical_analysis.engine import TechnicalAnalysisEngine
from backend.app.schemas.market import CandleRequest

router = APIRouter(prefix="/regime", tags=["Market Regime"])


class RegimeRequest(BaseModel):
  symbol: str
  exchange: str = "NSE"


@router.post("/detect")
async def detect_regime(request: RegimeRequest, db: AsyncSession = Depends(get_db)) -> dict:
  market = MarketDataEngine()
  df = await market.get_candles(
    CandleRequest(symbol=request.symbol, exchange=request.exchange, interval="15m", limit=200)
  )
  snap = TechnicalAnalysisEngine().analyze(df, request.symbol, "15m")
  regime = RegimeEngine().detect(df, request.symbol, snap)
  return {
    "symbol": request.symbol,
    "regime": regime.regime.value,
    "confidence": regime.confidence,
    "allowed_setups": regime.allowed_setups,
    "position_size_multiplier": regime.position_size_multiplier,
    "metrics": regime.metrics,
  }


@router.get("/history/{symbol}")
async def regime_history(symbol: str, limit: int = 20, db: AsyncSession = Depends(get_db)) -> dict:
  result = await db.execute(
    select(MarketRegimeRecord)
    .where(MarketRegimeRecord.symbol == symbol.upper())
    .order_by(MarketRegimeRecord.recorded_at.desc())
    .limit(limit)
  )
  rows = result.scalars().all()
  return {
    "items": [
      {
        "regime": r.regime,
        "confidence": float(r.confidence),
        "metrics": r.metrics,
        "recorded_at": r.recorded_at.isoformat(),
      }
      for r in rows
    ]
  }
