# Final scalability status

**Status:** **Defined and bounded** — aligned with [SCALABILITY_REPORT.md](./SCALABILITY_REPORT.md).

## Horizontal

- **API:** scale replicas behind LB; ensure DB pool sizing accounts for `workers × pool_size`.
- **Celery:** scale workers with Redis capacity.
- **WebSocket:** sticky sessions or dedicated WS tier if connection count grows.

## Vertical

- Scanner throughput bounded by `scanner_max_concurrent` and provider rate limits.

## Data path

- Single Postgres instance sufficient for research terminal workload; replicas optional for read-heavy analytics.

## Freeze statement

No further **scalability code** planned in 4.0.x without a new architecture program (frozen).
