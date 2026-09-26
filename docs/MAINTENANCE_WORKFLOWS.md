# Maintenance workflows

## Weekly

- Review Grafana: pipeline latency, scanner health, queue depth, AI latency.
- Skim `operational_alerts` from `/api/v1/observability/health` in monitoring.
- Check disk usage on Postgres volume.

## Monthly

- Dependency updates (security patches only unless planned).
- Review `walk_forward_runs` / `monte_carlo_runs` for strategy under review.
- Rotate API keys if auth enabled.

## Quarterly

- Re-read [FINAL_RISK_ASSESSMENT.md](./FINAL_RISK_ASSESSMENT.md) and [CRITICAL_RISK_REPORT.md](./CRITICAL_RISK_REPORT.md).
- Disaster recovery drill: restore Postgres backup to staging.

## Change management

- **No** casual changes to default risk thresholds — require review + version note in changelog.
