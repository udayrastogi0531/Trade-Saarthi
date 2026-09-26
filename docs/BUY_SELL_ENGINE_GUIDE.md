# Buy / Sell Engine Guide

The platform integrates two specialized discovery modules designed to filter opportunities and prune weak setups.

## Buy Opportunity Engine

Scans watchlists and ranks stocks with **Health Score >= 65** or status **BUY**.
* **Triggers:** Volatility consolidation, volume breakout (volume ratio > 1.4), positive relative strength (outperforming Nifty), and positive news sentiment.
* **Output:** Ranked list showing ticker, health score, rating (Excellent/Good/Average), buy status, and analysis confidence.

## Sell / Exit Opportunity Engine

Scans active portfolio holdings and flags weak setups.
* **Triggers:** Health Score < 50, broken trend structures (price below 50-day EMA), negative news catalysts, or stop-loss hits.
* **Output:** Ranked warning list outlining the symbol, exit status (REDUCE/SELL/EXIT), and precise stop-loss/risk reasons.
