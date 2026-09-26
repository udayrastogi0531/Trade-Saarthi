# Final refinement pass (v4.0.2)

**Scope:** Operational polish and research usability — **no** architecture expansion.

## Backend (existing modules extended)

| Area | Change |
|------|--------|
| Scorecards | `regime_summary` aggregation for regime comparison |
| Intelligence panel | `directional_volatility_context` — manual options/directional advisory only |
| Observability health | Richer payload: data-quality events, scanner latency, paper mode, governance flags |
| Observability | `GET /observability/data-quality` — recent feed events |

## Frontend

| Area | Change |
|------|--------|
| Shared components | Discipline banner, health strip, operational alerts, scorecard tables, volatility advisory |
| `/research` | Tables, regime comparison, signal quality stats, loading/errors |
| `/intelligence` | Risk flags, volatility advisory, readable setups |
| `/copilot` | WS ping/reconnect, discipline banner, error handling |
| Layout | Responsive nav, paper-first label |
| API client | `ApiError` + clearer error messages |

## Governance

All changes align with [FINAL_STABLE_RELEASE_CHARTER.md](./FINAL_STABLE_RELEASE_CHARTER.md) (P2/P3/P4).

## Not in scope

- New trading engines, indicators, or options automation
- Live execution defaults unchanged (`EXECUTION_ENABLED=false`)
