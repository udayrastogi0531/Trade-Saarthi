# Final research workflow (institutional discipline)

**Version:** 4.0.2  
**Purpose:** Lock **how** research is conducted on this platform — evidence over narrative. No new engines; alignment with existing modules only.

## Canonical references

- [VALIDATION_METHODOLOGY.md](./VALIDATION_METHODOLOGY.md) — walk-forward, Monte Carlo, interpretation rules.
- [QUANT_V4.md](./QUANT_V4.md) — capability map and intended use.
- [DAILY_RESEARCH_WORKFLOW.md](./DAILY_RESEARCH_WORKFLOW.md) — daily checklist.

## Workflow order (do not skip)

1. **Data quality** — confirm feeds healthy (`observability`, data-quality metrics); if degraded, **do not** treat signals as comparable to prior days.
2. **Hypothesis** — document symbol/universe, horizon, and what would **falsify** the idea before running validation.
3. **Walk-forward** — primary robustness gate; avoid peeking at future folds.
4. **Monte Carlo** — stress paths and tail behavior; interpret as **survivability**, not expected PnL.
5. **Regime context** — compare performance across regimes; avoid single-regime overfitting.
6. **Scorecard** — use consistent metrics across strategies; rank by **stability** and drawdown-aware measures, not peak returns alone.
7. **Edge decay** — monitor rolling hit rate / expectancy drift; treat rising rejection rates as information.
8. **Execution analytics** — even in paper, review simulated slippage and rejections before any live discussion.

## UX / presentation (terminal)

- Prefer **side-by-side strategy comparison** and **regime heatmaps** where the UI already exposes them; extend only via existing APIs — no new indicator layers in this freeze phase.

## Forbidden shortcuts

- Optimizing parameters on the full sample then “validating” on the same sample.
- Treating AI narrative as approval for risk — AI assists **human** judgment; capital gates remain mechanical.

## Sign-off line

Research conclusions are **provisional** until data quality is green and validation artifacts are archived for the run.
