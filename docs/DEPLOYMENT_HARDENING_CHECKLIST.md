# Deployment hardening checklist

- [ ] TLS 1.2+ on all public endpoints
- [ ] `DEBUG=false`, `APP_ENV=production`
- [ ] Secrets from vault / Docker secrets, not plain `.env` in image
- [ ] `API_AUTH_ENABLED=true` with rotated `API_KEY`
- [ ] Reverse proxy rate limits (e.g. nginx `limit_req`)
- [ ] Postgres: SSL mode, restricted security groups
- [ ] Redis: `requirepass`, private network only
- [ ] Grafana: strong admin password, SSO if available
- [ ] Log aggregation (ELK / CloudWatch / Loki)
- [ ] Backup + tested restore for `trading_db`
- [ ] Health checks wired to orchestrator (K8s / compose restart policy)
- [ ] Runbook links in on-call wiki ([OPERATIONS_RUNBOOK.md](./OPERATIONS_RUNBOOK.md))
