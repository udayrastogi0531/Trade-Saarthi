# FINAL SETUP GUIDE (v4.0.2)

## Required
- GROQ_API_KEY: Required for AI reasoning and copilot responses. If missing, AI routes return errors and AI-enhanced UI panels show empty/error states.
- PostgreSQL: Required for persistence (signals, journals, research artifacts). If missing, APIs that read/write persistent data fail.
- Redis: Required for queues, scanner coordination, and websocket/session reliability. If missing, scanner and realtime services degrade or fail.

## Optional
- TELEGRAM_BOT_TOKEN: Enables Telegram alert delivery.
- TELEGRAM_CHAT_ID: Target chat for alerts. Must be paired with TELEGRAM_BOT_TOKEN.
- KITE_API_KEY: Enables broker connectivity for Kite integrations.
- KITE_API_SECRET: Required for Kite OAuth token exchange.
- KITE_ACCESS_TOKEN: Required with KITE_API_KEY for authenticated broker calls (optional if stored via callback).
- DEEPGRAM_API_KEY: Enables speech-to-text for voice copilot features.
- ELEVENLABS_API_KEY: Enables text-to-speech voice responses.

## Feature Dependencies
- Copilot voice: Requires DEEPGRAM_API_KEY for speech-to-text and ELEVENLABS_API_KEY for speech synthesis.
- Telegram alerts: Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.
- Broker execution: Requires KITE_API_KEY and KITE_ACCESS_TOKEN; without these, UI remains in paper-first mode.
- Core research/scanner: Requires PostgreSQL and Redis for reliable operation.

## Fallback Behavior
- Missing AI keys: UI still renders, but AI responses and analysis panels will return errors or empty responses.
- Missing Redis: Scanner queues and websocket reliability degrade; UI shows operational alerts if available.
- Missing PostgreSQL: Research and journal data cannot be stored; UI shows API errors.

## Local Setup
1. Set required environment variables in your shell or .env file.
2. Ensure PostgreSQL and Redis are running.
3. Frontend runs against NEXT_PUBLIC_API_URL (defaults to http://localhost:8000).

## Production Setup
1. Set GROQ_API_KEY, PostgreSQL, and Redis in the production secret store.
2. Set optional integrations as needed.
3. Verify API health at /api/v1/health and /api/v1/observability/health.
