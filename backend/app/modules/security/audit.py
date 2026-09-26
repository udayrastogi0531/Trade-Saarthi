"""Audit logging for sensitive operations."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.db.models import AuditLog


class AuditLogger:
  @staticmethod
  async def log(
    db: AsyncSession,
    action: str,
    actor: str = "system",
    resource: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
  ) -> None:
    if not get_settings().audit_log_enabled:
      return
    db.add(
      AuditLog(
        actor=actor,
        action=action,
        resource=resource,
        details=details,
        ip_address=ip_address,
      )
    )
    await db.flush()
