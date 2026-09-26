# News Intelligence Audit

This report audits the News Intelligence Engine, checking its data sources, crawling mechanisms, update frequencies, sentiment algorithms, and whether headlines are real or simulated.

---

## Technical Audit Parameters

### 1. Data Source
* **Primary Source:** Google News RSS Search Feed
* **Query URL Format:**
  `https://news.google.com/rss/search?q={search_sym}+stock+market+india&hl=en-IN&gl=IN&ceid=IN:en`
* **Mechanics:** Binds to `backend/app/modules/intelligence/news.py` [L23-38](file:///d:/AI%20Trading/backend/app/modules/intelligence/news.py#L23-L38). Uses `httpx.AsyncClient` to crawl Google News dynamically and parses XML elements (`item`, `title`, `link`, `pubDate`, `source`).

### 2. Update Frequency
* **Dynamic Real-Time:** Fetched on-demand whenever the backend processes an analysis. There is no background scraping cron; it executes a live network request.

### 3. Sentiment Scorer (Algorithmic Reality)
* **Algorithm:** Keyword-based heuristic scoring.
* **Logic:** Converts headlines to lowercase, then counts occurrences of defined indicators:
  * **Bullish Words:** `profit`, `rise`, `grow`, `bullish`, `buy`, `gain`, `surge`, `rally`, `up`, `outperform`, `expand`, `record`, `dividend`, `acquisition`, `bonus`, `high`.
  * **Bearish Words:** `loss`, `fall`, `drop`, `bearish`, `sell`, `decline`, `plunge`, `slump`, `down`, `underperform`, `shrink`, `deficit`, `investigation`, `penalty`, `fine`, `low`.
* **Formula:**
  `score = (bull_count - bear_count) / (bull_count + bear_count)` (values range from `-1.0` to `1.0`).

---

## Verdict: Real or Simulated?

> [!TIP]
> **VERDICT:** **REAL NEWS IS ACTUALLY FETCHED.**
> 
> The system implements a legitimate, functioning RSS parser that retrieves real-time financial articles for Indian tickers without requiring paid API keys!
> 
> * **Simulated Fallback:** It only falls back to simulated news (`_get_fallback_news`) if the Google RSS URL returns a non-200 code, times out, or when network requests fail.
> * **The Fallback Tickers:** Hardcoded mock news about "Steady trading amid market consolidation" and "Institutional buying interest" serves as safety indicators when offline.
