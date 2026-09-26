# Final research discipline policy

**Version:** 4.0.2  
**Applies to:** All desk research using this platform.

## Core principles

1. **Evidence over narrative** — metrics from validation engines and DB, not LLM prose alone.
2. **Survivability over peak returns** — drawdowns and tail paths matter more than best-case backtests.
3. **Conservative by default** — when data quality or regime is uncertain, **do not** promote risk.
4. **No profit guarantees** — all outputs are provisional and sample-dependent.

## Required workflow

Follow gate order in [FINAL_RESEARCH_WORKFLOW.md](./FINAL_RESEARCH_WORKFLOW.md):

1. Data quality green  
2. Hypothesis documented (including falsification criteria)  
3. Walk-forward validation  
4. Monte Carlo stress  
5. Regime compatibility review  
6. Strategy scorecard comparison  
7. Edge decay monitoring  
8. Execution analytics (paper/sim)

## Focus areas (in scope)

- Statistical edge validation  
- Regime compatibility  
- Strategy decay detection  
- Confidence calibration stability  
- Signal quality and rejection analytics  
- Execution reliability and slippage in simulation  

## Out of scope (forbidden framing)

- Speculative “AI will predict the market” narratives  
- Unvalidated live promotion  
- Aggressive leverage or bypass of capital safety  

## Human accountability

AI copilot assists explanation and exploration; **risk and capital decisions remain human** with mechanical gates unchanged.

## References

- [VALIDATION_METHODOLOGY.md](./VALIDATION_METHODOLOGY.md)  
- [FINAL_VALIDATION_STANDARD.md](./FINAL_VALIDATION_STANDARD.md)  
- [DAILY_RESEARCH_WORKFLOW.md](./DAILY_RESEARCH_WORKFLOW.md)
