from backend.app.services.trading_pipeline import TradingPipeline

_pipeline: TradingPipeline | None = None


def get_pipeline() -> TradingPipeline:
  global _pipeline
  if _pipeline is None:
    _pipeline = TradingPipeline()
  return _pipeline
