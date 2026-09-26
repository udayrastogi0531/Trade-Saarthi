"""Long-run paper trading analytics — aggregates existing trades only."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import Signal, Trade, TradeJournal
from backend.app.db.session import get_db

router = APIRouter(prefix="/paper", tags=["Paper Trading"])


@router.get("/summary")
async def paper_summary(
  account_id: int = Query(1),
  days: int = Query(30, ge=1, le=365),
  db: AsyncSession = Depends(get_db),
) -> dict:
  since = datetime.utcnow() - timedelta(days=days)
  trades = await db.execute(
    select(Trade).where(
      Trade.account_id == account_id,
      Trade.is_paper.is_(True),
      Trade.opened_at.isnot(None),
      Trade.opened_at >= since,
    )
  )
  rows = list(trades.scalars().all())
  closed = [t for t in rows if t.status == "closed" and t.pnl is not None]
  open_ct = sum(1 for t in rows if t.status == "open")

  wins = sum(1 for t in closed if float(t.pnl or 0) > 0)
  total_pnl = sum(float(t.pnl or 0) for t in closed)

  sig = await db.execute(
    select(
      func.count().filter(Signal.approved.is_(True)).label("appr"),
      func.count().filter(Signal.approved.is_(False)).label("rej"),
    ).where(Signal.account_id == account_id, Signal.created_at >= since)
  )
  s = sig.one()
  appr = int(s.appr or 0)
  rej = int(s.rej or 0)

  return {
    "window_days": days,
    "paper_trades_opened": len(rows),
    "open_positions": open_ct,
    "closed_trades": len(closed),
    "win_rate_pct": round(wins / len(closed) * 100, 2) if closed else 0.0,
    "total_realized_pnl": round(total_pnl, 2),
    "signals_approved": appr,
    "signals_rejected": rej,
    "rejection_rate_pct": round(rej / max(appr + rej, 1) * 100, 2),
    "disclaimer": "Paper results do not guarantee live performance.",
  }


@router.get("/regime-breakdown")
async def paper_regime_breakdown(
  account_id: int = Query(1),
  days: int = Query(30, ge=1, le=180),
  db: AsyncSession = Depends(get_db),
) -> dict:
  since = datetime.utcnow() - timedelta(days=days)
  result = await db.execute(
    select(TradeJournal.market_regime, func.count().label("n"))
    .join(Trade, TradeJournal.trade_id == Trade.id)
    .where(Trade.account_id == account_id, Trade.is_paper.is_(True), TradeJournal.created_at >= since)
    .group_by(TradeJournal.market_regime)
  )
  items = [{"regime": r[0] or "unknown", "count": int(r[1])} for r in result.all()]
  return {"items": items, "window_days": days}
