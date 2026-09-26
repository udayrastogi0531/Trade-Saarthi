# Optimization report (final)

## Implemented (v4.0.x → 4.0.2)

1. **Parallel MTF fetches** — `MarketDataEngine.get_multi_timeframe` via `asyncio.gather`.
2. **AI reasoning cache** — Content-hash key, TTL from `AI_REASONING_CACHE_TTL_SECONDS`.
3. **AI latency histogram** — `trading_ai_latency_seconds` for LLM path monitoring.
4. **Portfolio snapshot serialization** — `dataclasses.asdict` for clean JSONB writes.
5. **WebSocket lifecycle** — Guaranteed `disconnect` in `finally` + JSON parse guard.

## Recommended (operational, not code-mandatory)

| Area | Action |
|------|--------|
| PostgreSQL | Add indexes on `signals(account_id, created_at)`, `trades(account_id, opened_at, is_paper)` when volume grows. |
| Grafana | Alert on `trading_scanner_queue_depth`, pipeline p95, `EXECUTION_FAILURES` rate. |
| Celery | Autoscale workers with queue depth; cap prefetch for long scans. |
| Next.js | Route-level `loading.tsx` for research terminal if LCP becomes an issue. |

## Bottleneck analysis (summary)

- **Dominant tail latency:** External LLM and broker I/O — address with timeouts, caching, and circuit breakers at the edge.
- **Scanner:** Bounded by `scanner_max_concurrent` and per-symbol retries — tune against provider rate limits.

See also [PERFORMANCE_BENCHMARK.md](./PERFORMANCE_BENCHMARK.md).
