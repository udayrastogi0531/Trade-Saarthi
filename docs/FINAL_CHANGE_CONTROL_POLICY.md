# Final change control policy

**Applies to:** v4.0.2+ (architecture frozen)  
**Authority:** [FINAL_STABLE_RELEASE_CHARTER.md](./FINAL_STABLE_RELEASE_CHARTER.md)

## 1. Change categories

| Category | Approval | Examples |
|----------|----------|----------|
| **P0 Security** | Expedited; post-merge review | CVE patch, credential leak fix |
| **P1 Safety** | Two reviewers; risk sign-off if execution-adjacent | Kill switch, data-quality gate, capital safety |
| **P2 Bug** | One reviewer + tests | Crash, incorrect metric, WS cleanup |
| **P3 Ops** | One reviewer | Runbooks, Grafana JSON, alert docs |
| **P4 Docs** | One reviewer | Typos, index links, governance |
| **P5 Scope** | **Formal reopening** | New engine, new product module, API breaking redesign |

## 2. Prohibited without P5 approval

- New duplicate pipelines or scanners
- Default `EXECUTION_ENABLED=true`
- Disabling `BLOCK_SIGNALS_ON_BAD_DATA` / `CONSERVATIVE_MODE` in shipped examples without explicit desk policy
- Removing audit logging or observability hooks for trading paths

## 3. PR requirements

Every PR must state:

1. **Category** (P0–P5)  
2. **Problem evidence** (issue, incident, CVE, benchmark)  
3. **Risk to trading semantics** (none / low / high)  
4. **Test plan** (`pytest`, manual steps, or N/A for docs-only)

## 4. Release

- Patch: `4.0.x` — bug/security/ops only  
- Minor: requires charter amendment if semantics change  
- Tag releases; note changes in commit message or release notes file if maintained

## 5. Rollback

- Keep previous Docker image tag deployable  
- Document rollback in [INCIDENT_RESPONSE_GUIDE.md](./INCIDENT_RESPONSE_GUIDE.md) for SEV1/SEV2

## 6. Escalation

Disputes over P5 vs P2 classification → platform owner + risk reviewer decision; default **deny** scope expansion.
