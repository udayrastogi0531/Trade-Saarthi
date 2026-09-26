# Final maintenance plan

**Applies after:** v4.0.2 architecture freeze (no uncontrolled feature expansion).

**Authoritative policy:** [FINAL_STABLE_RELEASE_CHARTER.md](./FINAL_STABLE_RELEASE_CHARTER.md).

## Cadence

| Frequency | Activity |
|-----------|----------|
| Daily | Health checks; scanner status; queue depth (see [DAILY_RESEARCH_WORKFLOW.md](./DAILY_RESEARCH_WORKFLOW.md)) |
| Weekly | Ops review ([WEEKLY_OPERATIONS_TEMPLATE.md](./WEEKLY_OPERATIONS_TEMPLATE.md)); dependency patch triage |
| Monthly | Security patches; review slow queries; backup restore spot test |
| Quarterly | Full dependency audit refresh; risk review; DR exercise |

## Allowed change types

- Bug fixes with regression tests where feasible.
- Security patches (frameworks, base images).
- Observability / documentation improvements that do not change trading semantics.
- Performance fixes that preserve correctness.

## Change control

- PR required; two-person review for execution-adjacent or capital-safety changes.
- Release notes per semantic version bump on `app` package.

## Deprecation

- Mark deprecated endpoints in OpenAPI before removal; minimum one minor version notice.

## Ownership

- **Platform:** owns infra, deploy, monitoring.
- **Research:** owns validation methodology and signal interpretation — not the runtime alone.
