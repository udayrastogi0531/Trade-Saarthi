# Final alert validation

**Purpose:** Checklist to validate alerts in **your** deployment (repo supplies metrics + health JSON; not hosted alertmanager rules).

## Pre-requisites

- [ ] Prometheus scraping `trading-api` (`/metrics`)
- [ ] Grafana dashboards imported
- [ ] Contact channels configured (see [ALERTING_MATRIX.md](./ALERTING_MATRIX.md))

## Validation matrix

| # | Alert | How to validate | Pass criteria |
|---|-------|-----------------|---------------|
| A1 | API down | Stop API container briefly | Alert fires within evaluation window; clears on recovery |
| A2 | Redis unhealthy | Block Redis or wrong `REDIS_URL` | `/observability/health` shows `redis: false`; alert fires |
| A3 | Scanner unhealthy | Force degraded scan or inspect `scanner_health` | `operational_alerts` contains `scanner:degraded` or `unhealthy` |
| A4 | Queue backlog | Enqueue >50 scanner jobs (test env) | `scanner_queue_backlog` in health alerts |
| A5 | Execution failures | Simulate failed paper order path | `trading_execution_failures_total` increases; optional alert |
| A6 | AI latency | Load-test copilot/analyze path | p95 from `trading_ai_latency_seconds` within SLO |
| A7 | Signal rejection spike | Compare `rate(trading_signals_rejected_total[5m])` baseline | Anomaly rule fires only on configured threshold |
| A8 | WS heartbeats | Send copilot `ping` messages | `trading_ws_heartbeat_total` increases |

## Health endpoint drill

```http
GET /api/v1/observability/health
```

Confirm fields: `status`, `redis`, `scanner_health`, `scanner_queue_depth`, `operational_alerts`, `disclaimer`.

## Sign-off

| Role | Validated (Y/N) | Date |
|------|-----------------|------|
| Engineering | | |
| Operations | | |

After sign-off, record dashboard URLs and alert rule IDs in your internal ops wiki (not committed secrets).
