# Portfolio Assistant Guide

The **Portfolio Assistant** performs quantitative evaluations on current stock positions to offer reliable decision directives.

## Decision Matrix

The assistant calculates indicators (RSI, ATR, Trend direction, multi-timeframe alignment) to determine a clear action path:

1. **🟡 HOLD:**
   * Trend is bullish but market is short-term overbought (RSI > 70).
   * Market structure is sideways/neutral. Protect capital and hold.
2. **🟢 ADD:**
   * Trend is bullish with stable RSI levels (< 70).
   * Volume is expanding, indicating room to accumulate.
3. **🟠 REDUCE:**
   * Trend is entering a bearish structure.
   * Volatility is expanding; trim shares to limit capital exposure.
4. **🔴 EXIT:**
   * Stop-loss parameters are exceeded (e.g. unrealized PnL < -10%).
   * Exiting is recommended for strict capital protection.

## Usage

Navigate to the **💼 Portfolio Assistant** tab in the Streamlit dashboard, enter your stock symbol, quantity owned, and average buy price, and click **Analyze Position Decision**.
