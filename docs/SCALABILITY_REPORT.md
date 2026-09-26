# Scalability report (final)

## Horizontal scaling

| Tier | Scaling lever | Limit |
|------|---------------|-------|
| API | Multiple uvicorn/gunicorn workers | Shared DB pool; use `pool_size` per worker math |
| Celery | More workers | Broker Redis throughput |
| Scanner | Queue + workers | Provider rate limits; tune `scanner_max_concurrent` |

## Vertical scaling

- **CPU:** TA + pandas per symbol; primary lever is concurrency cap.
- **Memory:** Large watchlists × OHLCV rows — reduce `limit` on candles if OOM.

## Stateless vs stateful

- **Stateless:** API workers behind LB if session stickiness not required for WS.
- **Stateful:** WebSocket connections — sticky sessions or dedicated WS service.

## Database

- Read replicas optional for analytics routes if read load dominates.
- Partition `signals` / `scanner_logs` by time if retention grows (future).

## Conclusion

Suitable for **team / desk** scale out of the box; **exchange-scale** would require provider-specific sharding and colocation — **explicitly out of scope** for this codebase.
