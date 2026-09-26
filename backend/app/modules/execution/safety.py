"""Advanced execution safety — pre-live protections."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.exceptions import RiskLimitExceeded
from backend.app.core.logging import get_logger
from backend.app.core.metrics import EXECUTION_FAILURES
from backend.app.db.models import ExecutionSafetyLog, RiskState, Trade
from backend.app.schemas.trade import TradeSetup

logger = get_logger(__name__)


@dataclass
class SafetyCheckResult:
  approved: bool
  reasons: list[str] = field(default_factory=list)
  requires_manual_confirm: bool = False
  slippage_cap: float = 0.0


class ExecutionSafetyEngine:
  """
  Duplicate prevention, cooldown, volatility shutdown, manual confirm mode.
  Global kill switch integration via RiskEngine.
  """

  def __init__(self) -> None:
    self._settings = get_settings()

  async def validate_execution(
    self,
    db: AsyncSession,
    account_id: int,
    setup: TradeSetup,
    current_atr_pct: float = 0.0,
    structure_fake_risk: float = 0.0,
  ) -> SafetyCheckResult:
    reasons: list[str] = []
    requires_confirm = self._settings.execution_manual_confirm

    # Kill switch via risk state
    risk = await self._risk_state(db, account_id)
    if risk and risk.kill_switch_active:
      reasons.append(f"Global kill switch: {risk.kill_switch_reason}")

    # Volatility shutdown
    if current_atr_pct >= self._settings.volatility_shutdown_atr_pct:
      reasons.append(f"Volatility shutdown — ATR {current_atr_pct:.1f}% exceeds limit")

    # Consecutive losses cooldown
    if await self._in_loss_cooldown(db, account_id):
      reasons.append(
        f"Cooldown active after consecutive losses ({self._settings.execution_cooldown_minutes}m)"
      )

    # Duplicate trade window
    if await self._duplicate_trade(db, account_id, setup):
      reasons.append(f"Duplicate {setup.symbol} trade within window")

    # Structure-based block
    if structure_fake_risk > 0.7:
      reasons.append("Structure indicates high fake breakout risk — execution blocked")

    # Max open positions
    open_count = await self._open_count(db, account_id)
    if open_count >= 3:
      reasons.append("Max concurrent positions for execution")

    approved = len(reasons) == 0
    if not approved:
      EXECUTION_FAILURES.inc()
      logger.warning("execution_safety_blocked", symbol=setup.symbol, reasons=reasons)
    await self._log_check(db, account_id, "full_validation", approved, {"reasons": reasons})

    return SafetyCheckResult(
      approved=approved,
      reasons=reasons,
      requires_manual_confirm=requires_confirm and approved,
      slippage_cap=self._settings.execution_max_slippage_pct,
    )

  async def confirm_execution(
    self, db: AsyncSession, account_id: int, setup: TradeSetup, confirmed: bool
  ) -> None:
    if not confirmed:
      raise RiskLimitExceeded("Manual execution confirmation not provided")
    await self._log_check(db, account_id, "manual_confirm", True, {"symbol": setup.symbol})

  async def _in_loss_cooldown(self, db: AsyncSession, account_id: int) -> bool:
    since = datetime.utcnow() - timedelta(minutes=self._settings.execution_cooldown_minutes)
    result = await db.execute(
      select(Trade)
      .where(
        Trade.account_id == account_id,
        Trade.status == "closed",
        Trade.closed_at >= since,
      )
      .order_by(Trade.closed_at.desc())
      .limit(5)
    )
    losses = [t for t in result.scalars().all() if t.pnl is not None and float(t.pnl) < 0]
    return len(losses) >= 3

  async def _duplicate_trade(
    self, db: AsyncSession, account_id: int, setup: TradeSetup
  ) -> bool:
    since = datetime.utcnow() - timedelta(minutes=self._settings.execution_duplicate_window_minutes)
    result = await db.execute(
      select(Trade).where(
        Trade.account_id == account_id,
        Trade.symbol == setup.symbol,
        Trade.direction == setup.direction,
        Trade.created_at >= since,
      )
    )
    return result.scalar_one_or_none() is not None

  async def _open_count(self, db: AsyncSession, account_id: int) -> int:
    result = await db.execute(
      select(Trade).where(Trade.account_id == account_id, Trade.status == "open")
    )
    return len(result.scalars().all())

  async def _risk_state(self, db: AsyncSession, account_id: int) -> RiskState | None:
    result = await db.execute(
      select(RiskState).where(
        RiskState.account_id == account_id,
        RiskState.trade_date == date.today(),
      )
    )
    return result.scalar_one_or_none()

  async def _log_check(
    self, db: AsyncSession, account_id: int, check_type: str, passed: bool, details: dict
  ) -> None:
    log = ExecutionSafetyLog(
      account_id=account_id,
      check_type=check_type,
      passed=passed,
      details=details,
    )
    db.add(log)
