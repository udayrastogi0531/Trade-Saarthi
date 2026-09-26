# Final go-live recommendation

**Version:** 4.0.2  
**Date:** 2026-05-19  
**Recommendation:** **Conditional GO** for **paper / research-only** production with **execution paths disabled** and **org controls** in place.

## Preconditions (must be true)

| # | Precondition |
|---|----------------|
| 1 | `TRADING_EXECUTION_ENABLED=false` (or equivalent) in all prod environments |
| 2 | `API_AUTH_ENABLED=true` with strong `X-API-Key` if API is internet-facing |
| 3 | Postgres + Redis HA appropriate to desk size; backups tested |
| 4 | Grafana alerts wired per [ALERTING_MATRIX.md](./ALERTING_MATRIX.md) |
| 5 | Kill switch / emergency procedures rehearsed ([INCIDENT_RESPONSE_GUIDE.md](./INCIDENT_RESPONSE_GUIDE.md)) |

## No-go until resolved (if applicable)

- Unauthenticated public API without edge rate limits.
- Live execution without desk-specific capital safety sign-off.

## Sign-off

| Role | Name | Date |
|------|------|------|
| Engineering | | |
| Risk / compliance | | |
| Operations | | |
