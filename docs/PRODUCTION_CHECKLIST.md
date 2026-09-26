# Production readiness checklist

- [ ] `APP_ENV=production`, `DEBUG=false`
- [ ] `SECRET_KEY` rotated; no secrets in repo
- [ ] `DATABASE_URL` / `REDIS_URL` point to managed HA endpoints
- [ ] `EXECUTION_ENABLED=false` until capital safety staged rollout complete
- [ ] `API_AUTH_ENABLED=true` and `API_KEY` set for external API access
- [ ] CORS origins restricted to real frontends (not `*` in prod)
- [ ] Grafana + Prometheus retention and alerts wired (PagerDuty/Slack)
- [ ] Postgres backups scheduled
- [ ] `GET /api/v1/observability/health` monitored; alert on `degraded` + non-empty `operational_alerts`
- [ ] Walk-forward + Monte Carlo run on representative symbols before widening watchlist
- [ ] Legal disclaimer surfaced on all client surfaces

## Sign-off

| Role | Name | Date |
|------|------|------|
| Engineering | | |
| Risk | | |
