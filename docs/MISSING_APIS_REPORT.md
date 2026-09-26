# Missing APIs Report

This report catalogs all missing API integrations in the AI Trading Terminal, outlining why they are needed, pricing tiers, and their prioritization ranking.

---

## Missing APIs Registry

### 1. Zerodha Kite Connect Derivatives Feed (Real Options Chain)
* **Description:** Integration with Zerodha Kite Connect active derivatives instruments and quote streams.
* **Why Needed:** Replace the completely synthetic/simulated options PCR, strikes, open interest, and implied volatility Skews with actual real-time options data to allow safe, real derivatives trading for your father.
* **Price / Tier:** **Paid** (Zerodha charges ₹2000/month for standard publisher API access, plus ₹2000/month for active real-time ticks/quotes/depth streams).
* **Prioritization:** **🚨 CRITICAL** (for options trading) / **⚠️ IMPORTANT** (for macro-market diagnostics).

### 2. Institutional News API (NewsAPI / MarketAux / Bloomberg)
* **Description:** Integration with dedicated institutional news tickers.
* **Why Needed:** Google News RSS is excellent and free, but it rate-limits under heavy scanning cycles and is prone to HTML formatting changes. A professional JSON News API provides stable, structured macro headlines and catalyst details.
* **Price / Tier:** **Free / Paid** (NewsAPI and MarketAux have excellent free tiers for 100 requests/day; premium tiers start at $29/month).
* **Prioritization:** **⚠️ IMPORTANT** (for macro and catalyst-driven stock filtering).

### 3. Kite Connect Profile & Margins API (`kite.margins()`)
* **Description:** Integration with Kite account profiles and margin/funds check.
* **Why Needed:** Retrieve available cash limits, collateral margins, and account balances to feed into the Risk Position Sizing Engine. Currently, position sizing runs on a static `.env` default account capital parameter (`100,000`), ignoring actual account constraints!
* **Price / Tier:** **Free** (Included inside the active Kite Connect subscription).
* **Prioritization:** **⚠️ IMPORTANT** (for robust capital protection).

### 4. SMTP / Email Push Mailer (SendGrid / Mailgun)
* **Description:** Mail server connector inside the Alerting Engine.
* **Why Needed:** Send daily Pre-Market briefings, portfolio summaries, or critical drawdown alerts directly to your father's inbox, ensuring a backup alerting channel outside Telegram.
* **Price / Tier:** **Free** (SMTP is free; SendGrid allows 100 free emails/day).
* **Prioritization:** **🟢 OPTIONAL**.

### 5. Ollama API Integration (Offline Local LLM Engine)
* **Description:** Local inference connector (e.g. `http://localhost:11434`) for open-source models like Llama-3 or Mistral.
* **Why Needed:** Run Hinglish prompts and advisor commentaries completely locally on your father's CPU/GPU, eliminating reliance on external Groq keys, network latency, and API costs.
* **Price / Tier:** **100% Free** (Open Source).
* **Prioritization:** **🟢 OPTIONAL**.

---

## Prioritization Summary

* **Critical Priority:** Real Options/Derivatives Chain API (Zerodha/NSE).
* **Important Priority:** Institutional News API (NewsAPI/MarketAux), Kite Account Profile & Margins API.
* **Optional Priority:** SMTP Email Mailer, Ollama local LLM connector.
