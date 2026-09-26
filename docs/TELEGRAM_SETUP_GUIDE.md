# TELEGRAM SETUP GUIDE (v4.0.2)

## Required Environment Variables
Set in `.env`:
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- TELEGRAM_ENABLED=true

## Behavior
- Scanner alerts: top approved setups in a digest.
- Rejection alerts: blocked setups with reasons (when used by pipelines).

## Where Alerts Are Triggered
- Scanner pipeline dispatch: [backend/app/services/scanner_service.py](../backend/app/services/scanner_service.py)
- Telegram engine: [backend/app/modules/telegram/engine.py](../backend/app/modules/telegram/engine.py)

## Quick Validation
1. Set TELEGRAM_* and TELEGRAM_ENABLED=true.
2. Trigger a scan:
```bash
curl -X POST http://localhost:8000/api/v1/scanner/run \
  -H "Content-Type: application/json" \
  -d '{"watchlist_name": "default"}'
```
3. Confirm messages arrive in the configured chat.

## Safety
Alerts are advisory only and include disclaimers. Live execution remains disabled by default.
