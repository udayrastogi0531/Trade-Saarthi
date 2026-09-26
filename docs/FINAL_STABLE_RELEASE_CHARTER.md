# Final stable release charter

**Product:** AI Quantitative Trading Intelligence Platform  
**Release line:** v4.0.2 — **architecture complete and frozen**  
**Purpose:** Authoritative **post-completion** policy for engineering, operations, and research. This is not a feature roadmap.

---

## 1. What this platform is

- A **professional quantitative research terminal** and market intelligence workstation.
- A **conservative, risk-first** execution-assistance stack (execution **off by default**; staged `sandbox` / `tiny_live` when explicitly enabled).
- A **long-term operational asset** — maintained for stability, not endless expansion.

---

## 2. Engineering policy (allowed changes only)

With the **architecture freeze** in force, changes are limited to:

| Allowed | Examples |
|---------|----------|
| Security fixes | Auth, secrets handling, dependency CVEs |
| Validated bug fixes | Correctness, crashes, data corruption risks |
| Dependency updates | Patched runtimes and libraries with regression checks |
| Operational improvements | Monitoring, alerts, runbooks, deploy ergonomics |
| Documentation | Accuracy, onboarding, incident playbooks |

**Not allowed without formal reopening of scope:** new engines, duplicate modules, speculative “AI prediction” layers, architecture redesigns, indicator/dashboard sprawl, or aggressive automation that bypasses risk and data-quality gates.

**Compatibility:** preserve backward compatibility for public APIs and deployment contracts where reasonable; document intentional breaks.

**Evidence:** every change should be justified by a **proven** operational or safety problem, with tests or runbook updates as appropriate.

---

## 3. System rules (non-negotiable)

The platform **must**:

- Stay **conservative** and **evidence-driven**; prioritize **survivability** and **capital preservation**.
- Enforce **data quality** and **conservative signal filtering**; reduce false positives over raw activity.
- Preserve **observability** and **auditability**.

The platform **must never**:

- Imply **guaranteed profits** or certainty.
- **Bypass** risk systems, kill switches, or reliability gates.
- **Trade** on knowingly unreliable data.
- Present itself as a hype **“AI prediction bot”** or unconstrained autopilot.

---

## 4. Operational stance

Operate as a **quant research environment**:

- Prefer **paper trading**, validation, regime analysis, strategy scorecards, edge stability, drawdown control, execution-quality monitoring.
- Use [MASTER_OPERATIONS_INDEX.md](./MASTER_OPERATIONS_INDEX.md) for daily/weekly workflows and monitoring.

---

## 5. Research stance

Focus research on:

- Statistical edge validation, regime compatibility, strategy decay, confidence calibration, signal quality, survivability, execution reliability, drawdown behavior.

Avoid speculative AI narratives as substitutes for **measurement** and **human judgment** on risk.

See [FINAL_RESEARCH_WORKFLOW.md](./FINAL_RESEARCH_WORKFLOW.md) and [VALIDATION_METHODOLOGY.md](./VALIDATION_METHODOLOGY.md).

---

## 6. Maintenance stance

Continue: dependency and CVE patching, monitoring and alert review, backup validation, Docker and infra hygiene, documentation updates per [FINAL_MAINTENANCE_PLAN.md](./FINAL_MAINTENANCE_PLAN.md).

---

## 7. Completion statement

The platform is **complete** as an architecture. The goal forward is **responsible operation**, **continuous validation**, **disciplined research**, **stability**, and **operational excellence** — not open-ended building.

---

*This charter supersedes informal “keep adding features” expectations for the frozen release line. Formal governance may amend it with version history.*

---

## Related governance (absolute final pass)

- [OPERATION_MODE.md](./OPERATION_MODE.md) — **how to run the platform day-to-day**
- [FINAL_GOVERNANCE_AUDIT.md](./FINAL_GOVERNANCE_AUDIT.md)  
- [FINAL_CHANGE_CONTROL_POLICY.md](./FINAL_CHANGE_CONTROL_POLICY.md)  
- [FINAL_OPERATIONS_PLAYBOOK.md](./FINAL_OPERATIONS_PLAYBOOK.md)  
- [CONTRIBUTING.md](../CONTRIBUTING.md)
