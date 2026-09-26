# Final Provider Configuration

## Supported Providers
- Live broker execution: Zerodha Kite.
- Market data providers: Kite (live) and mock (development/testing).

## Environment Configuration
- BROKER_MODE: paper | kite
- MARKET_DATA_PROVIDER: mock | kite

Kite credentials:
- KITE_API_KEY
- KITE_API_SECRET
- KITE_ACCESS_TOKEN (optional if stored via callback)

## Kite OAuth Flow
- GET /api/v1/broker/kite/login-url
- GET /api/v1/broker/kite/callback?request_token=...

Tokens are stored in the broker token table and used automatically when MARKET_DATA_PROVIDER=kite.

## Notes
- Angel One is not supported.
- No yfinance provider is wired in this release; use the mock provider for offline testing.
