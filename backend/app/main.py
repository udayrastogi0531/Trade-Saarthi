"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from starlette.responses import Response

from backend.app import __version__
from backend.app.api.routes import (
  analytics,
  backtest,
  briefings,
  chart,
  copilot,
  broker,
  execution,
  health,
  intelligence,
  market,
  observability,
  paper,
  portfolio,
  regime,
  research,
  risk,
  scanner,
  signals,
  trades,
  validation,
)
from backend.app.api.ws import copilot_ws
from backend.app.config import get_settings
from backend.app.core.exceptions import TradingPlatformError, http_exception_from_domain
from backend.app.core.logging import setup_logging

REQUEST_COUNT = Counter("trading_api_requests_total", "Total API requests", ["method", "endpoint"])


@asynccontextmanager
async def lifespan(app: FastAPI):
  settings = get_settings()
  setup_logging(debug=settings.debug)
  scheduler = None
  if settings.scanner_enabled and settings.app_env == "development":
    try:
      from apscheduler.schedulers.asyncio import AsyncIOScheduler

      from backend.app.services.scanner_scheduler import run_scheduled_scan

      scheduler = AsyncIOScheduler()
      scheduler.add_job(
        run_scheduled_scan,
        "interval",
        minutes=settings.scanner_interval_minutes,
        id="watchlist_scan",
      )
      scheduler.start()
    except Exception:
      pass
  yield
  if scheduler:
    scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
  settings = get_settings()

  app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
      "Institutional-grade AI Trading Assistant — probability-based execution, "
      "strict risk management, and explainable AI reasoning. Not financial advice."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
  )

  app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [
      "http://localhost:8501",
      "http://localhost:3000",
      "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
  )

  prefix = settings.api_prefix
  app.include_router(health.router, prefix=prefix)
  app.include_router(market.router, prefix=prefix)
  app.include_router(signals.router, prefix=prefix)
  app.include_router(risk.router, prefix=prefix)
  app.include_router(backtest.router, prefix=prefix)
  app.include_router(trades.router, prefix=prefix)
  app.include_router(scanner.router, prefix=prefix)
  app.include_router(analytics.router, prefix=prefix)
  app.include_router(chart.router, prefix=prefix)
  app.include_router(broker.router, prefix=prefix)
  app.include_router(regime.router, prefix=prefix)
  app.include_router(copilot.router, prefix=prefix)
  app.include_router(copilot_ws.router, prefix=prefix)
  app.include_router(intelligence.router, prefix=prefix)
  app.include_router(briefings.router, prefix=prefix)
  app.include_router(execution.router, prefix=prefix)
  app.include_router(validation.router, prefix=prefix)
  app.include_router(portfolio.router, prefix=prefix)
  app.include_router(research.router, prefix=prefix)
  app.include_router(observability.router, prefix=prefix)
  app.include_router(paper.router, prefix=prefix)

  @app.exception_handler(TradingPlatformError)
  async def trading_error_handler(_: Request, exc: TradingPlatformError) -> JSONResponse:
    http_exc = http_exception_from_domain(exc)
    return JSONResponse(status_code=http_exc.status_code, content=http_exc.detail)

  @app.middleware("http")
  async def metrics_middleware(request: Request, call_next):
    response = await call_next(request)
    if settings.prometheus_enabled:
      REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    return response

  if settings.prometheus_enabled:

    @app.get("/metrics")
    async def metrics() -> Response:
      return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

  @app.get("/")
  async def root() -> dict:
    return {
      "name": settings.app_name,
      "version": __version__,
      "docs": "/docs",
      "api": settings.api_prefix,
      "disclaimer": "This platform does not guarantee profits. Trade at your own risk.",
    }

  return app


app = create_app()
