# AI Copilot Context Audit

This report audits the AI Copilot's prompt context builder. We trace exactly what data enters the LLM's system prompt when your father asks: **"Should I sell TCS?"**

---

## Context Injection Matrix

We audited the `CopilotContextBuilder` in `backend/app/modules/copilot/context_builder.py` [L19-159](file:///d:/AI%20Trading/backend/app/modules/copilot/context_builder.py#L19-L159). Here is what gets injected into the LLM context:

| Context Element | Present | Source & Status |
| :--- | :--- | :--- |
| **Kite Holdings** | **YES (Mock Fallback)** | Calls `sync.fetch_portfolio()`. Since no `db` session is passed, it **always falls back to the mock portfolio** (`RELIANCE`, `TCS`, etc.), ignoring your father's actual Zerodha assets! |
| **Technical Market Data** | **YES (Real-Time)** | Extracts `"TCS"` and fetches real candles. Computes RSI, Trend, Trend Strength, Volatility, ATR, and Market Regime. |
| **Risk Policy** | **YES (Real-Time)** | Pulls current limits (Max daily loss `2%`, Drawdown `10%`, etc.) from `.env`. |
| **News Catalysts** | **NO (Complete Blind Spot)** | **Not included.** The context builder does not query `NewsIntelligenceEngine` for TCS. The AI makes sell decisions with zero knowledge of recent earnings, SEBI orders, or headlines! |
| **Options Greeks & PCR** | **NO (Complete Blind Spot)** | **Not included.** The context builder does not query `OptionChainEngine`. The AI has zero visibility into ATM delta, gamma, support/resistance zones, or Put-Call ratios! |
| **Scanner Results** | **NO (Complete Blind Spot)** | **Not included.** The scanner's specific breakout indicators or ratings for TCS are not injected into the prompt. |

---

## Verdict: Is the Copilot Ready?

> [!WARNING]
> **VERDICT:** **PARTIALLY COMPROMISED.**
> 
> The AI Copilot is excellent at interpreting basic technical parameters (like Trend and RSI) for TCS. However:
> 
> 1. **It hallucinates holdings:** It will tell your father what to do with TCS based on the **mock portfolio quantity of 8 shares at an average price of 4120**, rather than his actual Zerodha portfolio.
> 2. **It has no macro awareness:** It has absolute blind spots regarding news catalysts and options open interest zones. It cannot provide high-fidelity financial advice without these critical context pieces.
