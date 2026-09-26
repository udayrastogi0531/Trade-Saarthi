# Critical risk report

*Institutional risk register — not legal advice.*

## Critical (must mitigate before live capital)

| ID | Risk | Mitigation in product |
|----|------|------------------------|
| C1 | **Live execution loss** | `EXECUTION_ENABLED=false`, `PAPER_TRADING=true` by default; capital safety staging; manual confirm. |
| C2 | **Bad market data → bad trades** | Data quality gate in pipeline; optional NSE hours flag; block when penalty threshold exceeded. |
| C3 | **Model / LLM hallucination** | JSON-schema constrained trade AI; copilot grounded on context; disclaimers everywhere. |

## High

| ID | Risk | Mitigation |
|----|------|------------|
| H1 | **Redis single point** | Graceful degradation; restore for multi-worker Celery. |
| H2 | **Broker / API outage** | Retries on execution engine; execution logs; no silent success. |
| H3 | **Over-concentration** | Portfolio intelligence blocks; sector limits in advanced risk. |

## Medium

| M1 | WebSocket abuse / DoS | CORS + reverse proxy rate limits in production (not fully in-app). |
| M2 | DB pool exhaustion | `pool_size` / `max_overflow` set; monitor connections. |
| M3 | Stale AI cache | TTL on AI reasoning cache; context hash invalidates on data change. |

## Low

| L1 | Timezone naive summaries | Paper summaries use UTC; align reporting to exchange TZ in ops. |

**Review cadence:** Quarterly or after any major dependency upgrade.
