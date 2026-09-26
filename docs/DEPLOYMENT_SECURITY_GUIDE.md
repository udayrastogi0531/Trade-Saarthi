# Deployment security guide

## Image & build

- Build from locked Dockerfile; scan image in CI (Trivy, etc.).
- Non-root user in container where feasible.

## Runtime

- Read-only root filesystem where compatible.
- Drop Linux capabilities not required.
- Network policies: API → DB/Redis only; no public DB.

## Secrets injection

- Docker Compose: use `secrets` or orchestrator secret refs, not plain env files on disk in prod.

## Observability

- Grafana/Prometheus auth; no public unauthenticated `/metrics` without IP restriction.

## Backups

- Encrypted backups; restore tested quarterly.

## Compliance hooks

- Retention for `audit_logs` per legal policy.
- Data residency: choose region for Postgres host.
