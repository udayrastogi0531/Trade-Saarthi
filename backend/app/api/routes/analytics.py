from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.modules.journal.analytics import JournalAnalyticsEngine
from backend.app.modules.risk.advanced import AdvancedRiskEngine

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/journal")
async def journal_analytics(
  account_id: int = Query(1),
  advanced: bool = Query(False),
  db: AsyncSession = Depends(get_db),
) -> dict:
  engine = JournalAnalyticsEngine()
  if advanced:
    return await engine.get_advanced_analytics(db, account_id)
  return await engine.get_analytics(db, account_id)


@router.get("/correlation")
async def correlation_heatmap(symbols: str = Query("RELIANCE,TCS,INFY")) -> dict:
  sym_list = [s.strip().upper() for s in symbols.split(",")]
  matrix = AdvancedRiskEngine().correlation_matrix(sym_list)
  return {"symbols": sym_list, "matrix": matrix}
