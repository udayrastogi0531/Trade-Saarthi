# Final validation standard

**Version:** 4.0.2  
**Purpose:** Minimum institutional standard before treating a strategy as “research-approved” on this platform.

## 1. Walk-forward

| Requirement | Standard |
|-------------|----------|
| Out-of-sample splits | Train/test windows defined before viewing test results |
| Overfitting flag | Investigate when in-sample Sharpe ≫ out-of-sample |
| API | `POST /api/v1/validation/walk-forward` |
| Storage | Results persisted per platform schema |

**Fail:** Single in-sample optimization presented as validated.

## 2. Monte Carlo

| Requirement | Standard |
|-------------|----------|
| Simulations | Use configured count (e.g. `MONTE_CARLO_SIMULATIONS`); disclose N |
| Interpretation | Tail drawdown and ruin proxies are **diagnostic**, not forecasts |
| API | `POST /api/v1/validation/monte-carlo` |

**Fail:** Monte Carlo cited as “probability of profit.”

## 3. Regime analysis

- Compare performance across regimes from regime module / research APIs  
- Do not deploy logic that only works in one unlabeled regime bucket  

## 4. Scorecards

| Requirement | Standard |
|-------------|----------|
| Consistency | Same metric definitions across strategies compared |
| Source | `GET /research/scorecards` and related research endpoints |
| Ranking | Prefer stability, rejection rate context, drawdown-aware measures |

## 5. Confidence calibration

- Track stated confidence vs outcomes over paper window  
- Rising rejections or decay alerts → downgrade trust, do not increase size  

## 6. Edge decay

- Monitor `trading_strategy_decay_alerts_total` and research decay endpoints  
- Treat decay as **stop/review** signal, not auto-disable without human policy  

## 7. Promotion to live (if ever)

Blocked unless:

- [ ] Capital safety stage explicitly advanced (`sandbox` → staged → `tiny_live` per desk policy)  
- [ ] `can_execute_live` true with no blockers  
- [ ] `EXECUTION_ENABLED` deliberately set with sign-off  
- [ ] Data quality green for promotion window  

## Acceptance record

Archive validation artifacts (run IDs, dates, parameters) per strategy review — see [FINAL_OPERATIONS_PLAYBOOK.md](./FINAL_OPERATIONS_PLAYBOOK.md).

## References

- [VALIDATION_METHODOLOGY.md](./VALIDATION_METHODOLOGY.md)  
- [FINAL_RESEARCH_DISCIPLINE_POLICY.md](./FINAL_RESEARCH_DISCIPLINE_POLICY.md)
