# Operation mode (v4.0.2)

**Status:** Platform **complete** · architecture **frozen**  
**Mode:** Operation + validation + research — **not** feature development

**Governance:** [FINAL_STABLE_RELEASE_CHARTER.md](./FINAL_STABLE_RELEASE_CHARTER.md) · [FINAL_CHANGE_CONTROL_POLICY.md](./FINAL_CHANGE_CONTROL_POLICY.md)

---

## Role of the operator

The mission is no longer “build more features.” It is:

- Operate responsibly
- Validate continuously
- Research carefully
- Preserve stability
- Protect capital
- Improve discipline
- Maintain survivability

The platform behaves as a **quantitative research terminal**, **conservative institutional intelligence system**, and **risk-first execution assistant**.

---

## Paper trading rule (non-negotiable)

```env
EXECUTION_ENABLED=false
PAPER_TRADING=true
```

The platform **scans, analyzes, validates, simulates, learns, scores, and reports** — it does **not** aggressively live-trade by default.

Verify daily via `/api/v1/observability/health` → `execution_enabled: false`.

---

## Daily operation workflow

Every trading day:

### 1. Start & verify infrastructure

1. Start platform services (API, Postgres, Redis, Celery, monitoring stack).
2. Verify observability dashboards (Grafana).
3. Verify scanner health — `GET /api/v1/scanner/health` and observability health.
4. Verify Redis/Celery — health API `redis: true`; queue depth acceptable.
5. Verify data-quality gates — no open critical feed issues.
6. Verify WebSocket stability — copilot connects; heartbeats increment if used.
7. Confirm paper mode — `execution_enabled: false`.

### 2. Open workspaces

| Surface | Path |
|---------|------|
| Research terminal | Next.js `/research` |
| AI copilot | `/copilot` |
| Intelligence | `/intelligence` |
| Monitoring | Grafana dashboards (`monitoring/grafana/dashboards/`) |

### 3. Monitor through the session

- Signal quality (approvals vs rejections)
- False positives / rejection reasons
- Regime detection
- Scanner health and latency
- AI confidence (not as sole decision input)
- `operational_alerts` on observability health
- Scanner queue depth
- Execution safety and capital-safety state

Detail checklist: [DAILY_RESEARCH_WORKFLOW.md](./DAILY_RESEARCH_WORKFLOW.md)

---

## Daily research workflow

Review:

- Failed / rejected signals
- Regime compatibility
- Strategy scorecards (`GET /api/v1/research/scorecards`)
- Drawdowns (paper / validation)
- Edge stability
- False-positive context (rejection analytics)
- Confidence calibration drift
- Strategy degradation alerts

**Questions to ask:**

- Which setups fail most?
- Which regimes reduce expectancy?
- Which filters improve survivability?
- Which confidence thresholds reduce drawdown?

Focus only on **evidence-driven refinement**, **survivability**, **conservative improvement**, and **statistical validation** — not narrative or hype.

Policy: [FINAL_RESEARCH_DISCIPLINE_POLICY.md](./FINAL_RESEARCH_DISCIPLINE_POLICY.md) · Standard: [FINAL_VALIDATION_STANDARD.md](./FINAL_VALIDATION_STANDARD.md)

---

## Weekly workflow

1. Review strategy scorecards
2. Compare regime performance
3. Analyze drawdowns
4. Review execution-quality metrics (`GET /api/v1/observability/execution-quality`)
5. Review AI confidence drift
6. Review scanner false positives / rejection mix
7. Review operational alerts (fired / silenced)
8. Verify backups
9. Review Grafana alert rules
10. Review dependency / security notices

**Allowed changes:** threshold tuning, conservative filter improvements, validated operational fixes — **not** feature expansion.

Template: [WEEKLY_OPERATIONS_TEMPLATE.md](./WEEKLY_OPERATIONS_TEMPLATE.md)

---

## Monthly workflow

- Patch dependencies (controlled)
- Apply security fixes
- Validate backups (restore spot test)
- Rotate keys if policy requires
- Review Docker / container health
- Review operational logs
- Review technical debt reports ([TECHNICAL_DEBT_REPORT.md](./TECHNICAL_DEBT_REPORT.md))
- Validate observability coverage ([FINAL_OBSERVABILITY_STATUS.md](./FINAL_OBSERVABILITY_STATUS.md))
- Validate governance compliance ([FINAL_GOVERNANCE_AUDIT.md](./FINAL_GOVERNANCE_AUDIT.md))

Detail: [FINAL_MAINTENANCE_GOVERNANCE.md](./FINAL_MAINTENANCE_GOVERNANCE.md)

---

## Live capital policy

Live capital is **out of scope** until all of:

- Long paper-trading validation
- Acceptable drawdowns in paper / validation
- Stable edge quality
- Operational stability (health, alerts, backups)
- Confidence calibration stability

**Staged path only:** `sandbox` → `tiny_live` → staged scaling — start with **very small** capital.

Priorities: survivability · discipline · controlled scaling · capital preservation.

See [FINAL_GO_LIVE_RECOMMENDATION.md](./FINAL_GO_LIVE_RECOMMENDATION.md) and capital-safety APIs.

---

## System rules

**Must:** conservative · evidence-driven · survivability-first · operational stability · capital protection · reduce false positives · maintainable long-term.

**Must never:** guarantee profits · overtrade · bypass risk systems · trade on unreliable data · behave recklessly · act as a hype “AI prediction” platform.

---

## Future changes

Allowed only if:

- Operationally necessary
- Security-related
- Evidence-supported
- Governance-approved ([FINAL_CHANGE_CONTROL_POLICY.md](./FINAL_CHANGE_CONTROL_POLICY.md))

Architecture remains **frozen**.

---

## Related docs

| Doc | Use |
|-----|-----|
| [FINAL_OPERATIONS_PLAYBOOK.md](./FINAL_OPERATIONS_PLAYBOOK.md) | Full lifecycle (daily → quarterly) |
| [MASTER_OPERATIONS_INDEX.md](./MASTER_OPERATIONS_INDEX.md) | Documentation spine |
| [OPERATIONS_MONITORING_GUIDE.md](./OPERATIONS_MONITORING_GUIDE.md) | Metrics and golden signals |

**The platform is complete. Operate, validate, and research — do not expand without governance.**
