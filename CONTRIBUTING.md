# Contributing (v4.0.2 — architecture frozen)

This repository is **complete** as a product architecture. Contributions must follow governance — not expand scope casually.

## Read first

1. **[docs/FINAL_STABLE_RELEASE_CHARTER.md](docs/FINAL_STABLE_RELEASE_CHARTER.md)** — authoritative post-release policy  
2. **[docs/FINAL_CHANGE_CONTROL_POLICY.md](docs/FINAL_CHANGE_CONTROL_POLICY.md)** — how changes are reviewed and released  
3. **[docs/MASTER_OPERATIONS_INDEX.md](docs/MASTER_OPERATIONS_INDEX.md)** — operations spine  

## Allowed without formal scope reopening

- Security fixes and dependency/CVE patches (with regression checks)
- Validated bug fixes (tests or reproduction steps)
- Operational improvements (monitoring, runbooks, deploy docs) that **do not** change trading semantics
- Documentation corrections

## Not allowed without formal governance approval

- New engines, duplicate modules, speculative “AI prediction” layers
- Architecture redesigns, indicator/dashboard sprawl
- Changes that bypass risk, data-quality, or capital-safety gates
- Defaulting **live execution** on or weakening conservative filters

## Pull request checklist

- [ ] Change type matches charter (bug / security / ops / docs)
- [ ] `EXECUTION_ENABLED` and safety defaults unchanged unless explicitly approved
- [ ] Tests run (`pytest`) for code changes
- [ ] Runbooks or ops docs updated if behavior or alerts change
- [ ] No secrets in commits

## Disclaimer

This software does not provide financial advice. No contribution should imply guaranteed profitability.
