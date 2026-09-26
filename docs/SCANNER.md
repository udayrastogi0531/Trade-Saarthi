# Distributed Watchlist Scanner (v2.3)

Institutional market intelligence engine — parallel symbol scans through the full trading pipeline.

## Pipeline (per symbol)

Market Data → Technical Analysis → Strategy → Risk → AI Reasoning → Signal Filter → Market Structure → Learning calibration → Rank → Persist → Alerts

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/scanner/run` | Sync scan or `{"async_job": true}` to enqueue |
| GET | `/api/v1/scanner/health` | Recent run health (`ok` / `degraded` / `unhealthy`) |
| GET | `/api/v1/scanner/feed` | Ranked scanner log feed |
| GET/PUT | `/api/v1/scanner/watchlist` | DB-backed watchlists |
| GET | `/api/v1/scanner/jobs/{job_id}` | Async job status |

## Workers

- **Celery** `run_watchlist_scan` — scheduled full watchlist scan
- **Celery** `process_scanner_queue` — drains Redis (or in-memory) job queue every minute
- **APScheduler** fallback when Celery is not running

## Alerts

- Telegram digest (top 3 approved setups)
- Voice alert for best setup (if enabled)
- WebSocket broadcast on scan complete

## Configuration

See `.env.example`: `SCANNER_*`, `WATCHLIST_SYMBOLS`, `SCANNER_MAX_CONCURRENT`, `SCANNER_RETRY_ATTEMPTS`.

## Disclaimer

Scanner output is probabilistic analysis for decision support — not financial advice and not a profit guarantee.
