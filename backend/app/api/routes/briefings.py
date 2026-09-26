from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import MarketBriefing
from backend.app.db.session import get_db
from backend.app.modules.briefings.engine import BriefingEngine

router = APIRouter(prefix="/briefings", tags=["Market Briefings"])


@router.post("/generate")
async def generate_briefing(
  briefing_type: str = Query("intraday", pattern="^(pre_market|intraday|post_market)$"),
  account_id: int = Query(1),
  db: AsyncSession = Depends(get_db),
) -> dict:
  engine = BriefingEngine()
  return await engine.generate(db, briefing_type, account_id)


@router.get("/latest")
async def latest_briefings(limit: int = 5, db: AsyncSession = Depends(get_db)) -> dict:
  result = await db.execute(
    select(MarketBriefing).order_by(MarketBriefing.created_at.desc()).limit(limit)
  )
  rows = result.scalars().all()
  return {
    "items": [
      {
        "id": str(r.id),
        "type": r.briefing_type,
        "content": r.content[:500] + "..." if len(r.content) > 500 else r.content,
        "summary": r.summary,
        "created_at": r.created_at.isoformat(),
      }
      for r in rows
    ]
  }
