"""Real-time watchlist scanner — parallel async market intelligence."""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models import ScannerLog
from backend.app.schemas.trade import SignalRequest, SignalResponse
from backend.app.services.trading_pipeline import TradingPipeline

logger = get_logger(__name__)


@dataclass
class ScannerResult:
  run_id: str
  symbol: str
  approved: bool
  rank_score: float
  response: SignalResponse | None = None
  duration_ms: int = 0
  error: str | None = None


@dataclass
class ScannerRunSummary:
  run_id: str
  total: int
  approved: int
  results: list[ScannerResult] = field(default_factory=list)
  started_at: datetime = field(default_factory=datetime.utcnow)
  completed_at: datetime | None = None


class ScannerEngine:
  """Scan watchlist with parallel async workers and signal ranking."""

  def __init__(self) -> None:
    self._settings = get_settings()
    self._pipeline = TradingPipeline()

  async def scan_watchlist(
    self,
    db: AsyncSession,
    symbols: list[str] | None = None,
    account_id: int = 1,
    max_concurrent: int | None = None,
  ) -> ScannerRunSummary:
    symbols = symbols or self._settings.watchlist
    max_concurrent = max_concurrent or self._settings.scanner_max_concurrent
    run_id = str(uuid.uuid4())
    semaphore = asyncio.Semaphore(max_concurrent)

    async def scan_one(symbol: str) -> ScannerResult:
      async with semaphore:
        return await self._scan_symbol(db, run_id, symbol, account_id)

    logger.info("scanner_run_start", run_id=run_id, symbols=len(symbols))
    results = await asyncio.gather(
      *[scan_one(s) for s in symbols],
      return_exceptions=True,
    )

    parsed: list[ScannerResult] = []
    for i, r in enumerate(results):
      if isinstance(r, Exception):
        parsed.append(
          ScannerResult(
            run_id=run_id,
            symbol=symbols[i],
            approved=False,
            rank_score=0,
            error=str(r),
          )
        )
      else:
        parsed.append(r)

    parsed.sort(key=lambda x: x.rank_score, reverse=True)
    approved_count = sum(1 for r in parsed if r.approved)

    summary = ScannerRunSummary(
      run_id=run_id,
      total=len(symbols),
      approved=approved_count,
      results=parsed,
      completed_at=datetime.utcnow(),
    )
    logger.info(
      "scanner_run_complete",
      run_id=run_id,
      approved=approved_count,
      total=len(symbols),
    )
    return summary

  async def _scan_symbol(
    self,
    db: AsyncSession,
    run_id: str,
    symbol: str,
    account_id: int,
  ) -> ScannerResult:
    start = time.perf_counter()
    try:
      response = await self._pipeline.generate_signal(
        db,
        SignalRequest(symbol=symbol, account_id=account_id, include_ai_reasoning=True),
        persist_scanner=True,
        run_id=run_id,
      )
      rank = self._compute_rank(response)
      duration_ms = int((time.perf_counter() - start) * 1000)

      log = ScannerLog(
        run_id=uuid.UUID(run_id),
        symbol=symbol,
        approved=response.approved,
        quality_score=response.technical_summary.get("quality_score"),
        mtf_alignment_score=response.technical_summary.get("mtf_alignment_score"),
        regime=response.technical_summary.get("market_regime"),
        rank_score=rank,
        structure_score=response.technical_summary.get("structure_confidence"),
        rejection_reasons=response.rejection_reasons,
        duration_ms=duration_ms,
      )
      db.add(log)
      await db.flush()

      return ScannerResult(
        run_id=run_id,
        symbol=symbol,
        approved=response.approved,
        rank_score=rank,
        response=response,
        duration_ms=duration_ms,
      )
    except Exception as exc:
      logger.error("scanner_symbol_failed", symbol=symbol, error=str(exc))
      return ScannerResult(
        run_id=run_id,
        symbol=symbol,
        approved=False,
        rank_score=0,
        error=str(exc),
        duration_ms=int((time.perf_counter() - start) * 1000),
      )

  @staticmethod
  def _compute_rank(response: SignalResponse) -> float:
    if not response.approved or not response.setup:
      return 0.0
    base = response.setup.confidence
    qs = response.technical_summary.get("quality_score", 0) or 0
    mtf = (response.technical_summary.get("mtf_alignment_score", 0) or 0) * 100
    ai = response.ai_reasoning.confidence_score if response.ai_reasoning else 0
    struct = response.technical_summary.get("structure_confidence", 0) or 0
    return round(base * 0.35 + qs * 0.25 + mtf * 0.15 + ai * 0.1 + struct * 0.15, 2)
