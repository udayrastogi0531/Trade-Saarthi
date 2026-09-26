# Mock Data Detection Report

This report lists every occurrence of sample, fallback, demo, mock, or test data hardcoded into the AI Trading Terminal codebase, traced directly to their file locations and line numbers.

---

## Mock & Fallback Catalog

### 1. Mock Portfolio Holdings
* **File Location:** `backend/app/modules/portfolio/kite_sync.py` [L102-138](file:///d:/AI%20Trading/backend/app/modules/portfolio/kite_sync.py#L102-L138)
* **What is Mocked:**
  ```python
  mock_data = [
    {"symbol": "RELIANCE", "qty": 15, "avg_price": 2810.0},
    {"symbol": "TCS", "qty": 8, "avg_price": 4120.0},
    {"symbol": "INFY", "qty": 25, "avg_price": 1950.0},
    {"symbol": "HDFCBANK", "qty": 40, "avg_price": 1690.0},
    {"symbol": "ITC", "qty": 120, "avg_price": 435.0},
  ]
  ```
* **Trigger Condition:** Automatically active if `BROKER_MODE=paper` or if Zerodha Kite token is missing or expired in the static configuration.

### 2. Options Chain Open Interest & Skew
* **File Location:** `backend/app/modules/market_data/option_chain.py` [L92-120](file:///d:/AI%20Trading/backend/app/modules/market_data/option_chain.py#L92-L120)
* **What is Mocked:** Strikes step size, Implied Volatility skew, Open Interest decay factors, and Change in OI are calculated dynamically using simulated Gaussian distributions and seed-based random number generators:
  ```python
  rng = np.random.default_rng(hash(symbol) % 2**32)
  c_oi_factor = np.exp(-((s - (atm_strike + interval)) / (3 * interval))**2)
  c_oi = int(c_oi_factor * rng.integers(100_000, 1_000_000))
  ```
* **Trigger Condition:** **ALWAYS ACTIVE.** There is no real-world options feed connection in the entire codebase.

### 3. Mock News Catalyst Feeds
* **File Location:** `backend/app/modules/intelligence/news.py` [L86-104](file:///d:/AI%20Trading/backend/app/modules/intelligence/news.py#L86-L104)
* **What is Mocked:**
  ```python
  return [
    {"title": f"{symbol} shares trade steadily amid market consolidation", "sentiment": "Neutral", "sentiment_score": 0.0},
    {"title": f"Institutional buying interest remains healthy in {symbol}", "sentiment": "Bullish", "sentiment_score": 0.5}
  ]
  ```
* **Trigger Condition:** Bypasses Google News RSS feed if the internet connection is offline or if Google News rate-limits requests.

### 4. Mock Market Data Provider
* **File Location:** `backend/app/modules/market_data/providers/mock.py` [Whole File](file:///d:/AI%20Trading/backend/app/modules/market_data/providers/mock.py)
* **What is Mocked:** Simulates price candles, open/high/low/close prices, and volume lists for any ticker requested.
* **Trigger Condition:** Active when `MARKET_DATA_PROVIDER=mock` is configured in `.env`.

### 5. Rule-Based Father Mode Hinglish Fallback
* **File Location:** `backend/app/modules/ai_reasoning/father_mode.py` [L71-96](file:///d:/AI%20Trading/backend/app/modules/ai_reasoning/father_mode.py#L71-L96)
* **What is Mocked:** Hardcoded Hinglish text templates for bullish, bearish, and neutral trends.
* **Trigger Condition:** Automatically active if `GROQ_API_KEY` is not provided or Groq service returns a rate-limit error.

### 6. Heuristic Chart Analysis Fallback
* **File Location:** `backend/app/modules/chart_analysis/engine.py` [L95-110](file:///d:/AI%20Trading/backend/app/modules/chart_analysis/engine.py#L95-L110)
* **What is Mocked:** Returns a dictionary containing `"source": "heuristic"`, empty list levels, and risk warnings.
* **Trigger Condition:** Active if `GROQ_API_KEY` is missing or when the vision model triggers a timeout.

### 7. Pre-Market and Closing Briefings Fallbacks
* **File Location:** `backend/app/modules/briefings/engine.py` [L89-125](file:///d:/AI%20Trading/backend/app/modules/briefings/engine.py#L89-L125)
* **What is Mocked:** Pre-written market summaries describing fictional movements in Nifty, Dow Jones, and crude oil.
* **Trigger Condition:** Active if Groq LLM is not configured or fails.
