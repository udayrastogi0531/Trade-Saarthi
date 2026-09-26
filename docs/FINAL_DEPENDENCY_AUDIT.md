# Final dependency audit

## Runtime (required)

| Dependency | Role | Notes |
|------------|------|--------|
| PostgreSQL | System of record | asyncpg driver |
| Redis | Celery broker, cache, scanner queue | Reconnect hardened in 4.0.2 |
| Python 3.11+ | Runtime | Match Dockerfile |

## Runtime (optional / degraded)

| Dependency | Degraded behavior |
|--------------|-------------------|
| Redis down | Celery impaired; API cache + scanner job metadata use memory fallback where implemented |
| Groq / DeepSeek | AI reasoning falls back to rule-based response |

## Application packages (high level)

- **fastapi**, **uvicorn** — HTTP
- **sqlalchemy** + **asyncpg** — ORM / DB
- **redis** — async client
- **celery** — workers
- **prometheus_client** — metrics
- **pandas**, **numpy** — analytics / TA
- **pydantic-settings** — configuration

## Supply chain hygiene

- Pin major versions in `requirements.txt` / Docker build.
- Run `pip audit` or equivalent in CI monthly.

## Circular dependency risk

**Low:** `api` → `modules` → `db`; `ws` → `copilot` → `modules`; avoid routes importing each other.

## Conclusion

Dependency graph is **appropriate** for scope. **No new runtime services** recommended without formal architecture review (frozen).
