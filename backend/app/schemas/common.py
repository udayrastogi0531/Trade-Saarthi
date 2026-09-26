from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class HealthResponse(BaseModel):
  status: str = "ok"
  version: str
  environment: str
  paper_trading: bool
  execution_enabled: bool


class PaginatedResponse(BaseModel, Generic[T]):
  items: list[T]
  total: int
  page: int = 1
  page_size: int = Field(default=20, le=100)
