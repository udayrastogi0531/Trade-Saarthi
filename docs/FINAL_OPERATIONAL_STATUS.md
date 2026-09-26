# Final operational status

**Build:** 4.0.2  
**Mode:** Conservative / research-first  

## Component status (expected steady state)

| Component | Expected state |
|-----------|----------------|
| API | Running, `/health` = ok |
| Postgres | Primary store reachable |
| Redis | Up for Celery + cache (or degraded with memory fallback for scanner metadata) |
| Celery | Workers consuming tasks |
| Prometheus | Scraping `/metrics` |
| Grafana | Dashboards loaded from provisioning |

## Key endpoints for ops

- `GET /api/v1/health`
- `GET /api/v1/observability/health` — includes `operational_alerts`, `scanner_queue_depth`
- `GET /metrics`

## Change freeze recommendation

After 4.0.2: **feature freeze** except security patches, dependency CVEs, and validated bugfixes — maintain **stability over novelty**.
