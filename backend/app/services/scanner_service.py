"""Distributed market intelligence scanner — orchestration, alerts, queue."""

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.session import AsyncSession
from backend.app.modules.scanner.intelligence import IntelligenceScanner
from backend.app.modules.scanner.queue import ScannerJobQueue
from backend.app.modules.scanner.watchlist_service import WatchlistService
from backend.app.modules.scanner.engine import ScannerRunSummary
from backend.app.modules.telegram.engine import TelegramAlertEngine
from backend.app.modules.voice.alerts import VoiceAlertService

logger = get_logger(__name__)


class ScannerService:
  """
  Institutional scanner orchestrator.

  Flow per symbol:
  Market Data → TA → Strategy → Risk → AI → Signal Filter → Structure → Learning
  → rank → persist → optional alerts (Telegram / voice / WebSocket)
  """

  def __init__(self) -> None:
    self._scanner = IntelligenceScanner()
    self._watchlists = WatchlistService()
    self._queue = ScannerJobQueue()
    self._settings = get_settings()

  async def run_scan(
    self,
    db: AsyncSession,
    symbols: list[str] | None = None,
    account_id: int = 1,
    watchlist_name: str = "default",
    dispatch_alerts: bool = True,
  ) -> ScannerRunSummary:
    if symbols is None:
      symbols = await self._watchlists.get_active_symbols(db, watchlist_name)

    summary = await self._scanner.scan_watchlist(db, symbols, account_id)

    if dispatch_alerts:
      await self._dispatch_alerts(db, summary, account_id)

    await self._broadcast_scan_complete(summary)
    return summary

  async def enqueue_scan(
    self,
    symbols: list[str] | None,
    account_id: int = 1,
    watchlist_name: str = "default",
  ) -> str:
    return await self._queue.enqueue(symbols, account_id, watchlist_name)

  async def process_queued_job(self, db: AsyncSession, job: dict) -> dict:
    job_id = job["job_id"]
    await self._queue.update_status(job_id, "running")
    try:
      summary = await self.run_scan(
        db,
        job.get("symbols"),
        job.get("account_id", 1),
        job.get("watchlist_name", "default"),
      )
      result = {
        "run_id": summary.run_id,
        "total": summary.total,
        "approved": summary.approved,
        "health": await self._health_from_run(db, summary.run_id),
      }
      await self._queue.update_status(job_id, "completed", result)
      return result
    except Exception as exc:
      await self._queue.update_status(job_id, "failed", {"error": str(exc)})
      raise

  async def _dispatch_alerts(
    self, db: AsyncSession, summary: ScannerRunSummary, account_id: int
  ) -> None:
    approved = [r for r in summary.results if r.approved and r.response and r.response.setup]
    if not approved:
      return

    top = approved[:3]
    if self._settings.telegram_enabled:
      lines = [
        f"📡 *Scanner* — {summary.approved}/{summary.total} approved\n",
      ]
      for r in top:
        s = r.response.setup
        lines.append(
          f"• *{r.symbol}* {s.direction} | RR 1:{s.risk_reward} | "
          f"Conf {s.confidence}% | Rank {r.rank_score}"
        )
      lines.append("\n_Probabilistic analysis — not financial advice._")
      tg = TelegramAlertEngine()
      await tg.send_message("\n".join(lines))

    if self._settings.voice_alerts_enabled and top:
      best = top[0]
      setup = best.response.setup
      vas = VoiceAlertService()
      msg = vas.format_signal_alert(
        setup.symbol, setup.direction, setup.confidence, "hinglish", enhanced=True
      )
      await vas.create_alert(db, "scanner_top", msg, "hinglish", account_id, priority="high")

  async def _broadcast_scan_complete(self, summary: ScannerRunSummary) -> None:
    try:
      from backend.app.api.ws.copilot_ws import broadcast_alert

      await broadcast_alert(
        f"Scanner complete: {summary.approved}/{summary.total} setups approved.",
        "scanner",
      )
    except Exception:
      pass

  async def _health_from_run(self, db, run_id: str) -> str:
    from sqlalchemy import select
    from backend.app.db.models import ScannerRun
    import uuid

    result = await db.execute(
      select(ScannerRun).where(ScannerRun.run_id == uuid.UUID(run_id))
    )
    run = result.scalar_one_or_none()
    return run.health_status if run else "unknown"
