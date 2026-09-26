# AI Trading Assistant Platform v4.0

Institutional-grade **quantitative trading intelligence** for Indian equities (NSE/BSE). v4 evolves the platform from feature-rich AI trading into a **validated, research-driven system** focused on survivability, statistical edge validation, execution reliability, and disciplined risk management.

See **[docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md)** for the full documentation set (final completion reports, audits, runbooks). For **operations and production readiness**, start at **[docs/MASTER_OPERATIONS_INDEX.md](docs/MASTER_OPERATIONS_INDEX.md)**. **Operating the platform:** [docs/OPERATION_MODE.md](docs/OPERATION_MODE.md). **Governance (frozen architecture):** [docs/FINAL_STABLE_RELEASE_CHARTER.md](docs/FINAL_STABLE_RELEASE_CHARTER.md) · [CONTRIBUTING.md](CONTRIBUTING.md).

> **Disclaimer:** This software is for educational and research purposes. It does not provide financial advice. Trading involves substantial risk of loss.

---

## Architecture (v2)

```
 Next.js (:3001)  │  Streamlit (:8501)
         └────────┴──────── REST
                    ▼
         FastAPI Gateway (:8000)
    /scanner /regime /analytics /chart /signals ...
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
 Celery Worker   APScheduler    Trading Pipeline
 (watchlist)     (dev fallback)     │
                    │    ┌──────────┼──────────┐
                    │    ▼          ▼          ▼
                    │  Regime   MTF Align  Signal Filter
                    │    │          │          │
                    └──► Strategy → Risk → AI → Telegram
                              │
                    PostgreSQL + Redis
```

### v4.0 — Quantitative Validation & Survivability

| Section | Capability |
|---------|------------|
| 1 | Walk-forward validation — OOS testing, overfitting & decay detection |
| 2 | Monte Carlo risk — ruin probability, drawdown distribution, stress tests |
| 3 | Portfolio intelligence — VaR, correlation, sector exposure, heatmaps |
| 4 | AI strategy research — evidence-driven setup/regime analysis |
| 5 | Execution validation — slippage, latency, partial fills simulation |
| 6 | Regime research — extended regimes, profitability heatmaps |
| 7 | Institutional analytics — Sharpe, Sortino, Calmar, MAE/MFE |
| 8 | Conservative signal filtering — stricter thresholds, fake breakout weighting |
| 9 | Data quality layer — stale/gap detection, blocks bad feeds |
| 10 | Observability — system health, execution quality, Grafana dashboard |
| 11 | Capital safety — sandbox/tiny_live/staged rollout, emergency shutdown |
| 12 | Adaptive learning — edge tracking, confidence recalibration |
| 13 | Security — optional API key auth, audit logs |

### Section 1 — Distributed Watchlist Scanner (v2.3)

| Capability | Detail |
|------------|--------|
| Parallel scan | Async semaphore, configurable concurrency |
| Full pipeline | Market data → TA → strategy → risk → AI → filter → structure → learning |
| DB watchlists | `PUT /api/v1/scanner/watchlist` |
| Redis queue | `POST /api/v1/scanner/run` with `"async_job": true` |
| Health API | `GET /api/v1/scanner/health` |
| Signal feed | `GET /api/v1/scanner/feed` |
| Alerts | Telegram digest + voice (top setup) + WebSocket |
| Workers | Celery beat + APScheduler fallback |

### v2.2 Institutional Intelligence

| Module | Path | Purpose |
|--------|------|---------|
| Market Structure | `modules/market_structure/` | BOS, CHOCH, liquidity sweeps, FVG, fake breakout risk |
| Learning Engine | `modules/learning/` | Setup performance memory, adaptive confidence |
| Intelligence Scanner | `modules/scanner/intelligence.py` | Retry, health tracking, structure-ranked scans |
| Briefings | `modules/briefings/` | Pre-market / intraday AI + voice reports |
| Execution Safety | `modules/execution/safety.py` | Cooldown, duplicates, volatility shutdown |
| Intelligence Panel | `GET /api/v1/intelligence/panel` | Live regime, heatmaps, rankings |

