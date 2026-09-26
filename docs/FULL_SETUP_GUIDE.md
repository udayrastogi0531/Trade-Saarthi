# FULL SETUP GUIDE (v4.0.2)

## 1) Configure .env
Use [docs/FINAL_WORKING_ENV_TEMPLATE.md](FINAL_WORKING_ENV_TEMPLATE.md) or .env.example.

## 2) Start core services
```bash
docker compose up -d
```

## 3) Start API (if not using Docker)
```bash
uvicorn backend.app.main:app --reload --port 8000
```

## 4) Start frontend
```bash
cd frontend/web
npm run dev
```

## 5) Verify health
- http://localhost:8000/api/v1/health
- http://localhost:8000/api/v1/health/config
- http://localhost:8000/api/v1/scanner/health

## 6) Optional: Kite login flow
1. Set KITE_API_KEY and KITE_API_SECRET in .env.
2. Open login URL: GET /api/v1/broker/kite/login-url
3. Complete login and allow redirect to callback endpoint.
4. Token is stored in DB. Set MARKET_DATA_PROVIDER=kite.

## 7) Optional: Telegram alerts
Set TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED=true.

## 8) Optional: Voice
Set STT/TTS providers and keys if not using Groq + gTTS defaults.
