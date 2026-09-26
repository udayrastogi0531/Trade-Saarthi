# Free Provider Setup Guide — Yahoo Finance (yfinance)

This guide details how to configure the **Yahoo Finance (yfinance)** free market data provider for the platform.

## Configuration Settings

To activate the free `yfinance` provider, update your `.env` file with:

```env
MARKET_DATA_PROVIDER=yfinance
```

## Symbol Mapping

The platform automatically handles standard symbol translation for Indian indices and equities:

* **Equities (NSE):** `RELIANCE` automatically maps to `RELIANCE.NS`.
* **Equities (BSE):** Mapped to `SYMBOL.BO`.
* **Indices:** Mapped to standard ticker codes:
  * `NIFTY` -> `^NSEI`
  * `BANKNIFTY` -> `^NSEBANK`
  * `SENSEX` -> `^BSESN`

## Advantages

* **No Cost:** Completely free; does not require paid Zerodha Kite API access.
* **No Authentication:** Does not require access token renewal routines.
* **Coverage:** Access to standard candles (`1m`, `5m`, `15m`, `1h`, `1d`). Non-standard intervals like `4h` are automatically resampled from `1h` candles.
