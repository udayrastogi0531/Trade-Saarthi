# Final technical debt report

**Aligned with:** [TECHNICAL_DEBT_REPORT.md](./TECHNICAL_DEBT_REPORT.md) — this is the **closure** snapshot for the final phase.

## Must-fix before broad external exposure

1. **Rate limiting** — config exists; implement at edge or middleware.
2. **API auth** — enforce when exposing beyond trusted network.

## Should-fix (next maintenance window)

1. Composite DB indexes for high-volume accounts.
2. Scanner queue **max length** policy (reject or shed load with 429).
3. Full pytest in CI with Postgres service container.

## Won’t fix (by design)

- **No in-app broker credential encryption** — delegated to secret manager + disk encryption.
- **No built-in HSM** — institutional clients integrate externally.

## Debt trend

**Flat / decreasing** if change freeze and monitoring discipline are maintained.