New APIs: `/intelligence/*`, `/briefings/*`, `/execution/safety-check`

### AI Copilot (v2.1)

| Feature | Endpoint |
|---------|----------|
| Chat | `POST /api/v1/copilot/chat` |
| Stream | `POST /api/v1/copilot/chat/stream` |
| Voice in/out | `POST /api/v1/copilot/voice/chat` |
| STT only | `POST /api/v1/copilot/voice/transcribe` |
| TTS only | `POST /api/v1/copilot/voice/synthesize` |
| WebSocket | `WS /api/v1/ws/copilot` |
| UI | http://localhost:3001/copilot |

Languages: **English**, **Hindi**, **Hinglish**. Voice via Groq Whisper + gTTS (or ElevenLabs).

### v2 Modules

| Module | Path | Purpose |
|--------|------|---------|
| Scanner | `modules/scanner/` | Parallel watchlist scan, ranking |
| MTF Analysis | `modules/mtf_analysis/` | 5m–1D weighted alignment |
| Market Regime | `modules/market_regime/` | Trending/ranging/choppy/volatile |
| Signal Filter | `modules/signal_filter/` | Quality scoring, false-positive reduction |
| Advanced Risk | `modules/risk/advanced.py` | ATR stops, sector limits, circuit breaker |
| Chart AI | `modules/chart_analysis/` | Screenshot structure analysis |
| Journal | `modules/journal/` | MFE/MAE, setup analytics |
| Advanced Backtest | `modules/backtesting/advanced.py` | Walk-forward, Monte Carlo |
| Celery | `workers/` | Scheduled distributed scans |

### Module Map

| Module | Path | Responsibility |
|--------|------|----------------|
| 1 — Market Data | `backend/app/modules/market_data/` | OHLCV, multi-TF, caching, Kite/mock providers |
| 2 — Technical Analysis | `backend/app/modules/technical_analysis/` | RSI, MACD, EMA, VWAP, ATR, BB, volume spikes |
| 3 — Strategy | `backend/app/modules/strategy/` | Setup detection, validation, trade rejection |
| 4 — Risk | `backend/app/modules/risk/` | Position sizing, daily loss, kill switch |
| 5 — AI Reasoning | `backend/app/modules/ai_reasoning/` | Groq/DeepSeek structured JSON explanations |
| 6 — Telegram | `backend/app/modules/telegram/` | Professional trade/rejection alerts |
| 7 — Dashboard | `frontend/dashboard/` | Streamlit dark UI starter |
| 8 — Backtesting | `backend/app/modules/backtesting/` | Walk-forward metrics |
| 9 — Paper Trading | `backend/app/modules/paper_trading/` | Simulated execution |
| 10 — Execution | `backend/app/modules/execution/` | Live orders (disabled by default) |

---

## Folder Structure

```
AI Trading/
├── backend/app/
│   ├── main.py                 # FastAPI entry
│   ├── config.py               # Environment settings
│   ├── api/routes/             # REST endpoints
│   ├── core/                   # Logging, exceptions
│   ├── db/                     # SQLAlchemy models + schema.sql
│   ├── modules/                # Trading engines (1–10)
│   ├── schemas/                # Pydantic models
│   └── services/               # Pipeline orchestration
├── frontend/dashboard/         # Streamlit UI
├── monitoring/                 # Prometheus + Grafana
├── tests/                      # Unit tests
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Quick Start (Docker)

### 1. Configure environment

```powershell
copy .env.example .env
```

Edit `.env` — at minimum keep `PAPER_TRADING=true` and `EXECUTION_ENABLED=false`.

Optional: set `GROQ_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_ENABLED=true`.

### 2. Start stack

```powershell
docker compose up -d --build
```

### 3. Access services

| Service | URL |
|---------|-----|
| API Docs | http://localhost:8000/docs |
| Dashboard (Streamlit) | http://localhost:8501 |
| Dashboard (Next.js) | http://localhost:3001 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin/admin) |

### 4. Analyze a signal

```powershell
curl -X POST http://localhost:8000/api/v1/signals/analyze `
  -H "Content-Type: application/json" `
  -d '{"symbol": "RELIANCE", "exchange": "NSE", "include_ai_reasoning": true}'
```

