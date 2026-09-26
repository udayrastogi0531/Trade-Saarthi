# FINAL AUTOMATION WORKFLOW (v4.0.2)

## Scheduler
- Celery beat runs scheduled watchlist scans and queue draining.
- APScheduler fallback runs in development mode.

## Celery schedules
Defined in [backend/app/workers/celery_app.py](../backend/app/workers/celery_app.py):
- watchlist-scan
- scanner-queue-drain
- intraday-briefing
- pre-market-briefing

## Scanner flow
1. Scheduled scan runs ScannerService.run_scan()
2. Alerts dispatched (Telegram/Voice/WebSocket) when enabled
3. Results persisted and available in /scanner/feed

## Queue flow
1. /scanner/run with async_job true enqueues a job
2. process_scanner_queue drains Redis queue and executes jobs

## Operational checks
- /api/v1/health/config
- /api/v1/scanner/health
- /api/v1/observability/health
