from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import ChartAnalysisRecord
from backend.app.db.session import get_db
from backend.app.modules.chart_analysis.engine import ChartAnalysisEngine

router = APIRouter(prefix="/chart", tags=["Chart Analysis"])


@router.post("/analyze")
async def analyze_chart(
  file: UploadFile = File(...),
  symbol: str | None = Form(None),
  db: AsyncSession = Depends(get_db),
) -> dict:
  """Upload chart screenshot for AI structure analysis."""
  content = await file.read()
  engine = ChartAnalysisEngine()
  result = await engine.analyze_image(content, symbol, file.filename or "chart.png")

  record = ChartAnalysisRecord(
    symbol=symbol,
    file_path=file.filename,
    analysis=result,
    risk_assessment={"level": result.get("risk_assessment"), "flags": result.get("risk_flags", [])},
  )
  db.add(record)
  await db.flush()

  return {"id": str(record.id), "analysis": result}
