# Incident response guide

## Severity levels

| Level | Definition | Example |
|-------|------------|---------|
| SEV1 | Trading safety compromised or data corruption | Kill switch stuck off; mass bad orders |
| SEV2 | Major degradation | API down; Postgres read-only |
| SEV3 | Partial degradation | Redis flapping; scanner unhealthy |

## SEV1 playbook (outline)

1. **Stop risk:** enable kill switch / `emergency_shutdown` via capital safety API if live path exists.
2. **Preserve evidence:** export logs + DB snapshot if policy allows.
3. **Communicate:** stakeholder template per org policy.
4. **Rollback:** redeploy last known good image; restore DB if corrupted.

## SEV2 / SEV3

- Scale/restart failed service (API, worker, Redis).
- Follow [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).

## Post-incident

- Root cause doc within 5 business days.
- Update [ALERTING_MATRIX.md](./ALERTING_MATRIX.md) if gap found.

## Contacts

Fill in org-specific:

- Primary on-call: _______________
- Escalation: _______________
