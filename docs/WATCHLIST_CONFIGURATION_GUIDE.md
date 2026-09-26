# WATCHLIST CONFIGURATION GUIDE (v4.0.2)

## Watchlist Sources
- Database watchlists take priority.
- If no DB watchlist exists, WATCHLIST_SYMBOLS from .env is used.

## Default Watchlist
Created by migration:
- name: default
- symbols: RELIANCE,TCS,INFY,HDFCBANK,NIFTY
- scan_interval_minutes: 3

## Configure via API
Endpoint: PUT /api/v1/scanner/watchlist

Example: NIFTY50
```bash
curl -X PUT http://localhost:8000/api/v1/scanner/watchlist \
  -H "Content-Type: application/json" \
  -d '{
    "name": "nifty50",
    "symbols": ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK"],
    "scan_interval_minutes": 5,
    "is_active": true
  }'
```

Example: BANKNIFTY
```bash
curl -X PUT http://localhost:8000/api/v1/scanner/watchlist \
  -H "Content-Type: application/json" \
  -d '{
    "name": "banknifty",
    "symbols": ["HDFCBANK","ICICIBANK","KOTAKBANK","AXISBANK","SBIN"],
    "scan_interval_minutes": 3,
    "is_active": true
  }'
```

Example: Favorites
```bash
curl -X PUT http://localhost:8000/api/v1/scanner/watchlist \
  -H "Content-Type: application/json" \
  -d '{
    "name": "favorites",
    "symbols": ["RELIANCE","INFY","LT"],
    "scan_interval_minutes": 10,
    "is_active": true
  }'
```

## Select Watchlist for Scan
- Sync scan: POST /api/v1/scanner/run with {"watchlist_name": "nifty50"}
- Async scan: POST /api/v1/scanner/run with {"async_job": true, "watchlist_name": "nifty50"}

## Notes
- Use uppercase symbols.
- scan_interval_minutes is per watchlist for scheduler usage.
- The scheduler uses the default watchlist when no name is provided.
