# Portfolio Intelligence Guide

The Portfolio Intelligence module provides advanced quantitative health metrics and recommendation matrices for individual equity positions.

## Computed Metrics

* **Trend Score (0-100):** Quantifies daily trend direction and velocity, with scores >50 indicating bullish structures.
* **Risk Score (0-100):** Blends volatility (ATR percentage), momentum extremes (RSI), and structural trends to classify risk profiles.
* **News Sentiment Score (-1.0 to +1.0):** Compiles sentiment heuristics from Google News to assess positive/negative catalyst flows.
* **Volume Strength:** Evaluates recent volume metrics to classify interest level (Very Strong, Strong, Average, Weak).
* **Relative Strength vs Nifty:** Compiles relative outperformance percentage compared directly to the benchmark Nifty 50 Index.

## Action Recommendations

1. **🟢 BUY:** Strong bullish trend structure, healthy momentum, and stable relative outperformance.
2. **🟡 HOLD:** Bullish trend but short-term overbought (RSI > 72), or neutral range-bound structure.
3. **🟠 REDUCE:** Bearish trend structure forming. Trim quantity to scale back capital exposure.
4. **🔴 EXIT:** Stop-loss margin exceeded (PnL < -8%) or extreme risk score. Exit recommended.
