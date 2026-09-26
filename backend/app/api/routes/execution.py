from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import RiskLimitExceeded, http_exception_from_domain
from backend.app.db.session import get_db
from backend.app.modules.execution.safety import ExecutionSafetyEngine
from backend.app.modules.execution.simulation import ExecutionSimulationEngine
from backend.app.schemas.trade import TradeSetup

router = APIRouter(prefix="/execution", tags=["Execution Safety"])


class SafetyCheckRequest(BaseModel):
  account_id: int = 1
  setup: TradeSetup
  atr_pct: float = 0.0
  structure_fake_risk: float = 0.0


@router.post("/safety-check")
async def safety_check(
  request: SafetyCheckRequest,
  db: AsyncSession = Depends(get_db),
) -> dict:
  engine = ExecutionSafetyEngine()
  result = await engine.validate_execution(
    db,
    request.account_id,
    request.setup,
    request.atr_pct,
    request.structure_fake_risk,
  )
  return {
    "approved": result.approved,
    "reasons": result.reasons,
    "requires_manual_confirm": result.requires_manual_confirm,
    "slippage_cap_pct": result.slippage_cap,
  }


class SimulateExecutionRequest(BaseModel):
  symbol: str
  direction: str = "BUY"
  expected_price: float
  quantity: int = 1
  spread_bps: float = 5.0
  broker_down: bool = False
  persist: bool = True


@router.post("/simulate")
async def simulate_execution(
  request: SimulateExecutionRequest,
  db: AsyncSession = Depends(get_db),
) -> dict:
  sim = ExecutionSimulationEngine()
  fill = sim.simulate_order(
    request.symbol,
    request.direction,
    request.expected_price,
    request.quantity,
    request.spread_bps,
    request.broker_down,
  )
  if request.persist:
    await sim.log_fill(db, fill, request.symbol, request.expected_price)
  return {
    "fill_price": fill.fill_price,
    "slippage_bps": fill.slippage_bps,
    "latency_ms": fill.latency_ms,
    "partial_fill": fill.partial_fill,
    "rejected": fill.rejected,
    "rejection_reason": fill.rejection_reason,
  }


@router.get("/quality-analytics")
async def execution_quality_analytics(db: AsyncSession = Depends(get_db)) -> dict:
  return (await ExecutionSimulationEngine().get_analytics(db)).__dict__
