# FINAL AI TRADING AGENT SETUP

This document explains what is required vs optional, what is used, and how the platform operates.

====================================================
CORE STACK USED
====================================================

Frontend:
- Next.js
- React
- TypeScript
- TailwindCSS

Backend:
- Python
- FastAPI
- Celery
- Redis
- PostgreSQL

AI:
- Groq API (primary AI reasoning)
- Whisper STT via Groq
- Optional local Ollama support (not required)

Infrastructure:
- Docker
- Prometheus
- Grafana

====================================================
YES - PYTHON IS USED HEAVILY
====================================================

Python is the main backend engine. It handles:
- market analysis
- scanner workflows
- AI orchestration
- risk engine
- regime detection
- backtesting
- learning engine
- Celery workers
- APIs
- websocket server
- operational workflows

Main backend: backend/app/
FastAPI server: backend/app/main.py

====================================================
GROQ API - MAIN AI ENGINE
====================================================

Groq is the primary AI provider. Used for:
- AI copilot
- market reasoning
- Hindi/Hinglish chat
- signal explanations
- AI summaries
- Whisper speech-to-text
- voice workflows

Required:
- GROQ_API_KEY

Example:
GROQ_API_KEY=gsk_xxxxxxxxx

Recommended models:
- llama-3.3-70b-versatile
- deepseek-r1-distill-llama-70b

====================================================
OLLAMA - OPTIONAL
====================================================

Ollama is not required. It can be used for:
- local/private inference
- backup AI provider
- offline experimentation

Recommendation:
Use Groq only for now. Do not complicate the stack initially.

====================================================
REQUIRED INFRASTRUCTURE
====================================================

1) PostgreSQL
Purpose:
- trade history
- journals
- scorecards
- learning data
- research reports
- operational state
Required: YES

2) Redis
Purpose:
- websocket pub/sub
- Celery queues
- caching
- scanner queues
- operational workflows
Required: YES

3) Docker
Purpose:
- run full stack easily
- Redis
- PostgreSQL
- monitoring
- backend services
Required: STRONGLY RECOMMENDED

====================================================
REQUIRED ENVIRONMENT VARIABLES
====================================================

Minimum required:
- GROQ_API_KEY=
- DATABASE_URL=
- REDIS_URL=

====================================================
OPTIONAL APIS
====================================================

1) Telegram Alerts
Optional
- TELEGRAM_BOT_TOKEN=
- TELEGRAM_CHAT_ID=
Used for alerts, signals, operational notifications.

2) Kite/Zerodha
Optional
- KITE_API_KEY=
- KITE_API_SECRET=
- KITE_ACCESS_TOKEN= (optional if stored via callback)
Used for live NSE market data and broker integration.
Token flow endpoints:
- GET /api/v1/broker/kite/login-url
- GET /api/v1/broker/kite/callback?request_token=...

3) Deepgram
Optional
- DEEPGRAM_API_KEY=
Used for advanced speech-to-text.

4) ElevenLabs
Optional
- ELEVENLABS_API_KEY=
Used for premium voice output.

====================================================
WHAT THE AI AGENT ACTUALLY DOES
====================================================

Flow:
User asks: "Nifty trend kya hai?"

Agent:
1. fetches market data
2. runs scanner
3. checks structure
4. checks regime
5. validates risk
6. calculates confidence
7. generates AI reasoning
8. explains result
9. sends alerts if needed

====================================================
HOW TO RUN THE SYSTEM
====================================================

1) Configure .env
2) Start Docker stack:
   docker compose up -d
3) Start frontend:
   cd frontend/web
   npm run dev

====================================================
MAIN URLS
====================================================

Research:
http://localhost:3000/research

Copilot:
http://localhost:3000/copilot

Intelligence:
http://localhost:3000/intelligence

API Docs:
http://localhost:8000/docs

Grafana:
http://localhost:3001

====================================================
IMPORTANT SAFETY RULE
====================================================

Keep:
EXECUTION_ENABLED=false

Until:
- long paper validation
- stable performance
- low drawdowns
- operational confidence

====================================================
FINAL RECOMMENDATION
====================================================

Use:
- Groq
- PostgreSQL
- Redis
- Docker

Only. Do not complicate the system with:
- Ollama
- local LLMs
- unnecessary AI providers
- architecture rewrites

Focus on:
- validation
- discipline
- operational usage
- helping your father trade systematically
