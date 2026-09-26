# Codebase Reality Report

This report audits every major module of the AI Trading Terminal codebase, providing a brutally honest assessment of whether the code is fully implemented, partially implemented, a placeholder, dead code, or a mock implementation.

---

## Module Status Matrix

| Module | Location | Status | Summary of Reality |
| :--- | :--- | :--- | :--- |
| **Broker Integration** | `backend/app/api/routes/broker.py`, `app/services/broker_tokens.py` | **Partially Implemented** | Login URL (`/broker/kite/login-url`) and OAuth callback (`/broker/kite/callback`) are fully functional. Dynamic access tokens are correctly saved to the DB via `BrokerTokenService`. **Critical Gap:** The `KitePortfolioSync` engine completely ignores these DB tokens and relies solely on a static `.env` string! |
| **Portfolio Sync** | `backend/app/modules/portfolio/kite_sync.py`, `app/api/routes/portfolio.py` | **Partially Implemented** | Fetches holdings/positions from Zerodha Kite. If offline or not configured, it gracefully falls back to mock holdings (`RELIANCE`, `TCS`, etc.) with live Yahoo Finance pricing. **Critical Gap:** Route clashing on `GET /portfolio/analysis` shadows the newer holdings-based Portfolio Assistant, making it completely unreachable. |
| **Stock Health Scoring** | `backend/app/modules/portfolio/health_score.py` | **Fully Implemented** | Unified indicator-based scoring model (Trend, Volume, Structure, Sentiment, Volatility, Relative Strength) on a 0-100 scale. Works flawlessly out-of-the-box. |
| **Opportunity Engines** | `backend/app/modules/scanner/opportunity_engine.py` | **Fully Implemented** | Buy opportunity engine ranks watchlist breakouts. Sell opportunity engine scans portfolio holdings and flags candidates for exit. |
| **Option Chain Engine** | `backend/app/modules/market_data/option_chain.py` | **Mock / Synthetic** | **Brutal Reality:** Does NOT fetch any option chain data from Zerodha or the NSE! It generates synthetic strikes, implied volatilities, and open interest using random decay models centered on spot prices. While Black-Scholes Greeks calculations are real, they run on completely fake inputs. |
| **News Intelligence** | `backend/app/modules/intelligence/news.py` | **Fully Implemented** | Actually fetches real stock news from Google News RSS feed dynamically via `httpx`. Uses a keyword-based rule set to score sentiment (-1 to 1). Falls back to mock headlines only if Google RSS fails or is rate-limited. |
| **AI Copilot Context** | `backend/app/modules/copilot/context_builder.py` | **Partially Implemented** | Assembles context (trades, regime, watchlist) for Groq/DeepSeek calls. **Gap:** It does not pass `db` to `KitePortfolioSync`, causing the Copilot to always analyze the mock portfolio. It also ignores options Greeks and news in the query focus. |
| **Father Mode Explanation** | `backend/app/modules/ai_reasoning/father_mode.py` | **Fully Implemented** | Explains stock conditions in high-quality Hinglish (Hindi/English mix). Runs via Groq LLM or uses an excellent rule-based local generator when offline. |
| **Market Structure Engine** | `backend/app/modules/market_structure/engine.py` | **Fully Implemented** | Implements Break of Structure (BOS), Change of Character (CHOCH), liquidity sweeps, and fake breakout risk detection. |
| **Risk Management Engine** | `backend/app/modules/risk/advanced.py` | **Fully Implemented** | Calculates portfolio heat, concentration limits, and correlation-based blocks dynamically. |

---

## Detailed Findings

### 1. Broker Integration & OAuth Token Gap
* **Implemented:** The OAuth flow works. It redirects the user to Zerodha's login page, handles the callback, exchanges the request token for a session token, and saves the token to the SQLite/PostgreSQL `broker_tokens` database table.
* **Mocked/Disconnected:** `KitePortfolioSync.fetch_portfolio` only queries `self._settings.kite_access_token` (from the static `.env` file). It never asks the database table for the active dynamic token, rendering the entire OAuth callback flow useless.

### 2. Option Chain Illusion
* **Brutal Reality:** There is no Kite Option Chain API integration or NSE scraping.
* strikes, OI, change in OI, and IV are 100% synthetic, generated mathematically using `np.random.default_rng(hash(symbol) % 2**32)`.
* **Impact:** The resulting option chain, support/resistance zones, and Black-Scholes Greeks are completely simulated. They have zero relationship to the actual options market and cannot be used for live option trading.

### 3. FastAPI Endpoint Shadowing
* **Dead Code / Shadowed Route:** In `backend/app/api/routes/portfolio.py`:
  - Route 1: `GET /analysis` (binds to `portfolio_analysis`) -> queries open database trades (`Trade.status == "open"`).
  - Route 2: `GET /analysis` (binds to `get_portfolio_analysis`) -> queries `KitePortfolioSync` and runs the `PortfolioAssistantEngine`.
  - **Issue:** FastAPI maps routes sequentially. Route 1 completely shadows Route 2. The holdings-based Portfolio Assistant analysis is unreachable via the REST API.
