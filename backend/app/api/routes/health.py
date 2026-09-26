from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app import __version__
from backend.app.config import get_settings
from backend.app.db.session import get_db
from backend.app.services.broker_tokens import BrokerTokenService
from backend.app.services.redis_client import get_redis
from backend.app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
  settings = get_settings()
  return HealthResponse(
    status="ok",
    version=__version__,
    environment=settings.app_env,
    paper_trading=settings.paper_trading,
    execution_enabled=settings.execution_enabled,
  )


@router.get("/health/config")
async def health_config(db: AsyncSession = Depends(get_db)) -> dict:
  settings = get_settings()
  redis_ok = await get_redis() is not None
  kite_token = await BrokerTokenService().get_latest(db, "kite")
  return {
    "ai_provider": settings.ai_provider,
    "groq_configured": bool(settings.groq_api_key),
    "telegram_configured": bool(settings.telegram_bot_token and settings.telegram_chat_id),
    "telegram_enabled": settings.telegram_enabled,
    "kite_configured": bool(settings.kite_api_key and settings.kite_api_secret),
    "kite_token_in_db": kite_token is not None,
    "market_data_provider": settings.market_data_provider,
    "broker_mode": settings.broker_mode,
    "redis_ok": redis_ok,
    "scanner_enabled": settings.scanner_enabled,
    "scanner_interval_minutes": settings.scanner_interval_minutes,
    "paper_trading": settings.paper_trading,
    "execution_enabled": settings.execution_enabled,
  }
