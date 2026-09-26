"""Broker token persistence for OAuth-based brokers."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import BrokerToken


class BrokerTokenService:
  async def save_token(
    self,
    db: AsyncSession,
    broker: str,
    access_token: str,
    account_id: int | None = 1,
    metadata: dict | None = None,
  ) -> BrokerToken:
    row = BrokerToken(
      broker=broker,
      account_id=account_id,
      access_token=access_token,
      metadata_=metadata,
      created_at=datetime.utcnow(),
      updated_at=datetime.utcnow(),
    )
    db.add(row)
    await db.flush()
    return row

  async def get_latest(
    self,
    db: AsyncSession,
    broker: str,
    account_id: int | None = 1,
  ) -> BrokerToken | None:
    result = await db.execute(
      select(BrokerToken)
      .where(BrokerToken.broker == broker, BrokerToken.account_id == account_id)
      .order_by(BrokerToken.created_at.desc())
      .limit(1)
    )
    return result.scalar_one_or_none()
