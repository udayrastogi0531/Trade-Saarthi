# Performance benchmark notes (v4.0.1)

## What was optimized

1. **Multi-timeframe market data**: `get_multi_timeframe` now fetches intervals concurrently via `asyncio.gather` (reduces wall-clock vs sequential awaits).
2. **AI trade reasoning**: Optional Redis/memory JSON cache on identical technical context (`AI_REASONING_CACHE_TTL_SECONDS`).
3. **Metrics**: `AI_LATENCY` histogram records end-to-end LLM path latency (cache hits skip external call and are not double-counted as remote latency in the same way — first-hit dominates).

## How to benchmark locally

```powershell
cd "d:\AI Trading"
$env:PYTHONPATH = "."
# Micro-benchmark MTF fetch (requires running API or in-process script)
python -c "
import asyncio, time
from backend.app.modules.market_data.engine import MarketDataEngine
from backend.app.schemas.market import MultiTimeframeRequest

async def main():
  m = MarketDataEngine()
  req = MultiTimeframeRequest(symbol='RELIANCE', exchange='NSE', intervals=['5m','15m','1h','4h','1d'])
  t0 = time.perf_counter()
  d = await m.get_multi_timeframe(req)
  print('intervals', len(d), 'elapsed_s', round(time.perf_counter()-t0, 3))

asyncio.run(main())
"
```

## Bottleneck analysis (typical)

| Layer | Risk | Mitigation |
|-------|------|------------|
| External LLM | Tail latency | Cache + timeout in httpx/Groq clients |
| DB | N+1 in dashboards | Use bounded `limit` + aggregates (paper summary) |
| Redis | Hot keys | TTL on OHLCV cache; scanner job TTL already 24h |
| WebSocket | Idle disconnects | Client `ping` / server `pong`; `WS_HEARTBEATS` metric |

See [SCALABILITY_REPORT.md](./SCALABILITY_REPORT.md) for horizontal/vertical scaling notes.
 + Grafana dashboard export after load test; attach to release artifacts. No automated benchmark committed to CI to avoid flaky network dependencies.
