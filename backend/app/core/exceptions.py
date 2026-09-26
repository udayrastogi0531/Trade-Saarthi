"""Domain-specific exceptions."""

from fastapi import HTTPException, status


class TradingPlatformError(Exception):
  """Base platform exception."""

  def __init__(self, message: str, code: str = "PLATFORM_ERROR"):
    self.message = message
    self.code = code
    super().__init__(message)


class RiskLimitExceeded(TradingPlatformError):
  """Risk engine blocked the action."""

  def __init__(self, message: str):
    super().__init__(message, code="RISK_LIMIT_EXCEEDED")


class TradeRejected(TradingPlatformError):
  """Strategy or validation rejected the trade."""

  def __init__(self, message: str, reasons: list[str] | None = None):
    self.reasons = reasons or []
    super().__init__(message, code="TRADE_REJECTED")


class MarketDataError(TradingPlatformError):
  def __init__(self, message: str):
    super().__init__(message, code="MARKET_DATA_ERROR")


def http_exception_from_domain(exc: TradingPlatformError) -> HTTPException:
  status_map = {
    "RISK_LIMIT_EXCEEDED": status.HTTP_403_FORBIDDEN,
    "TRADE_REJECTED": status.HTTP_422_UNPROCESSABLE_ENTITY,
    "MARKET_DATA_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
  }
  return HTTPException(
    status_code=status_map.get(exc.code, status.HTTP_400_BAD_REQUEST),
    detail={"code": exc.code, "message": exc.message},
  )
