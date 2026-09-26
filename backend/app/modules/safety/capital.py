"""Live capital safety — staged rollout, emergency shutdown, human approval."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models import CapitalSafetyState, RiskState

logger = get_logger(__name__)


class CapitalSafetyFramework:
  """
  Prevents reckless live scaling.

  Stages: sandbox → tiny_live → staged → full
  """

  STAGES = ("sandbox", "tiny_live", "staged", "full")

  def __init__(self) -> None:
    self._settings = get_settings()

  async def get_or_create_state(self, db: AsyncSession, account_id: int = 1) -> CapitalSafetyState:
    result = await db.execute(
      select(CapitalSafetyState).where(CapitalSafetyState.account_id == account_id)
    )
    row = result.scalar_one_or_none()
    if row:
      return row
    row = CapitalSafetyState(
      account_id=account_id,
      deployment_stage=self._settings.default_deployment_stage,
      max_live_capital=Decimal(str(self._settings.tiny_live_max_capital)),
      human_approval_required=True,
    )
    db.add(row)
    await db.flush()
    return row

  async def can_execute_live(
    self,
    db: AsyncSession,
    account_id: int = 1,
    order_notional: float = 0,
  ) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not self._settings.capital_safety_enabled:
      return True, reasons

    state = await self.get_or_create_state(db, account_id)

    if state.emergency_shutdown:
      return False, [f"Emergency shutdown active: {state.shutdown_reason or 'unspecified'}"]

    risk = await db.execute(
      select(RiskState).where(RiskState.account_id == account_id).order_by(RiskState.updated_at.desc())
    )
    risk_row = risk.scalars().first()
    if risk_row and risk_row.kill_switch_active:
      return False, ["Risk kill switch active"]

    if state.deployment_stage == "sandbox":
      return False, ["Sandbox mode — live execution blocked"]

    if state.deployment_stage == "tiny_live":
      max_cap = float(state.max_live_capital or self._settings.tiny_live_max_capital)
      if order_notional > max_cap * 0.1:
        reasons.append(f"Order exceeds 10% of tiny-live cap ({max_cap})")

    if state.human_approval_required and self._settings.execution_manual_confirm:
      reasons.append("Human approval required before live order")

    if reasons and state.deployment_stage in ("tiny_live", "staged"):
      return False, reasons

    return True, reasons

  async def emergency_shutdown(
    self, db: AsyncSession, account_id: int, reason: str
  ) -> CapitalSafetyState:
    state = await self.get_or_create_state(db, account_id)
    state.emergency_shutdown = True
    state.shutdown_reason = reason
    logger.warning("emergency_shutdown", account_id=account_id, reason=reason)
    return state

  async def set_deployment_stage(
    self, db: AsyncSession, account_id: int, stage: str, max_capital: float | None = None
  ) -> CapitalSafetyState:
    if stage not in self.STAGES:
      raise ValueError(f"Invalid stage: {stage}")
    state = await self.get_or_create_state(db, account_id)
    state.deployment_stage = stage
    state.emergency_shutdown = False
    state.shutdown_reason = None
    if max_capital is not None:
      state.max_live_capital = Decimal(str(max_capital))
    return state
