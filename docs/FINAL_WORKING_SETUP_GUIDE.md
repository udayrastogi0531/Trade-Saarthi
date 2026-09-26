# FINAL WORKING SETUP GUIDE (v4.0.2)

## Minimal steps
1. Copy .env and fill required keys.
2. docker compose up -d
3. npm run dev (frontend/web)

## Required keys
- GROQ_API_KEY
- DATABASE_URL
- REDIS_URL

## Optional keys
- TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
- KITE_API_KEY, KITE_API_SECRET (for live data)
- DEEPGRAM_API_KEY (optional STT)
- ELEVENLABS_API_KEY (optional TTS)

## Health checks
- /api/v1/health
- /api/v1/health/config
- /api/v1/scanner/health
