"""AI strategy research API — evidence-driven."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import StrategyResearchReport, Trade, TradeJournal
from backend.app.db.session import get_db
from backend.app.modules.analytics.institutional import InstitutionalAnalyticsEngine
from backend.app.modules.regime.research import RegimeResearchEngine
from backend.app.modules.research.engine import StrategyResearchEngine
from backend.app.modules.research.scorecard import StrategyScorecardEngine

router = APIRouter(prefix="/research", tags=["Research"])


class ResearchRequest(BaseModel):
  report_type: str = "full"
  setup_type: str | None = None
  regime: str | None = None
  use_ai_summary: bool = False


@router.post("/analyze")
async def run_research(
  request: ResearchRequest,
  db: AsyncSession = Depends(get_db),
) -> dict:
  engine = StrategyResearchEngine()
  return await engine.generate_report(
    db,
    request.report_type,
    request.setup_type,
    request.regime,
    request.use_ai_summary,
  )


@router.get("/regime-heatmap")
async def regime_heatmap(db: AsyncSession = Depends(get_db)) -> dict:
  items = await RegimeResearchEngine().get_regime_heatmap(db)
  return {"items": items}


@router.get("/institutional-metrics")
async def institutional_metrics(
  account_id: int = Query(1),
  db: AsyncSession = Depends(get_db),
) -> dict:
  result = await db.execute(
    select(Trade).where(Trade.account_id == account_id, Trade.pnl.isnot(None))
  )
  trades = list(result.scalars().all())
  pnls = [float(t.pnl) for t in trades if t.pnl is not None]

  journal_result = await db.execute(select(TradeJournal).limit(200))
  journals = list(journal_result.scalars().all())
  maes = [float(j.mae) for j in journals if j.mae]
  mfes = [float(j.mfe) for j in journals if j.mfe]

  metrics = InstitutionalAnalyticsEngine().compute(pnls, maes, mfes)
  rolling = InstitutionalAnalyticsEngine().rolling_series(pnls)
  return {"metrics": metrics.to_dict(), "rolling": rolling}


@router.get("/scorecards")
async def strategy_scorecards(
  account_id: int = Query(1),
  db: AsyncSession = Depends(get_db),
) -> dict:
  return await StrategyScorecardEngine().build_scorecards(db, account_id)


@router.get("/edge-quality")
async def edge_quality_report(
  account_id: int = Query(1),
  db: AsyncSession = Depends(get_db),
) -> dict:
  return await StrategyScorecardEngine().edge_quality_report(db, account_id)


@router.get("/reports")
async def list_reports(
  limit: int = Query(10, le=50),
  db: AsyncSession = Depends(get_db),
) -> dict:
  result = await db.execute(
    select(StrategyResearchReport).order_by(StrategyResearchReport.created_at.desc()).limit(limit)
  )
  return {
    "items": [
      {
        "id": str(r.id),
        "type": r.report_type,
        "narratives": (r.findings or {}).get("strongest_setups"),
        "created_at": r.created_at.isoformat(),
      }
      for r in result.scalars().all()
    ]
  }
