# Zerodha Kite Integration Audit

This audit evaluates the reality of the Zerodha Kite integration flow. We trace the login flow, token persistence, holdings retrieval, and look at the exact mechanics of whether the system reads actual holdings or mock portfolios.

---

## Technical Flow Evaluation

### 1. Login Flow
* **Status:** **Fully Implemented**
* **Code Location:** `backend/app/api/routes/broker.py` [L13-25](file:///d:/AI%20Trading/backend/app/api/routes/broker.py#L13-L25)
* **Mechanics:** Binds to `GET /api/v1/broker/kite/login-url`. Instantiates `KiteConnect` with `settings.kite_api_key` and calls `kite.login_url()` to generate a redirect URL for Zerodha's OAuth portal.

### 2. Token Generation
* **Status:** **Fully Implemented**
* **Code Location:** `backend/app/api/routes/broker.py` [L27-50](file:///d:/AI%20Trading/backend/app/api/routes/broker.py#L27-L50)
* **Mechanics:** Binds to `GET /api/v1/broker/kite/callback`. It receives `request_token` from Zerodha's redirect, then runs:
  ```python
  session = kite.generate_session(request_token, api_secret=settings.kite_api_secret)
  access_token = session.get("access_token")
  ```

### 3. Token Persistence
* **Status:** **Fully Implemented**
* **Code Location:** `backend/app/api/routes/broker.py` [L51-64](file:///d:/AI%20Trading/backend/app/api/routes/broker.py#L51-L64)
* **Mechanics:** The access token is written dynamically to the `broker_tokens` database table:
  ```python
  await BrokerTokenService().save_token(db, "kite", access_token, metadata=metadata)
  await db.commit()
  ```

### 4. Holdings Fetch
* **Status:** **Implemented (With Static Constraints)**
* **Code Location:** `backend/app/modules/portfolio/kite_sync.py` [L30-55](file:///d:/AI%20Trading/backend/app/modules/portfolio/kite_sync.py#L30-L55)
* **Mechanics:** Calls `kite.holdings()` and maps parameters: symbol (`tradingsymbol`), quantity (`quantity`), and average price (`average_price`).

### 5. Positions Fetch
* **Status:** **Implemented (With Static Constraints)**
* **Code Location:** `backend/app/modules/portfolio/kite_sync.py` [L57-65](file:///d:/AI%20Trading/backend/app/modules/portfolio/kite_sync.py#L57-L65)
* **Mechanics:** Calls `kite.positions().get("net", [])` to retrieve active intraday/net positions.

### 6. Portfolio Sync
* **Status:** **Implemented**
* **Code Location:** `backend/app/modules/portfolio/kite_sync.py` [L19-89](file:///d:/AI%20Trading/backend/app/modules/portfolio/kite_sync.py#L19-L89)
* **Mechanics:** Combines holdings, positions, and aggregate summaries (Total Invested, Current Value, P&L, P&L %). It updates real-time valuations using yfinance if the exchange stream is inactive.

### 7. Account Profile Retrieval
* **Status:** **NOT IMPLEMENTED (Complete Gap)**
* **Mechanics:** The system never calls `kite.profile()` or `kite.margins()`. It is completely incapable of displaying account names, free cash balances, active margins, or account tiers to your father.

---

## Critical Verdict: Real vs. Mock Holdings

> [!CAUTION]
> **BRUTAL VERDICT:** Out-of-the-box, the system **DOES NOT fetch real Kite holdings**, even if your father completes the login flow!
> 
> * **The Disconnect:** `kite_sync.py` relies exclusively on `self._settings.kite_access_token` (which reads from the static `.env` file). 
> * **The Consequence:** Because it never queries the SQLite/PostgreSQL `broker_tokens` table for the dynamically saved OAuth token, the portfolio sync *fails* its check and **silently falls back to mock holdings** (`RELIANCE`, `TCS`, `INFY`, `HDFCBANK`, `ITC`).
> * **How to force real sync today:** You would have to manually extract the daily `access_token` from the database or terminal logs and hardcode it into the `.env` file under `KITE_ACCESS_TOKEN` every single morning.
