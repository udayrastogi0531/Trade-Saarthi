# Weekly operations template

**Owner:** _________________  
**Week of:** _________________

## 1. Health (15 min)

- [ ] `GET /api/v1/health` — OK
- [ ] `GET /api/v1/observability/health` — note `status`, `operational_alerts`, `scanner_queue_depth`
- [ ] Grafana: pipeline p95, scanner runs, AI latency

## 2. Data & queues (15 min)

- [ ] Postgres disk usage & connection count
- [ ] Redis memory / evictions
- [ ] Celery queue depth (broker inspection)

## 3. Security & config (10 min)

- [ ] No unexpected env drift (`EXECUTION_ENABLED` still false for conservative ops)
- [ ] API keys / tokens rotation due? (if policy)

## 4. Research / validation (20 min)

- [ ] Review `GET /api/v1/research/scorecards` — any `edge_quality: weak` with `trade_count ≥ 10`?
- [ ] Optional: run walk-forward on 1 benchmark symbol (non-prod or scheduled job)

## 5. Incidents & follow-ups

| Incident | Root cause | Action item | Owner |
|----------|------------|-------------|-------|
| | | | |

## Sign-off

Ops: _________________  Date: _________
