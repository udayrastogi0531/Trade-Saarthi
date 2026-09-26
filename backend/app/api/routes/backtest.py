from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import BacktestRun
from backend.app.db.session import get_db
from backend.app.modules.backtesting.advanced import AdvancedBacktestEngine
from backend.app.modules.backtesting.engine import BacktestEngine
from backend.app.modules.market_data.engine import MarketDataEngine
from backend.app.schemas.market import CandleRequest

router = APIRouter(prefix="/backtest", tags=["Backtesting"])


class BacktestRequest(BaseModel):
  symbol: str = Field(..., examples=["RELIANCE"])
  exchange: str = "NSE"
  interval: str = "15m"
  initial_capital: float = 100_000
  risk_per_trade_pct: float = 1.0
  advanced: bool = False
  slippage_bps: float = 5.0
  commission_per_trade: float = 20.0


@router.post("/run")
async def run_backtest(
  request: BacktestRequest,
  db: AsyncSession = Depends(get_db),
) -> dict:
  market = MarketDataEngine()
  df = await market.get_candles(
    CandleRequest(symbol=request.symbol, exchange=request.exchange, interval=request.interval, limit=500)
  )

  from datetime import date

  if request.advanced:
    engine = AdvancedBacktestEngine()
    metrics, detail = engine.run_advanced(
      df,
      request.symbol,
      request.interval,
      initial_capital=request.initial_capital,
      risk_per_trade_pct=request.risk_per_trade_pct,
      slippage_bps=request.slippage_bps,
      commission_per_trade=request.commission_per_trade,
    )
    metrics_dict = metrics.to_dict()
    sample_trades = detail.get("sample_trades", [])
  else:
    engine = BacktestEngine()
    metrics, trades = engine.run(
      df,
      request.symbol,
      request.interval,
      initial_capital=request.initial_capital,
      risk_per_trade_pct=request.risk_per_trade_pct,
    )
    metrics_dict = metrics.to_dict()
    sample_trades = trades[-10:]
    detail = {}

  record = BacktestRun(
    strategy_name="multi_setup_advanced" if request.advanced else "multi_setup",
    symbol=request.symbol,
    start_date=df["timestamp"].iloc[0].date() if hasattr(df["timestamp"].iloc[0], "date") else date.today(),
    end_date=df["timestamp"].iloc[-1].date() if hasattr(df["timestamp"].iloc[-1], "date") else date.today(),
    parameters=request.model_dump(),
    metrics=metrics_dict,
  )
  db.add(record)
  await db.flush()

  return {
    "backtest_id": str(record.id),
    "metrics": metrics_dict,
    "detail": detail,
    "sample_trades": sample_trades,
  }
