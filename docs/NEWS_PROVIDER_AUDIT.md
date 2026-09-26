# News Provider Integration Audit

This report audits the status of News API, Google News RSS, and MarketAux inside the News Intelligence engine.

---

## News Providers Evaluation

### 1. Google News RSS Crawler
* **Status:** **FULLY IMPLEMENTED & REAL**
* **Active Key in `.env`:** **NO** (100% Free - no keys required)
* **Integration Reality:**
  - Crawls `https://news.google.com/rss/search` dynamically using `httpx`.
  - Parsed XML items return real financial news titles, URLs, pub dates, and sources for Indian tickers in real-time.
  - Sentiment is scored using a hardcoded keyword-based list.
* **Verdict:** Real and active. Serves as the primary working news feed.

### 2. NewsAPI.org
* **Status:** **COMPLETELY MISSING (Docstring Placeholder)**
* **Active Key in `.env`:** **NO** (Unconfigured)
* **Integration Reality:**
  - Mentioned in `fetch_stock_news` docstrings: *"Fetch news for a symbol from Google News RSS (Free) or NewsAPI (if configured)."*
  - **The Reality:** There is zero code implementing NewsAPI requests, payload formats, HTTP endpoints, or Settings keys in `config.py`!
* **Verdict:** Missing.

### 3. MarketAux
* **Status:** **COMPLETELY MISSING**
* **Active Key in `.env`:** **NO**
* **Integration Reality:**
  - There is zero reference, import, or configuration key for MarketAux.
* **Verdict:** Missing.

---

## Verdict Summary

| News Provider | Implemented | Configured in `.env` | Active Source | Data Type |
| :--- | :--- | :--- | :--- | :--- |
| **Google News RSS** | **YES** | **NO** (No key needed) | **YES** | **REAL** (Crawled dynamically) |
| **NewsAPI** | **NO** | **NO** | **NO** | **MOCK** (Falls back to static template) |
| **MarketAux** | **NO** | **NO** | **NO** | **MOCK** |
