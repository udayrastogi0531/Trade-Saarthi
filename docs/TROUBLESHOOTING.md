# Troubleshooting guide

## API returns 500 on research / paper / scorecards

- **Cause:** PostgreSQL unreachable or schema not migrated.
- **Check:** `GET /api/v1/health`, DB logs, Docker `postgres` health.
- **Fix:** Run compose migrations volume; ensure `DATABASE_URL` correct.

## Redis “degraded” in observability health

- **Cause:** Redis down or firewall.
- **Effect:** Scanner job queue may use in-memory fallback (single process only).
- **Fix:** Restore Redis for multi-worker Celery + durable queues.

## WebSocket disconnects immediately

- **Check:** CORS / proxy WebSocket upgrade headers.
- **Check:** Invalid JSON on first message — server sends `error` payload.

## Scanner always “unhealthy”

- **Cause:** High per-symbol latency or >50% symbol errors.
- **Fix:** Reduce `scanner_max_concurrent`, fix market data provider, increase timeouts if legitimate slowness.

## AI reasoning always fallback

- **Cause:** Missing `GROQ_API_KEY` or wrong `AI_PROVIDER`.
- **Fix:** Set keys in `.env`; verify `/docs` try-out.

## Celery tasks not running

- **Check:** `celery-worker` container up, `CELERY_BROKER_URL` / Redis.
- **Check:** Beat schedule for periodic tasks.

## Prometheus empty

- **Cause:** `PROMETHEUS_ENABLED=false` or scrape target wrong.
- **Fix:** Enable flag; point Prometheus at `api:8000/metrics`.
