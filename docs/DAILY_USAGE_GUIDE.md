# DAILY USAGE GUIDE (v4.0.2)

## Daily Startup (Ops)
1. Ensure Postgres + Redis are running.
2. Ensure API is running.
3. Start Celery worker + beat (or use Docker Compose).
4. Confirm PAPER_TRADING=true and EXECUTION_ENABLED=false.

## Run Scans
- Manual scan:
```bash
curl -X POST http://localhost:8000/api/v1/scanner/run \
  -H "Content-Type: application/json" \
  -d '{"watchlist_name": "default"}'
```
- Queue scan:
```bash
curl -X POST http://localhost:8000/api/v1/scanner/run \
  -H "Content-Type: application/json" \
  -d '{"watchlist_name": "default", "async_job": true}'
```

## Copilot Usage
- Web UI: /copilot
- Ask questions in English, Hindi, or Hinglish.
- Example prompts:
  - "Nifty trend kya hai?"
  - "Aaj best setup konsa hai?"
  - "Risky trades kaunse hain?"
  - "Open signals batao."

## Voice Usage
- Voice chat endpoint: POST /api/v1/copilot/voice/chat
- Requires STT provider configured (GROQ or DEEPGRAM).
- TTS defaults to gTTS; ElevenLabs optional.

## Alerts
- Telegram alerts for top setups when TELEGRAM_ENABLED=true.
- WebSocket alerts broadcast to /copilot UI.
- Voice alerts for top setup when VOICE_ALERTS_ENABLED=true.

## Safety Practices
- Keep paper trading on by default.
- Use conservative thresholds (CONSERVATIVE_MODE=true).
- Monitor data quality at /api/v1/observability/health.

## Health Checks
- /api/v1/health
- /api/v1/scanner/health
- /api/v1/observability/health
