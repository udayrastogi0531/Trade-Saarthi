"""Advanced watchlist scanner — retry, health, structure-aware ranking."""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.core.metrics import (
  SCANNER_ERRORS,
  SCANNER_LATENCY,
  SCANNER_RUNS,
  SCANNER_SYMBOL_LATENCY,
)
from backend.app.db.models import ScannerRun
from backend.app.modules.scanner.engine import ScannerEngine, ScannerResult, ScannerRunSummary

logger = get_logger(__name__)


class IntelligenceScanner(ScannerEngine):
  """Extended scanner with health tracking, retries, and enhanced ranking."""

  def __init__(self) -> None:
    super().__init__()
    self._settings = get_settings()

  async def scan_watchlist(
    self,
    db,
    symbols: list[str] | None = None,
    account_id: int = 1,
    max_concurrent: int | None = None,
  ) -> ScannerRunSummary:
    symbols = symbols or self._settings.watchlist
    max_concurrent = max_concurrent or self._settings.scanner_max_concurrent
    run_id = str(uuid.uuid4())
    started = datetime.utcnow()
    semaphore = asyncio.Semaphore(max_concurrent)
    errors: list[str] = []

    async def scan_one(symbol: str) -> ScannerResult:
      async with semaphore:
        return await self._scan_with_retry(db, run_id, symbol, account_id)

    logger.info("intel_scanner_start", run_id=run_id, count=len(symbols))
    t0 = time.perf_counter()
    results = await asyncio.gather(*[scan_one(s) for s in symbols], return_exceptions=True)

    parsed: list[ScannerResult] = []
    latencies: list[int] = []
    for i, r in enumerate(results):
      if isinstance(r, Exception):
        errors.append(f"{symbols[i]}: {r}")
        parsed.append(
          ScannerResult(run_id=run_id, symbol=symbols[i], approved=False, rank_score=0, error=str(r))
        )
      else:
        parsed.append(r)
        if r.duration_ms:
          latencies.append(r.duration_ms)

    parsed.sort(key=lambda x: x.rank_score, reverse=True)
    approved_count = sum(1 for r in parsed if r.approved)
    avg_lat = sum(latencies) / len(latencies) if latencies else 0
    health = "ok"
    if avg_lat > self._settings.scanner_health_degraded_latency_ms:
      health = "degraded"
    if len(errors) > len(symbols) // 2:
      health = "unhealthy"

    run_record = ScannerRun(
      run_id=uuid.UUID(run_id),
      symbols_scanned=len(symbols),
      approved_count=approved_count,
      avg_latency_ms=Decimal(str(round(avg_lat, 2))),
      health_status=health,
      errors=errors,
      started_at=started,
      completed_at=datetime.utcnow(),
    )
    db.add(run_record)

    SCANNER_RUNS.inc()
    SCANNER_LATENCY.observe(time.perf_counter() - t0)

    summary = ScannerRunSummary(
      run_id=run_id,
      total=len(symbols),
      approved=approved_count,
      results=parsed,
      completed_at=datetime.utcnow(),
    )
    logger.info("intel_scanner_done", run_id=run_id, health=health, approved=approved_count)
    return summary

  async def _scan_with_retry(
    self, db, run_id: str, symbol: str, account_id: int
  ) -> ScannerResult:
    attempts = max(1, self._settings.scanner_retry_attempts)
    last: ScannerResult | None = None
    for attempt in range(attempts):
      last = await self._scan_symbol(db, run_id, symbol, account_id)
      if not last.error:
        if last.duration_ms:
          SCANNER_SYMBOL_LATENCY.labels(symbol=symbol).observe(last.duration_ms / 1000)
        return last
      if attempt < attempts - 1:
        await asyncio.sleep(min(2**attempt, 6))
    SCANNER_ERRORS.labels(symbol=symbol).inc()
    return last or ScannerResult(
      run_id=run_id, symbol=symbol, approved=False, rank_score=0, error="scan failed"
    )

  @staticmethod
  def _compute_rank(response) -> float:
    base = ScannerEngine._compute_rank(response)
    if not base:
      return 0.0
    struct_conf = response.technical_summary.get("structure_confidence", 0) or 0
    return round(base + struct_conf * 0.15, 2)
