# v4.0 — Quantitative Validation & Survivability

Institutional upgrade focused on statistical validation, capital preservation, and execution discipline.

## New modules

| Section | Module | API prefix |
|---------|--------|------------|
| Walk-forward validation | `modules/validation/walk_forward.py` | `POST /validation/walk-forward` |
| Monte Carlo risk | `modules/validation/monte_carlo.py` | `POST /validation/monte-carlo` |
| Portfolio intelligence | `modules/portfolio/engine.py` | `GET /portfolio/analysis` |
| Strategy research | `modules/research/engine.py` | `POST /research/analyze` |
| Execution simulation | `modules/execution/simulation.py` | `POST /execution/simulate` |
| Regime research | `modules/regime/research.py` | `GET /research/regime-heatmap` |
| Institutional analytics | `modules/analytics/institutional.py` | `GET /research/institutional-metrics` |
| Data quality | `modules/data_quality/engine.py` | (pipeline-integrated) |
| Capital safety | `modules/safety/capital.py` | `GET /observability/capital-safety` |
| Security | `modules/security/` | `X-API-Key` when `API_AUTH_ENABLED=true` |

## Database

Apply migration: `backend/app/db/migrations/005_quant_validation.sql` (auto-mounted in Docker).

## Configuration (.env)

```
CONSERVATIVE_MODE=true
MIN_SIGNAL_QUALITY_SCORE=72
SIGNAL_CONFIDENCE_THRESHOLD=78
DATA_QUALITY_ENABLED=true
BLOCK_SIGNALS_ON_BAD_DATA=true
CAPITAL_SAFETY_ENABLED=true
DEFAULT_DEPLOYMENT_STAGE=sandbox
API_AUTH_ENABLED=false
```

## Deployment

```bash
docker compose up -d --build
```

- API docs: http://localhost:8000/docs
- Research UI: http://localhost:3000/research
- Grafana: http://localhost:3001 (dashboard: Quant Validation)

## Principles

- No profit guarantees
- Signals blocked on unreliable data
- Live execution requires capital safety stage + manual confirm
- Research outputs cite database evidence only
