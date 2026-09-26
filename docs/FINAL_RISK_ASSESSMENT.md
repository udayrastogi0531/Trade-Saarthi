# Final risk assessment

## Inherent risks (cannot eliminate)

- **Market risk:** All analytics are probabilistic; past performance ≠ future results.
- **Model risk:** LLMs can err; mitigated by schema, fallbacks, and human oversight for live actions.
- **Operational risk:** Dependency failures (DB, Redis, broker) — mitigated by monitoring and runbooks.

## Residual product risks

| Risk | Likelihood | Impact | Control |
|------|------------|--------|---------|
| Misconfigured live execution | Low if defaults kept | High | Staging + manual confirm + kill switch |
| Data feed corruption | Medium | High | Data quality engine + alerts |
| Over-aggressive watchlist | Medium | Medium | Scanner confidence + portfolio blocks |

## Risk appetite statement

This system is designed for **capital preservation and discipline**, not maximum activity. **Low trade count** may be a **healthy** outcome.

## Sign-off recommendation

Risk owner reviews [CRITICAL_RISK_REPORT.md](./CRITICAL_RISK_REPORT.md) before any live capital.
