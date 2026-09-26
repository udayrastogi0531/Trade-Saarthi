# OPERATIONAL AGENT SETUP (v4.0.2)

## Scope
Operationalize existing agent workflows using current configuration and infrastructure only. No new modules or architecture changes.

## Core Environment Defaults
Set in `.env` based on [.env.example](../.env.example):

- EXECUTION_ENABLED=false
- PAPER_TRADING=true
- CONSERVATIVE_MODE=true
- SCANNER_ENABLED=true
- SCANNER_INTERVAL_MINUTES=3
- SCANNER_MIN_CONFIDENCE=70
- MIN_SIGNAL_QUALITY_SCORE=72
- SIGNAL_CONFIDENCE_THRESHOLD=78
- WATCHLIST_SYMBOLS=RELIANCE,TCS,INFY,HDFCBANK,NIFTY
- TELEGRAM_ENABLED=false (enable when configured)
- COPILOT_ENABLED=true
- COPILOT_DEFAULT_LANGUAGE=hinglish
- STT_PROVIDER=groq (or deepgram)
- TTS_PROVIDER=gtts (or elevenlabs)
- VOICE_ALERTS_ENABLED=true

## Scheduler Modes
- Production: Celery beat + worker schedule scans and queue processing.
- Development: APScheduler fallback runs watchlist scans when APP_ENV=development.

Celery schedules are defined in [backend/app/workers/celery_app.py](../backend/app/workers/celery_app.py).

## Scanner Workflow
- Scheduled scans use the default watchlist name "default".
- Watchlist symbols are read from DB if present; fallback to WATCHLIST_SYMBOLS.
- Alerts are dispatched via Telegram, voice, and WebSocket when enabled.

Key implementations:
- Scheduler runner: [backend/app/services/scanner_scheduler.py](../backend/app/services/scanner_scheduler.py)
- Scanner orchestrator: [backend/app/services/scanner_service.py](../backend/app/services/scanner_service.py)
- Watchlist service: [backend/app/modules/scanner/watchlist_service.py](../backend/app/modules/scanner/watchlist_service.py)

## Safety Defaults (Paper-First)
- Live execution is blocked when PAPER_TRADING=true or EXECUTION_ENABLED=false.
- Execution safety uses cooldowns, duplicate windows, and volatility shutdown.

Key modules:
- Safety engine: [backend/app/modules/execution/safety.py](../backend/app/modules/execution/safety.py)
- Execution engine (live): [backend/app/modules/execution/engine.py](../backend/app/modules/execution/engine.py)

## Copilot and Voice
- Copilot WebSocket: WS /api/v1/ws/copilot
- Copilot voice: POST /api/v1/copilot/voice/chat
- STT and TTS providers selected via env.

## Operational Checklist
- Redis and Postgres running.
- Celery worker + beat running (or APScheduler dev fallback).
- TELEGRAM_* configured if alerts are required.
- GROQ_API_KEY (or DEEPSEEK_API_KEY) set for AI reasoning.
