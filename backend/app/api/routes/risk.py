from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import RiskLimitExceeded, http_exception_from_domain
from backend.app.db.session import get_db
from backend.app.modules.risk.engine import RiskEngine

router = APIRouter(prefix="/risk", tags=["Risk Management"])


class KillSwitchRequest(BaseModel):
  account_id: int = 1
  reason: str = Field(..., min_length=3, max_length=256)


@router.post("/kill-switch")
async def activate_kill_switch(
  request: KillSwitchRequest,
  db: AsyncSession = Depends(get_db),
) -> dict:
  engine = RiskEngine()
  try:
    await engine.activate_kill_switch(db, request.account_id, request.reason)
  except RiskLimitExceeded as exc:
    raise http_exception_from_domain(exc) from exc
  return {"status": "kill_switch_activated", "reason": request.reason}
