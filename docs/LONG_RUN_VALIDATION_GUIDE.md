# Long-run validation guide

## Objective

Demonstrate **stability of edge estimates** and **survivability of rules** over weeks–months, not single backtests.

## Inputs

- Continuous **paper** trading and/or **signal logs** (`signals`, `trade_journal`, `setup_performance`).
- Periodic **walk-forward** runs on the same strategy configuration (store in `walk_forward_runs`).
- **Monte Carlo** on rolling windows of realized PnL when `trades` exist.

## Cadence

| Horizon | Activity |
|---------|----------|
| Weekly | Review scorecards + paper summary ([WEEKLY_OPERATIONS_TEMPLATE.md](./WEEKLY_OPERATIONS_TEMPLATE.md)) |
| Monthly | Compare last 4 walk-forward stability scores; flag monotonic decay |
| Quarterly | Full methodology review ([VALIDATION_METHODOLOGY.md](./VALIDATION_METHODOLOGY.md)) |

## Pass / fail heuristics (desk-defined)

- **Fail research promotion** if: OOS Sharpe gap persistently above internal threshold **and** `overfitting_flag` true in stored runs.
- **Fail risk relaxation** if: Monte Carlo `probability_of_ruin` above desk threshold **or** drawdown p99 worsening month-over-month.

## Outputs

- CSV/JSON exports from API for external archival (optional).
- Grafana annotations for “validation run” markers.

## Disclaimer

Past paper performance does not guarantee live results. This guide supports **discipline**, not **automation of go-live**.
