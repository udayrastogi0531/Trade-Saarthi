# Final observability status

**Version:** 4.0.2  
**Validation:** Code and config review (not live cluster soak).

## Metrics (Prometheus)

| Metric | Purpose | Status |
|--------|---------|--------|
| `trading_signals_approved_total` / `rejected_total` | Signal discipline | **Stable** |
| `trading_scanner_runs_total` | Scanner activity | **Stable** |
| `trading_ai_latency_seconds` | AI path latency | **Stable** |
| `trading_pipeline_latency_seconds` | End-to-end pipeline | **Stable** |
| `trading_scanner_queue_depth` | Queue pressure (set on `/observability/health`) | **Stable** |
| `trading_ws_heartbeat_total` | Copilot WS ping/pong | **Stable** |
| `trading_copilot_ws_connections_total` | **Cumulative** connection counter (not active gauge) | **Documented** |
| `trading_execution_failures_total` | Execution failures | **Stable** |
| `trading_data_quality_events_total` | Feed quality | **Stable** |
| `trading_api_requests_total` | API traffic | **Stable** |

**Scrape:** `monitoring/prometheus.yml` → `api:8000/metrics`.

## Health API

`GET /api/v1/observability/health` exposes:

- `redis`, `scanner_health`, `scanner_queue_depth`, `operational_alerts`, `execution_enabled`, `conservative_mode`, `data_quality_issues`

Use for synthetic checks and alert inputs.

## Grafana

| Dashboard | Path |
|-----------|------|
| Trading overview | `monitoring/grafana/dashboards/trading-overview.json` |
| Quant validation | `monitoring/grafana/dashboards/quant-validation.json` |

**Deploy-time:** import dashboards and bind to Prometheus datasource (`monitoring/grafana/provisioning/datasources/datasource.yml`).

## Gaps

- Alert **routing** (Pager/Slack) is environment-specific — see [FINAL_ALERT_VALIDATION.md](./FINAL_ALERT_VALIDATION.md).
- Active WS count not exposed as gauge; use logs `ws_connected` / `ws_disconnected` for session debugging.

## Verdict

**OBSERVABILITY ADEQUATE** for institutional paper/research operations when Prometheus + Grafana are deployed and alerts validated per matrix.
