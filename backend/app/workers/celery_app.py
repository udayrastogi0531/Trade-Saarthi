"""Celery application for distributed background tasks."""

from celery import Celery
from datetime import timedelta

from backend.app.config import get_settings

settings = get_settings()

celery_app = Celery(
  "trading_platform",
  broker=settings.celery_broker,
  backend=settings.celery_backend,
  include=["backend.app.workers.tasks"],
)

celery_app.conf.update(
  task_serializer="json",
  accept_content=["json"],
  result_serializer="json",
  timezone="Asia/Kolkata",
  enable_utc=True,
  task_track_started=True,
  task_acks_late=True,
  worker_prefetch_multiplier=1,
)

if settings.scanner_enabled:
  celery_app.conf.beat_schedule = {
    "watchlist-scan": {
      "task": "backend.app.workers.tasks.run_watchlist_scan",
      "schedule": timedelta(minutes=max(1, settings.scanner_interval_minutes)),
    },
    "scanner-queue-drain": {
      "task": "backend.app.workers.tasks.process_scanner_queue",
      "schedule": timedelta(minutes=1),
    },
    "intraday-briefing": {
      "task": "backend.app.workers.tasks.generate_intraday_briefing",
      "schedule": timedelta(hours=2),
    },
    "pre-market-briefing": {
      "task": "backend.app.workers.tasks.generate_pre_market_briefing",
      "schedule": timedelta(hours=24),
    },
  }
