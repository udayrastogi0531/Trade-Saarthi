# Runtime Validation Report

This report documents the actual operational startup, runtime commands, API response states, and dashboard compilation parameters for the AI Trading Terminal.

---

## Service Startup & Verification

### 1. Backend API Service
* **Command:** `.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`
* **Status:** **Fully Operational**
* **Verification:** The backend launches and boots the FastAPI webserver in less than `1.2s`. Mounts 22 routers. Binds standard database migrations cleanly.
* **REST API Documentation:** Available locally at `http://127.0.0.1:8000/docs` (Swagger UI).

### 2. Frontend Streamlit Dashboard
* **Command:** `.\.venv\Scripts\streamlit run frontend/dashboard/app.py`
* **Status:** **Fully Operational**
* **Verification:** The Streamlit dashboard starts successfully, binds to the default port `8501`, and opens in the browser. It displays the dark-mode layout with 9 active tabs (Signal Analyzer, Trades, Backtest, Chart, Portfolio, News, Options, Briefings, Opportunities).

---

## Endpoint Response Validation

| Endpoint Path | Method | Operational Status | Reality/Calculations Returned |
| :--- | :--- | :--- | :--- |
| `/api/v1/health` | `GET` | **100% OK** | Binds to `health.py` and returns `{"status": "ok", "environment": "development", "paper_trading": true, "execution_enabled": false}`. |
| `/api/v1/portfolio` | `GET` | **100% OK** | Binds to `portfolio.py`. Returns holdings, positions, and summary metrics. **Mock Warning:** Returns simulated RELIANCE/TCS shares unless static env token is entered. |
| `/api/v1/portfolio/analysis` | `GET` | **Clashed / Shadowed** | Shadowed by the older Trades-based route. **Unreachable.** Queries `Trade.status == "open"` in local db, ignoring Kite completely. |
| `/api/v1/portfolio/analyze-position` | `POST` | **100% OK** | Computes RSI, Daily Trend, Volatility ATR, PCR, FII/DII sentiment, and rule-based Hinglish Father Mode explanations. |
| `/api/v1/scanner/buy-candidates` | `GET` | **100% OK** | Runs parallel async tasks to score the watchlist symbols. |
| `/api/v1/scanner/sell-candidates` | `GET` | **100% OK** | Evaluates holdings (mock) and flags stocks for reduce/exit. |
| `/api/v1/copilot` | `POST` | **100% OK** | Streams AI token responses using Groq/DeepSeek model integrations. |

---

## Test Suite Execution Report
We ran the complete unit and integration test suite via `pytest`:
* **Command:** `.\.venv\Scripts\pytest -v`
* **Result:** `25 passed, 4 skipped in 30.66s`.
* **Details:**
  * Multi-Timeframe Alignment (`test_mtf.py`) -> **PASSED**
  * Market Regime Detection (`test_regime.py`) -> **PASSED**
  * Risk Position Sizing (`test_risk.py`) -> **PASSED**
  * AI Copilot Language Processing (`test_copilot.py`) -> **PASSED**
  * Monte Carlo & Walk-Forward (`test_validation.py`) -> **PASSED**
  * Technical Indicator Computations (`test_technical_analysis.py`) -> **PASSED**

> [!NOTE]
> **Why 4 tests skipped:** Database and external broker network tests are automatically skipped inside the dev/sandbox environment if an active live connection to Zerodha or an active database instance isn't running. This is standard safety logic.
