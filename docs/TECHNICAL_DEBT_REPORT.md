# Technical debt report

## Confirmed debt

| Item | Severity | Notes |
|------|----------|--------|
| **In-app rate limiting** | Medium | `API_RATE_LIMIT_PER_MINUTE` in config; enforce via middleware or API gateway in production. |
| **Scanner queue max depth** | Low | No server-side cap; rely on Prometheus + ops throttling. |
| **Alembic migrations** | Low | SQL files in Docker init; no unified migration runner for non-Docker deploys. |
| **Test DB coupling** | Low | Some API tests skip without Postgres; add containerized CI job for full suite. |
| **RBAC granularity** | Low | API key auth is binary; roles defined but not fully enforced per-route. |

## Non-debt (intentional)

- **Dual dashboards** (Next.js + Streamlit): different audiences; not duplicate engines.
- **Memory fallback for Redis**: intentional resilience for dev/single-node.

## Retirement criteria

Close debt items when: production SLO defined, load test completed, and gateway-level controls deployed.
