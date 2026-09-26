# FINAL KITE SETUP GUIDE (v4.0.2)

## Prerequisites
- KITE_API_KEY
- KITE_API_SECRET
- kiteconnect installed (included in requirements.txt)

## Step 1: Configure .env
Set:
- KITE_API_KEY
- KITE_API_SECRET
- MARKET_DATA_PROVIDER=kite (after token saved)

## Step 2: Get login URL
Call:
- GET /api/v1/broker/kite/login-url

Open the returned login_url in a browser.

## Step 3: Callback
Kite redirects to the registered app callback with request_token.
The platform callback endpoint is:
- GET /api/v1/broker/kite/callback?request_token=...

This stores access token in DB. No manual token copy needed.

## Step 4: Validate
- GET /api/v1/broker/kite/status
- /api/v1/health/config

## Notes
- Access token is stored in DB and used by market data provider.
- Keep EXECUTION_ENABLED=false and PAPER_TRADING=true.
