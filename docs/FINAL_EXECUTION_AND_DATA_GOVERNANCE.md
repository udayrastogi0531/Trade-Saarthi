# Final execution and data governance

**Version:** 4.0.2  
**Scope:** Operational checklist — **no new execution logic** in this pass.

## Execution safety (verify in deployment)

| Control | Expected behavior |
|---------|-------------------|
| Default | Live execution **disabled**; paper / simulation default |
| Duplicate prevention | Second identical order blocked or flagged per engine rules |
| Volatility shutdown | High vol path blocks or reduces size per config |
| Staged capital | `tiny_live` / staged modes require explicit limits and monitoring |
| Manual confirmation | Human step where configured; no silent full-size live |
| Emergency shutdown | Kill switch / API stops new risk |
| Timeouts | Broker calls bounded; failures surfaced in metrics/logs |
| Reconciliation | Positions/orders reconciled on schedule or on demand |
| Slippage protection | Simulated or live slippage caps honored |

**Modes to regression-test when touching execution code:** `sandbox`, `tiny_live`, staged deployment (per desk policy).

## Data quality (verify in deployment)

| Control | Expected behavior |
|---------|-------------------|
| Stale feeds | Blocked or de-weighted; confidence reduced |
| Invalid candles | Rejected at ingest or pipeline |
| Exchange outages | Detected via health / gaps; scanner may skip safely |
| WebSocket recovery | Reconnect with backoff; no permanent stale clients in copilot WS map |
| Missing candles | Safe gap handling — no synthetic certainty |
| Market hours | Signals outside session treated per policy (reject or hold) |

## Operator rule

When **data quality** or **scanner health** is red, the desk assumes **no new risk** regardless of model output.

See [FINAL_SYSTEM_CONSISTENCY_REPORT.md](./FINAL_SYSTEM_CONSISTENCY_REPORT.md), [FINAL_RISK_STATUS.md](./FINAL_RISK_STATUS.md).
