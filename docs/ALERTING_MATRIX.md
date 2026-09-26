# Alerting matrix

| Alert | Condition (Prometheus / health) | Severity | Channel |
|-------|----------------------------------|----------|---------|
| API down | `up{job="trading-api"} == 0` | SEV2 | Pager |
| Postgres connections | Custom exporter / DB alert | SEV2 | Pager |
| Redis down | health `redis: false` 5m | SEV3 | Slack |
| Scanner unhealthy | `scanner_health == unhealthy` | SEV3 | Slack |
| Queue backlog | `scanner_queue_depth > 50` 15m | SEV3 | Slack |
| High rejections | Sudden spike `trading_signals_rejected_total` | SEV3 | Email |
| AI latency SLO | p95 `trading_ai_latency_seconds` | SEV3 | Slack |
| Execution failures | `trading_execution_failures_total` rate | SEV2 if live | Pager |

**Note:** Wire channels in Grafana Alerting or external system; repo provides metrics only.

## Silence policy

- Planned maintenance: silence with ticket ID + end time.
