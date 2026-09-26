# Final performance report

**Version:** 4.0.2  
**Scope:** Finalization — no new performance features; **status** of existing optimizations.

## Implemented optimizations (locked)

| Area | Mechanism |
|------|-----------|
| MTF market data | `asyncio.gather` per interval |
| AI trade reasoning | Content-hash cache + latency histogram |
| Scanner | Semaphore concurrency + per-symbol retry cap |
| Portfolio persist | `dataclasses.asdict` for JSONB |

## Profiling

- Manual procedure: [PERFORMANCE_BENCHMARK.md](./PERFORMANCE_BENCHMARK.md)
- **Slow query detection:** enable `echo=True` via `DEBUG` only in non-prod; use Postgres `pg_stat_statements` in production.

## DB index review (recommendation)

When trade/signal volume grows, add:

- `(account_id, created_at)` on `signals`
- `(account_id, opened_at, is_paper)` on `trades`

**Not applied in code** — DBA-owned migration when metrics justify.

## WebSocket stability

- Heartbeat metric: `trading_ws_heartbeat_total`
- Lifecycle cleanup in `finally` (consistency report).

## Queue pressure

- `trading_scanner_queue_depth` Gauge updated from `/observability/health` Redis `LLEN`
- **Starvation:** mitigated operationally by worker count + beat interval; no code starvation loop identified.

## Conclusion

Performance posture is **adequate for desk-scale** quantitative operations. Exchange-scale HFT is **explicitly out of scope**.
