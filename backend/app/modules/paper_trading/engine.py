"""Paper Trading Engine — simulated execution before live trading."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import get_logger
from backend.app.db.models import Signal, Trade
from backend.app.schemas.trade import TradeSetup

logger = get_logger(__name__)


class PaperTradingEngine:
  async def open_trade(
    self,
    db: AsyncSession,
    account_id: int,
    setup: TradeSetup,
    signal_id: UUID | None = None,
  ) -> Trade:
    trade = Trade(
      signal_id=signal_id,
      account_id=account_id,
      symbol=setup.symbol,
      direction=setup.direction,
      status="open",
      entry_price=Decimal(str(setup.entry)),
      stop_loss=Decimal(str(setup.stop_loss)),
      target_price=Decimal(str(setup.target)),
      quantity=setup.position_size,
      is_paper=True,
      opened_at=datetime.utcnow(),
    )
    db.add(trade)
    await db.flush()
    logger.info(
      "paper_trade_opened",
      trade_id=str(trade.id),
      symbol=setup.symbol,
      qty=setup.position_size,
    )
    return trade

  async def close_trade(
    self,
    db: AsyncSession,
    trade: Trade,
    exit_price: float,
    reason: str = "manual",
  ) -> Trade:
    entry = float(trade.entry_price or 0)
    qty = trade.quantity
    if trade.direction == "BUY":
      pnl = (exit_price - entry) * qty
    else:
      pnl = (entry - exit_price) * qty

    trade.exit_price = Decimal(str(exit_price))
    trade.pnl = Decimal(str(round(pnl, 2)))
    trade.pnl_pct = Decimal(str(round((pnl / (entry * qty)) * 100, 4))) if entry * qty else Decimal("0")
    trade.status = "closed"
    trade.closed_at = datetime.utcnow()

    logger.info("paper_trade_closed", trade_id=str(trade.id), pnl=pnl, reason=reason)
    return trade
