from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_pipeline
from backend.app.db.session import get_db
from backend.app.schemas.trade import SignalRequest, SignalResponse
from backend.app.services.trading_pipeline import TradingPipeline

router = APIRouter(prefix="/signals", tags=["Signals"])


@router.post("/analyze", response_model=SignalResponse)
async def analyze_signal(
  request: SignalRequest,
  db: AsyncSession = Depends(get_db),
  pipeline: TradingPipeline = Depends(get_pipeline),
) -> SignalResponse:
  """
  Full pipeline: market data → technical analysis → strategy → risk → AI → alerts.
  """
  return await pipeline.generate_signal(db, request)
