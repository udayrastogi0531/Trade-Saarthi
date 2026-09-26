"""Risk Management Engine — capital protection and position sizing."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.exceptions import RiskLimitExceeded
from backend.app.core.logging import get_logger
from backend.app.db.models import Account, RiskState, Trade
from backend.app.schemas.trade import TradeSetup

logger = get_logger(__name__)


@dataclass
class RiskCheckResult:
  approved: bool
  position_size: int
  position_value: float
  risk_amount: float
  reasons: list[str]
  kill_switch_active: bool = False


class RiskEngine:
  """
  Institutional risk controls:
  - max daily loss, max drawdown, position sizing
  - exposure limits, max trades/day, kill switch
  """

  def __init__(self) -> None:
    self._settings = get_settings()

  async def validate_trade(
    self,
    db: AsyncSession,
    account_id: int,
    setup: TradeSetup,
    capital: float | None = None,
    open_symbols: list[str] | None = None,
  ) -> RiskCheckResult:
    account = await self._get_account(db, account_id)
    equity = float(capital or account.capital)
    risk_state = await self._get_or_create_risk_state(db, account_id, equity)

    reasons: list[str] = []

    if risk_state.kill_switch_active:
      reasons.append(f"Kill switch active: {risk_state.kill_switch_reason or 'manual'}")
      return RiskCheckResult(False, 0, 0, 0, reasons, kill_switch_active=True)

    daily_loss_limit = equity * (self._settings.max_daily_loss_pct / 100)
    if float(risk_state.daily_pnl) <= -daily_loss_limit:
      reasons.append(
        f"Max daily loss reached ({self._settings.max_daily_loss_pct}% of capital)"
      )

    if float(risk_state.current_drawdown_pct) >= self._settings.max_drawdown_pct:
      reasons.append(
        f"Max drawdown exceeded ({risk_state.current_drawdown_pct}% >= "
        f"{self._settings.max_drawdown_pct}%)"
      )

    if risk_state.trades_today >= self._settings.max_trades_per_day:
      reasons.append(f"Max trades per day ({self._settings.max_trades_per_day}) reached")

    open_symbols = open_symbols or await self._open_symbols(db, account_id)
    if setup.symbol in open_symbols:
      reasons.append(f"Already exposed to {setup.symbol}")

    if len(open_symbols) >= 3:
      reasons.append("Max concurrent positions (3) reached")

    risk_per_share = abs(setup.entry - setup.stop_loss)
    if risk_per_share <= 0:
      reasons.append("Invalid stop loss — zero risk distance")

    max_risk_amount = equity * (self._settings.max_position_size_pct / 100)
    position_size = int(max_risk_amount / risk_per_share) if risk_per_share else 0

    if position_size < 1:
      reasons.append("Position size too small for risk parameters")

    position_value = position_size * setup.entry
    max_position_value = equity * 0.25
    if position_value > max_position_value:
      position_size = int(max_position_value / setup.entry)
      position_value = position_size * setup.entry

    risk_amount = position_size * risk_per_share

    if setup.risk_reward < self._settings.min_risk_reward:
      reasons.append(f"Risk-reward below policy minimum ({self._settings.min_risk_reward})")

    approved = len(reasons) == 0

    if approved:
      logger.info(
        "risk_approved",
        symbol=setup.symbol,
        position_size=position_size,
        risk_amount=risk_amount,
      )
    else:
      logger.warning("risk_rejected", symbol=setup.symbol, reasons=reasons)

    return RiskCheckResult(
      approved=approved,
      position_size=position_size if approved else 0,
      position_value=round(position_value, 2) if approved else 0,
      risk_amount=round(risk_amount, 2) if approved else 0,
      reasons=reasons,
      kill_switch_active=risk_state.kill_switch_active,
    )

  def apply_sizing_to_setup(self, setup: TradeSetup, risk: RiskCheckResult) -> TradeSetup:
    return setup.model_copy(
      update={
        "position_size": risk.position_size,
        "position_value": risk.position_value,
        "risk_amount": risk.risk_amount,
      }
    )

  async def activate_kill_switch(
    self, db: AsyncSession, account_id: int, reason: str
  ) -> None:
    risk_state = await self._get_or_create_risk_state(
      db, account_id, self._settings.default_account_capital
    )
    risk_state.kill_switch_active = True
    risk_state.kill_switch_reason = reason
    logger.critical("kill_switch_activated", account_id=account_id, reason=reason)
    raise RiskLimitExceeded(f"Kill switch activated: {reason}")

  async def _get_account(self, db: AsyncSession, account_id: int) -> Account:
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
      raise RiskLimitExceeded(f"Account {account_id} not found")
    return account

  async def _get_or_create_risk_state(
    self, db: AsyncSession, account_id: int, equity: float
  ) -> RiskState:
    today = date.today()
    result = await db.execute(
      select(RiskState).where(
        RiskState.account_id == account_id,
        RiskState.trade_date == today,
      )
    )
    state = result.scalar_one_or_none()
    if state:
      return state

    state = RiskState(
      account_id=account_id,
      trade_date=today,
      peak_equity=Decimal(str(equity)),
      daily_pnl=Decimal("0"),
      trades_today=0,
    )
    db.add(state)
    await db.flush()
    return state

  async def get_open_symbols(self, db: AsyncSession, account_id: int) -> list[str]:
    return await self._open_symbols(db, account_id)

  async def _open_symbols(self, db: AsyncSession, account_id: int) -> list[str]:
    result = await db.execute(
      select(Trade.symbol).where(
        Trade.account_id == account_id,
        Trade.status == "open",
      )
    )
    return list(result.scalars().all())
