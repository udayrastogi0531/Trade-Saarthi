# Final operational audit

## Run state

| Capability | Operational expectation |
|------------|-------------------------|
| API | Process up; `/api/v1/health` OK |
| Postgres | Migrations applied; connections within pool limits |
| Redis | Reachable for Celery; API tolerates outage with reconnect + memory fallback for cache paths |
| Celery | Workers running; beat for scanner/briefings/queue |
| Prometheus | Scrapes `/metrics` |
| Grafana | Dashboards loaded |

## Procedures

- [OPERATIONS_RUNBOOK.md](./OPERATIONS_RUNBOOK.md)
- [OPERATIONS_MONITORING_GUIDE.md](./OPERATIONS_MONITORING_GUIDE.md)
- [INCIDENT_RESPONSE_GUIDE.md](./INCIDENT_RESPONSE_GUIDE.md)

## Cadence

- [WEEKLY_OPERATIONS_TEMPLATE.md](./WEEKLY_OPERATIONS_TEMPLATE.md)
- [DAILY_RESEARCH_WORKFLOW.md](./DAILY_RESEARCH_WORKFLOW.md)

## Change control

- **Architecture freeze** post 4.0.2: bugfixes, security patches, dependency CVEs only unless a formal change program is opened.

## Gaps (explicit)

- In-app **rate limiting** not wired — use **API gateway** in production ([FINAL_SECURITY_POSTURE.md](./FINAL_SECURITY_POSTURE.md)).
