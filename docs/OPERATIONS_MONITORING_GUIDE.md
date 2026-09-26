# Operations monitoring guide

## Golden signals

| Signal | Source | Action threshold (example) |
|--------|--------|----------------------------|
| API availability | `/api/v1/health` | Non-200 > 1 min |
| Redis | `observability.health.redis` | `false` > 5 min |
| Scanner health | `observability.health.scanner_health` | `unhealthy` |
| Queue backlog | `scanner_queue_depth` | Sustained > 50 (tune to desk) |
| Pipeline latency | `histogram_quantile(0.95, trading_pipeline_latency_seconds_bucket)` | SLO breach |
| AI latency | `trading_ai_latency_seconds` | Tail > SLO |
| Execution failures | `rate(trading_execution_failures_total[5m])` | > 0 sustained in paper-off scenario |

## Dashboards

- `monitoring/grafana/dashboards/trading-overview.json`
- `monitoring/grafana/dashboards/quant-validation.json`

## Logs

- Correlate `intel_scanner_done`, `scheduled_scan_failed`, `execution_safety_blocked`, `redis_ping_failed_resetting`.

## Ownership

- **On-call** rotates weekly; links [INCIDENT_RESPONSE_GUIDE.md](./INCIDENT_RESPONSE_GUIDE.md) and [ALERTING_MATRIX.md](./ALERTING_MATRIX.md).
