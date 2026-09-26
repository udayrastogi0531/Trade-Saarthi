# Dependency map (logical)

## Runtime dependencies

```
FastAPI
├── SQLAlchemy (async) → asyncpg → PostgreSQL
├── Redis (async) → optional; memory fallback for parts of scanner cache
├── Celery → Redis broker
├── Groq / httpx → external LLM APIs
├── Prometheus client → /metrics
└── APScheduler (optional, dev scanner)
```

## Python module dependency (simplified)

- `api.routes.*` → `modules.*`, `services.*`, `db.session`
- `services.trading_pipeline` → most `modules.*` engines
- `api.ws.copilot_ws` → `modules.copilot`, `db.session`
- `workers.tasks` → `services.scanner_service`, `db.session`

## Frontend

- `frontend/web` → `NEXT_PUBLIC_API_URL` → FastAPI
- `frontend/dashboard` (Streamlit) → `API_BASE_URL`

## Rule

**Routes must not embed business rules** — keep in `modules/` for testability and reuse.
