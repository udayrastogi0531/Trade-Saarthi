"""Execution Engine — live order placement (disabled by default)."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.app.config import get_settings
from backend.app.core.exceptions import RiskLimitExceeded
from backend.app.core.logging import get_logger
from backend.app.db.models import ExecutionLog, Trade
from backend.app.schemas.trade import TradeSetup

logger = get_logger(__name__)


class ExecutionEngine:
  """
  Live execution — only when EXECUTION_ENABLED=true and PAPER_TRADING=false.
  Includes retry logic and execution logging.
  """

  def __init__(self) -> None:
    self._settings = get_settings()

  def _ensure_live_allowed(self) -> None:
    if self._settings.paper_trading:
      raise RiskLimitExceeded("Live execution blocked — paper trading mode active")
    if not self._settings.execution_enabled:
      raise RiskLimitExceeded("Live execution disabled — set EXECUTION_ENABLED=true")

  @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
  async def place_order(
    self,
    db: AsyncSession,
    setup: TradeSetup,
    account_id: int,
    atr_pct: float = 0.0,
    structure_fake_risk: float = 0.0,
    manual_confirmed: bool = False,
  ) -> Trade:
    self._ensure_live_allowed()

    from backend.app.modules.execution.safety import ExecutionSafetyEngine

    safety = ExecutionSafetyEngine()
    check = await safety.validate_execution(
      db, account_id, setup, atr_pct, structure_fake_risk
    )
    if not check.approved:
      raise RiskLimitExceeded("; ".join(check.reasons))
    if check.requires_manual_confirm and not manual_confirmed:
      raise RiskLimitExceeded("Manual execution confirmation required")

    broker = self._settings.broker_mode
    order_payload = self._build_order_payload(setup)

    try:
      response = await self._dispatch_to_broker(broker, order_payload)
      status = "submitted"
    except Exception as exc:
      await self._log_execution(db, None, broker, order_payload, {}, "failed", str(exc))
      raise

    trade = Trade(
      account_id=account_id,
      symbol=setup.symbol,
      direction=setup.direction,
      status="open",
      entry_price=Decimal(str(setup.entry)),
      stop_loss=Decimal(str(setup.stop_loss)),
      target_price=Decimal(str(setup.target)),
      quantity=setup.position_size,
      is_paper=False,
      opened_at=datetime.utcnow(),
    )
    db.add(trade)
    await db.flush()
    await self._log_execution(db, trade.id, broker, order_payload, response, status)
    logger.info("live_order_placed", symbol=setup.symbol, broker=broker)
    return trade

  async def _dispatch_to_broker(self, broker: str, payload: dict[str, Any]) -> dict[str, Any]:
    if broker == "kite":
      return await self._place_kite_order(payload)
    raise RiskLimitExceeded(f"Unsupported broker: {broker}")

  async def _place_kite_order(self, payload: dict[str, Any]) -> dict[str, Any]:
    settings = self._settings
    try:
      from kiteconnect import KiteConnect
    except ImportError as exc:
      raise RiskLimitExceeded("kiteconnect not installed") from exc

    kite = KiteConnect(api_key=settings.kite_api_key)
    kite.set_access_token(settings.kite_access_token)
    order_id = kite.place_order(**payload)
    return {"order_id": order_id, "status": "placed"}

  @staticmethod
  def _build_order_payload(setup: TradeSetup) -> dict[str, Any]:
    transaction_type = "BUY" if setup.direction == "BUY" else "SELL"
    return {
      "variety": "regular",
      "exchange": "NSE",
      "tradingsymbol": setup.symbol,
      "transaction_type": transaction_type,
      "quantity": setup.position_size,
      "product": "MIS",
      "order_type": "LIMIT",
      "price": setup.entry,
    }

  @staticmethod
  async def _log_execution(
    db: AsyncSession,
    trade_id,
    broker: str,
    request: dict,
    response: dict,
    status: str,
    error: str | None = None,
  ) -> None:
    log = ExecutionLog(
      trade_id=trade_id,
      broker=broker,
      order_type="entry",
      request_payload=request,
      response_payload=response,
      status=status,
      error_message=error,
    )
    db.add(log)
