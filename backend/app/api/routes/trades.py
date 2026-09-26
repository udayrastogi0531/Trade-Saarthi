from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import Trade
from backend.app.db.session import get_db

router = APIRouter(prefix="/trades", tags=["Trades"])


@router.get("/")
async def list_trades(
  account_id: int = Query(1),
  status: str | None = Query(None),
  limit: int = Query(50, le=200),
  db: AsyncSession = Depends(get_db),
) -> dict:
  query = select(Trade).where(Trade.account_id == account_id).order_by(Trade.created_at.desc()).limit(limit)
  if status:
    query = query.where(Trade.status == status)

  result = await db.execute(query)
  trades = result.scalars().all()

  return {
    "items": [
      {
        "id": str(t.id),
        "symbol": t.symbol,
        "direction": t.direction,
        "status": t.status,
        "entry_price": float(t.entry_price) if t.entry_price else None,
        "exit_price": float(t.exit_price) if t.exit_price else None,
        "stop_loss": float(t.stop_loss),
        "target_price": float(t.target_price),
        "quantity": t.quantity,
        "pnl": float(t.pnl) if t.pnl else None,
        "is_paper": t.is_paper,
        "opened_at": t.opened_at.isoformat() if t.opened_at else None,
        "closed_at": t.closed_at.isoformat() if t.closed_at else None,
      }
      for t in trades
    ],
    "total": len(trades),
  }


@router.get("/analytics")
async def trade_analytics(
  account_id: int = Query(1),
  db: AsyncSession = Depends(get_db),
) -> dict:
  result = await db.execute(
    select(Trade).where(Trade.account_id == account_id, Trade.status == "closed")
  )
  closed = result.scalars().all()

  if not closed:
    return {
      "win_rate": 0,
      "total_pnl": 0,
      "sharpe_ratio": 0,
      "trade_count": 0,
    }

  pnls = [float(t.pnl or 0) for t in closed]
  wins = [p for p in pnls if p > 0]
  import numpy as np

  returns = np.array(pnls)
  sharpe = float(returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0

  return {
    "win_rate": round(len(wins) / len(pnls) * 100, 2),
    "total_pnl": round(sum(pnls), 2),
    "sharpe_ratio": round(sharpe, 2),
    "trade_count": len(closed),
    "avg_pnl": round(np.mean(pnls), 2),
  }
