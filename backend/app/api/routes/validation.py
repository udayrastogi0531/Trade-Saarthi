"""Walk-forward validation & Monte Carlo risk APIs."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import MonteCarloRun, Trade, WalkForwardRun
from backend.app.db.session import get_db
from backend.app.modules.market_data.engine import MarketDataEngine
from backend.app.modules.validation.monte_carlo import MonteCarloConfig, MonteCarloRiskEngine
from backend.app.modules.validation.walk_forward import WalkForwardEngine
from backend.app.schemas.market import CandleRequest

router = APIRouter(prefix="/validation", tags=["Validation"])


class WalkForwardRequest(BaseModel):
  symbol: str = Field(..., examples=["RELIANCE"])
  exchange: str = "NSE"
  strategy_name: str = "multi_setup"
  windows: int | None = None
  persist: bool = True


class MonteCarloRequest(BaseModel):
  account_id: int = 1
  strategy_name: str | None = None
  simulations: int | None = None
  initial_capital: float = 100_000
  persist: bool = True


@router.post("/walk-forward")
async def run_walk_forward(
  request: WalkForwardRequest,
  db: AsyncSession = Depends(get_db),
) -> dict:
  market = MarketDataEngine()
  df = await market.get_candles(
    CandleRequest(symbol=request.symbol, exchange=request.exchange, interval="15m", limit=800)
  )
  engine = WalkForwardEngine()
  report = engine.run(df, request.symbol, request.strategy_name, windows=request.windows)
  row = None
  if request.persist:
    row = await engine.persist(db, report)
  return {"report": report.to_dict(), "run_id": str(row.id) if row else None}


@router.post("/monte-carlo")
async def run_monte_carlo(
  request: MonteCarloRequest,
  db: AsyncSession = Depends(get_db),
) -> dict:
  result = await db.execute(
    select(Trade).where(Trade.account_id == request.account_id, Trade.pnl.isnot(None)).limit(500)
  )
  pnls = [float(t.pnl) for t in result.scalars().all() if t.pnl is not None]

  config = MonteCarloConfig(
    simulations=request.simulations or 2000,
    initial_capital=request.initial_capital,
  )
  engine = MonteCarloRiskEngine()
  report = engine.simulate(pnls, config)
  row = None
  if request.persist:
    row = await engine.persist(db, report, config, request.account_id, request.strategy_name)
  return {"report": report.to_dict(), "run_id": str(row.id) if row else None}


@router.get("/walk-forward/history")
async def walk_forward_history(
  limit: int = Query(10, le=50),
  db: AsyncSession = Depends(get_db),
) -> dict:
  result = await db.execute(
    select(WalkForwardRun).order_by(WalkForwardRun.created_at.desc()).limit(limit)
  )
  runs = result.scalars().all()
  return {
    "items": [
      {
        "id": str(r.id),
        "strategy": r.strategy_name,
        "symbol": r.symbol,
        "stability_score": float(r.stability_score or 0),
        "overfitting": r.overfitting_flag,
        "decay": r.decay_detected,
        "created_at": r.created_at.isoformat(),
      }
      for r in runs
    ]
  }


@router.get("/monte-carlo/history")
async def monte_carlo_history(
  limit: int = Query(10, le=50),
  db: AsyncSession = Depends(get_db),
) -> dict:
  result = await db.execute(
    select(MonteCarloRun).order_by(MonteCarloRun.created_at.desc()).limit(limit)
  )
  runs = result.scalars().all()
  return {
    "items": [
      {
        "id": str(r.id),
        "survival_probability": float(r.survival_probability or 0),
        "probability_of_ruin": float(r.probability_of_ruin or 0),
        "expected_drawdown_pct": float(r.expected_drawdown_pct or 0),
        "created_at": r.created_at.isoformat(),
      }
      for r in runs
    ]
  }
