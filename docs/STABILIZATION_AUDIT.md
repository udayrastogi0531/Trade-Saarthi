# Stabilization audit (v4.0.1)

Internal engineering audit — **no new product features**; fixes, metrics, and documentation only.

## TODO audit (resolved in this pass)

| Item | Action |
|------|--------|
| `DataQualityReport` missing `healthy` assignment | Restored `healthy` logic before return |
| Duplicate `AI_LATENCY` metric definition | Removed duplicate; single histogram retained |
| `trading_pipeline` wrong metrics import | Restored `AI_REQUESTS`; removed unused `AI_LATENCY` |
| `research.py` broken imports | Restored `get_db` and module imports |
| `observability` missing `get_redis` | Import added |
| `portfolio` `__dict__` on dataclass | Switched to `asdict()` |
| `execution/safety` syntax / logger | Fixed `EXECUTION_FAILURES` + `get_logger` order |
| Unused `RegimeEngine` in pipeline | Removed earlier (stabilization) |
| MTF candle fetch latency | Parallel `asyncio.gather` in `MarketDataEngine.get_multi_timeframe` |

## Remaining TODOs (non-blocking)

- Add Alembic or single migration runner for greenfield DBs beyond Docker init order.
- Expand institutional tests with Postgres fixtures for scorecard + paper APIs.
- Optional: rate-limit middleware wired to `API_RATE_LIMIT_PER_MINUTE` (config exists).

## Cleanup report

- Removed no-op `time.sleep(0)` from execution simulation.
- Consolidated `research` route imports.
- Prometheus: `SCANNER_QUEUE_DEPTH` Gauge, `WS_HEARTBEATS` counter; execution failures counter used in safety path.

## Optimization suggestions

1. **DB**: Add composite indexes on `signals(account_id, created_at)`, `trades(account_id, opened_at, is_paper)` when trade volume grows.
2. **AI**: Response cache keyed by SHA-256 of context (`ai_reasoning_cache_ttl_seconds`) — implemented in `AIReasoningEngine`.
3. **Scanner**: Keep `scanner_max_concurrent` tuned to CPU/IO; monitor `trading_scanner_symbol_latency_seconds`.
4. **Celery**: Keep `process_scanner_queue` beat interval aligned with queue depth alerts.

## Module boundaries

- **Research scorecards**: `modules/research/scorecard.py` — DB aggregation only; no LLM.
- **Paper analytics**: `api/routes/paper.py` — read-only aggregates.
- **Observability**: health + queue depth + lightweight `operational_alerts` heuristics.
