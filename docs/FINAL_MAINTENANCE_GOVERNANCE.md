# Final maintenance governance

**Authority:** [FINAL_STABLE_RELEASE_CHARTER.md](./FINAL_STABLE_RELEASE_CHARTER.md) · [FINAL_CHANGE_CONTROL_POLICY.md](./FINAL_CHANGE_CONTROL_POLICY.md)

## Principles

- Maintenance stays **lightweight** and **evidence-driven**
- No “drive-by” refactors during patch weeks
- Dependency updates are **controlled**, not automatic blind upgrades

## CVE / dependency workflow

| Step | Action |
|------|--------|
| 1 | Monitor advisories (GitHub Dependabot, `pip audit`, base image scans) |
| 2 | Triage severity (CVSS + exploitability + exposure) |
| 3 | Patch in branch; run `pytest` |
| 4 | Note in PR per change control (P0/P2) |
| 5 | Deploy during maintenance window; watch metrics 24h |

## Cadence (summary)

| Frequency | Work |
|-----------|------|
| Weekly | Patch triage; ops review ([WEEKLY_OPERATIONS_TEMPLATE.md](./WEEKLY_OPERATIONS_TEMPLATE.md)) |
| Monthly | Apply security patches; backup restore spot test |
| Quarterly | Dependency audit refresh ([FINAL_DEPENDENCY_AUDIT.md](./FINAL_DEPENDENCY_AUDIT.md)); DR exercise |

Full detail: [FINAL_MAINTENANCE_PLAN.md](./FINAL_MAINTENANCE_PLAN.md).

## Docker / infrastructure

- Pin image tags in production; rebuild on CVE
- Verify `docker compose` healthchecks after upgrades
- Rotate secrets on compromise or scheduled policy

## Documentation maintenance

- Any behavior change → update runbook + [FINAL_OPERATIONS_PLAYBOOK.md](./FINAL_OPERATIONS_PLAYBOOK.md) if cadence affected
- Keep [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) current when adding governance docs only (rare post-freeze)

## What maintenance is not

- Not a channel for new trading features disguised as “ops improvements”
- Not exemption from charter without P5 approval
