"""API authentication — optional API key + RBAC roles."""

from enum import Enum

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from backend.app.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class Role(str, Enum):
  VIEWER = "viewer"
  TRADER = "trader"
  ADMIN = "admin"


ROLE_PERMISSIONS: dict[Role, set[str]] = {
  Role.VIEWER: {"read"},
  Role.TRADER: {"read", "trade", "scan"},
  Role.ADMIN: {"read", "trade", "scan", "execute", "admin"},
}


def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
  settings = get_settings()
  if not settings.api_auth_enabled:
    return "anonymous"
  if not settings.api_key:
    raise HTTPException(status_code=503, detail="API auth enabled but no key configured")
  if api_key != settings.api_key:
    raise HTTPException(status_code=401, detail="Invalid API key")
  return "api_user"


def require_permission(role: Role, permission: str) -> None:
  if permission not in ROLE_PERMISSIONS.get(role, set()):
    raise HTTPException(status_code=403, detail=f"Permission denied: {permission}")
