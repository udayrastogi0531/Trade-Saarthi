import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_ohlcv() -> pd.DataFrame:
  n = 120
  end = datetime.utcnow()
  timestamps = [end - timedelta(minutes=15 * i) for i in range(n)][::-1]
  rng = np.random.default_rng(42)
  closes = 1000 * np.cumprod(1 + rng.normal(0, 0.002, n))
  opens = np.roll(closes, 1)
  opens[0] = 1000
  highs = np.maximum(opens, closes) * 1.002
  lows = np.minimum(opens, closes) * 0.998
  volumes = rng.integers(100_000, 300_000, n).astype(float)
  return pd.DataFrame(
    {
      "timestamp": timestamps,
      "open": opens,
      "high": highs,
      "low": lows,
      "close": closes,
      "volume": volumes,
    }
  )
