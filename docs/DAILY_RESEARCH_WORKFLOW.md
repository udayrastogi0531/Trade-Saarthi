# Daily research workflow

**Audience:** Quant researcher / desk analyst using the platform as a **terminal**, not an autopilot.

## Morning (15–30 min)

1. Open **Next.js** `/research` (or API directly).
2. `GET /api/v1/observability/health` — confirm no critical `operational_alerts`.
3. `GET /api/v1/research/scorecards` — scan top/bottom setups; note sample sizes.
4. `GET /api/v1/paper/summary?days=7` — win rate, rejection rate; **no action** implied by numbers alone.

## Midday

5. If scanning: `GET /api/v1/scanner/health` — latency and error mix.
6. Optional: `POST /api/v1/validation/walk-forward` on watchlist symbol **after** data refresh (do not batch blindly).

## Close

7. Export or screenshot Grafana panels if material regime shift suspected.
8. Log qualitative notes externally (compliance / journal); platform stores quantitative artifacts only.

## Rules

- **Evidence first:** LLM summaries (`use_ai_summary`) are secondary to DB scorecards and validation runs.
- **No guarantee:** Any “edge” is statistical until validated out-of-sample and in paper.

See [VALIDATION_METHODOLOGY.md](./VALIDATION_METHODOLOGY.md).
