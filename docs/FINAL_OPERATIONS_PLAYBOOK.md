# Final operations playbook

**Version:** 4.0.2  
**Single lifecycle guide** — consolidates daily through quarterly operations. Detail docs linked; do not duplicate charter text.

**Governance:** [FINAL_STABLE_RELEASE_CHARTER.md](./FINAL_STABLE_RELEASE_CHARTER.md)

---

## Daily (research + ops)

| Time | Task | Reference |
|------|------|-----------|
| Start | `GET /api/v1/health` and `/api/v1/observability/health` | [OPERATIONS_MONITORING_GUIDE.md](./OPERATIONS_MONITORING_GUIDE.md) |
| Start | Confirm `execution_enabled: false` unless authorized live window | Health / observability JSON |
| Research | Run daily research checklist | [DAILY_RESEARCH_WORKFLOW.md](./DAILY_RESEARCH_WORKFLOW.md) |
| Intraday | Monitor scanner health, queue depth, `operational_alerts` | Grafana + health API |
| Intraday | Review signal approvals/rejections; note data-quality events | Metrics / DB |
| End | Log anomalies; no new risk if data quality red | [FINAL_EXECUTION_AND_DATA_GOVERNANCE.md](./FINAL_EXECUTION_AND_DATA_GOVERNANCE.md) |

---

## Weekly

| Task | Reference |
|------|-----------|
| Complete weekly ops template | [WEEKLY_OPERATIONS_TEMPLATE.md](./WEEKLY_OPERATIONS_TEMPLATE.md) |
| Alert review (fired / silenced / false positives) | [ALERTING_MATRIX.md](./ALERTING_MATRIX.md) |
| Paper-trading summary: win rate, rejections, slippage sim | `GET /paper/summary` |
| Strategy review: scorecards, edge quality, decay | [FINAL_RESEARCH_DISCIPLINE_POLICY.md](./FINAL_RESEARCH_DISCIPLINE_POLICY.md) |
| Dependency patch triage | [FINAL_MAINTENANCE_GOVERNANCE.md](./FINAL_MAINTENANCE_GOVERNANCE.md) |

---

## Monthly

| Task | Reference |
|------|-----------|
| Apply security patches (controlled) | [FINAL_MAINTENANCE_PLAN.md](./FINAL_MAINTENANCE_PLAN.md) |
| Backup verification (restore spot test) | [DEPLOYMENT_SECURITY_GUIDE.md](./DEPLOYMENT_SECURITY_GUIDE.md) |
| Slow query / DB health review | Ops logs + Postgres |
| Re-validate alert rules sample | [FINAL_ALERT_VALIDATION.md](./FINAL_ALERT_VALIDATION.md) |
| Docker image rebuild on CVE | [FINAL_MAINTENANCE_GOVERNANCE.md](./FINAL_MAINTENANCE_GOVERNANCE.md) |

---

## Quarterly

| Task | Reference |
|------|-----------|
| Dependency audit refresh | [FINAL_DEPENDENCY_AUDIT.md](./FINAL_DEPENDENCY_AUDIT.md) |
| Risk review | [FINAL_RISK_STATUS.md](./FINAL_RISK_STATUS.md) |
| DR / incident tabletop | [INCIDENT_RESPONSE_GUIDE.md](./INCIDENT_RESPONSE_GUIDE.md) |
| Long-run paper validation review | [LONG_RUN_VALIDATION_GUIDE.md](./LONG_RUN_VALIDATION_GUIDE.md) |

---

## Backup verification

1. Confirm automated backup job success (platform-specific).  
2. Quarterly: restore to isolated instance; verify schema + sample queries.  
3. Document result in weekly ops notes when performed.

---

## Incident handling

| Severity | Action |
|----------|--------|
| SEV1 | Kill switch / emergency shutdown; preserve logs | [INCIDENT_RESPONSE_GUIDE.md](./INCIDENT_RESPONSE_GUIDE.md) |
| SEV2 | Restart failed service; rollback image if needed | [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) |
| SEV3 | Redis/scanner degradation; monitor | Health API |

---

## Paper-trading review process

1. Pull paper summary and execution-quality analytics.  
2. Compare to prior week; flag drift in rejections or fill quality.  
3. No live discussion if data quality issues open.  
4. Archive notes with validation run IDs where applicable.

---

## Strategy review process

1. Scorecards side-by-side (same metrics).  
2. Walk-forward + Monte Carlo artifacts current.  
3. Regime heatmap / regime tags reviewed.  
4. Decay alerts addressed or accepted with written rationale.  
5. Promotion blocked by default — see [FINAL_VALIDATION_STANDARD.md](./FINAL_VALIDATION_STANDARD.md).

---

## Change / release (engineering)

All code changes: [FINAL_CHANGE_CONTROL_POLICY.md](./FINAL_CHANGE_CONTROL_POLICY.md) + [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## Platform stance (reminder)

Conservative · evidence-driven · execution off by default · no profit guarantees · architecture frozen.

**This playbook completes the operational lifecycle for v4.0.2.**
