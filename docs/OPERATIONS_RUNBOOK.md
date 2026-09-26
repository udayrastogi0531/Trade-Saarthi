# Operations runbook

## Services (Docker Compose)

| Service | Port | Purpose |
|---------|------|---------|
| api | 8000 | FastAPI |
| postgres | 5432 | Primary store |
| redis | 6379 | Cache + Celery broker |
| celery-worker | — | Background tasks |
| web | 3000 | Next.js (if enabled) |
| grafana | 3001 | Dashboards |
| prometheus | 9090 | Metrics scrape |

## Health checks

- `GET /api/v1/health` — API liveness
- `GET /api/v1/observability/health` — Redis, scanner, data-quality hints, queue depth, `operational_alerts`
- `GET /metrics` — Prometheus (when enabled)

## Capital safety

- Live execution remains **disabled** by default (`EXECUTION_ENABLED=false`, `PAPER_TRADING=true`).
- `GET /api/v1/observability/capital-safety?account_id=1` — deployment stage and blockers
- `POST /api/v1/observability/capital-safety/emergency-shutdown` — halt progression (body: `account_id`, `reason`)

## Incident recovery

1. **Kill switch**: Use existing risk APIs / DB `risk_state.kill_switch_active` per operational procedure.
2. **Bad data storm**: Toggle `BLOCK_SIGNALS_ON_BAD_DATA=true` (already default); fix upstream provider.
3. **Redis down**: API degrades to in-memory cache for scanner jobs (dev/single-node); restore Redis for multi-worker.
4. **Broker outage**: Execution engine retries with `reraise=True` after attempts; orders not marked submitted until broker ack (extend in broker adapter as needed).

## Logs

Structured logs via `structlog`/project logger — search by `event` keys: `intel_scanner_done`, `execution_safety_blocked`, `ai_reasoning_failed`.