---

## Local Development (without Docker)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env

# Start PostgreSQL + Redis locally, then:
$env:PYTHONPATH = "."
uvicorn backend.app.main:app --reload --port 8000

# Dashboard (separate terminal)
streamlit run frontend/dashboard/app.py
```

Run tests:

```powershell
$env:PYTHONPATH = "."
pytest -v
```

---

## API Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/market/candles` | Fetch OHLCV |
| POST | `/api/v1/market/multi-timeframe` | Multi-TF data |
| POST | `/api/v1/signals/analyze` | Full trading pipeline |
| GET | `/api/v1/trades/` | List trades |
| GET | `/api/v1/trades/analytics` | Win rate, PnL, Sharpe |
| POST | `/api/v1/backtest/run` | Run backtest |
| POST | `/api/v1/risk/kill-switch` | Emergency halt |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/v1/scanner/run` | Run watchlist scanner |
| GET | `/api/v1/scanner/watchlist` | Configured symbols |
| POST | `/api/v1/regime/detect` | Market regime detection |
| GET | `/api/v1/analytics/journal` | Trade journal analytics |
| GET | `/api/v1/analytics/correlation` | Sector correlation heatmap |
| POST | `/api/v1/chart/analyze` | Upload chart for AI analysis |
| POST | `/api/v1/backtest/run` | Set `"advanced": true` for Monte Carlo |

---

## Database Schema

Tables: `accounts`, `risk_state`, `signals`, `trades`, `execution_logs`, `backtest_runs`, `alert_logs`.

See `backend/app/db/schema.sql` for full DDL.

---

## Trading Rules (Enforced)

- Minimum risk-reward **1:2** (configurable)
- Reject sideways / low-volatility markets
- Volume confirmation for breakouts
- Multi-timeframe trend alignment
- Max daily loss, drawdown, trades per day
- Kill switch for emergency halt
- **Paper trading ON** and **live execution OFF** by default

---

## Broker Integration

### Zerodha Kite

1. `pip install kiteconnect`
2. Set `MARKET_DATA_PROVIDER=kite`, `BROKER_MODE=kite`
3. Add `KITE_API_KEY`, `KITE_ACCESS_TOKEN`

---

## AI Configuration

```env
GROQ_API_KEY=your_key
GROQ_MODEL=llama-3.3-70b-versatile
AI_PROVIDER=groq
```

For DeepSeek R1:

```env
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key
```

Without API keys, the system uses a **deterministic fallback** — no hallucinated predictions.

---

## Telegram Alerts

```env
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

Example alert format:

```
BUY: RELIANCE
Entry: 2890 | SL: 2860 | Target: 2950
RR: 1:2.5 | Confidence: 81%
Reason: Strong breakout with volume confirmation...
```

---

## Enabling Live Trading (Advanced)

Only after thorough paper trading validation:

```env
PAPER_TRADING=false
EXECUTION_ENABLED=true
BROKER_MODE=kite
```

> Live trading can result in real financial loss. Use at your own risk.

---

## Monitoring

- **Prometheus** scrapes `/metrics` from the API
- **Grafana** provisioned with Prometheus datasource
- Structured JSON logs via `structlog`

---

## Production Checklist

- [ ] Change `SECRET_KEY`
- [ ] Set `APP_ENV=production`, `DEBUG=false`
- [ ] Restrict CORS origins
- [ ] Use managed PostgreSQL + Redis
- [ ] Enable TLS reverse proxy (nginx/traefik)
- [ ] Rotate API keys regularly
- [ ] Never commit `.env`
- [ ] Validate strategies via backtest + paper trading first

---

## License

Proprietary — use responsibly.
