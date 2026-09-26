# Validation methodology

## Principles

1. **Evidence over narrative** — metrics come from DB and backtest engines, not LLM prose.
2. **Out-of-sample discipline** — walk-forward splits train vs test windows; flag overfitting when IS ≫ OOS Sharpe gap.
3. **Tail risk** — Monte Carlo on realized or simulated PnL series; report ruin probability as **diagnostic**, not prophecy.
4. **No profit guarantee** — all reports include uncertainty and sample-size caveats.

## Workflows

| Workflow | API / UI | Output |
|----------|----------|--------|
| Walk-forward | `POST /validation/walk-forward` | Stability, decay, overfitting flags |
| Monte Carlo | `POST /validation/monte-carlo` | Drawdown distribution, survival proxy |
| Strategy scorecards | `GET /research/scorecards` | Per-setup/regime DB aggregates |
| Edge quality | `GET /research/edge-quality` | Top/bottom setups + paper metrics |
| Paper ops | `GET /paper/summary` | Win rate, rejection rate over window |

## Acceptance criteria (research)

- Sample sizes **disclosed** in narratives.
- Rejection rate **not** labeled as “true false positive rate” without labeled outcomes.
- Live promotion **blocked** until capital safety stage explicitly advanced.

## References

- [STABILIZATION_AUDIT.md](./STABILIZATION_AUDIT.md)  
- [PERFORMANCE_BENCHMARK.md](./PERFORMANCE_BENCHMARK.md)
