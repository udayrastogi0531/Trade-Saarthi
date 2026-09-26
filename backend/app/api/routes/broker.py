"""Broker integration routes (Kite OAuth and status)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.db.session import get_db
from backend.app.services.broker_tokens import BrokerTokenService

router = APIRouter(prefix="/broker", tags=["Broker"])


@router.get("/kite/login-url")
async def kite_login_url() -> dict:
  settings = get_settings()
  if not settings.kite_api_key or not settings.kite_api_secret:
    raise HTTPException(status_code=400, detail="Kite API key/secret not configured")
  try:
    from kiteconnect import KiteConnect
  except ImportError as exc:
    raise HTTPException(status_code=500, detail="kiteconnect package not installed") from exc

  kite = KiteConnect(api_key=settings.kite_api_key)
  return {"login_url": kite.login_url()}


@router.get("/kite/callback")
async def kite_callback(
  request_token: str = Query(...),
  status: str | None = Query(None),
  db: AsyncSession = Depends(get_db),
) -> dict:
  settings = get_settings()
  if not settings.kite_api_key or not settings.kite_api_secret:
    raise HTTPException(status_code=400, detail="Kite API key/secret not configured")
  try:
    from kiteconnect import KiteConnect
  except ImportError as exc:
    raise HTTPException(status_code=500, detail="kiteconnect package not installed") from exc

  kite = KiteConnect(api_key=settings.kite_api_key)
  try:
    session = kite.generate_session(request_token, api_secret=settings.kite_api_secret)
  except Exception as exc:
    raise HTTPException(status_code=400, detail=f"Kite token exchange failed: {exc}") from exc

  access_token = session.get("access_token")
  if not access_token:
    raise HTTPException(status_code=400, detail="Kite access token missing in response")

  metadata = {
    "user_id": session.get("user_id"),
    "login_time": session.get("login_time"),
    "status": status,
  }
  await BrokerTokenService().save_token(db, "kite", access_token, metadata=metadata)
  await db.commit()

  return {
    "status": "ok",
    "token_saved": True,
    "user_id": session.get("user_id"),
    "note": "Access token stored. Set MARKET_DATA_PROVIDER=kite and BROKER_MODE=kite if needed.",
  }


@router.get("/kite/status")
async def kite_status(db: AsyncSession = Depends(get_db)) -> dict:
  settings = get_settings()
  token = await BrokerTokenService().get_latest(db, "kite")
  return {
    "kite_configured": bool(settings.kite_api_key and settings.kite_api_secret),
    "token_in_db": token is not None,
    "market_data_provider": settings.market_data_provider,
    "broker_mode": settings.broker_mode,
  }
