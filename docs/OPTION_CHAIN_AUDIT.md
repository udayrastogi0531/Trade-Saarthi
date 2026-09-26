# Option Chain Audit

This report audits the Option Chain Engine to check the source of strike chains, Open Interest (OI), Put-Call Ratio (PCR), Implied Volatility (IV), and Options Greeks.

---

## Technical Audit Parameters

### 1. Data Source
* **Primary Source:** **NONE.** The engine does not connect to any exchange, scraper, or broker for options data.
* **Input Origin:** Binds to `backend/app/modules/market_data/option_chain.py` [L74-80](file:///d:/AI%20Trading/backend/app/modules/market_data/option_chain.py#L74-L80). It receives a ticker's spot price (from Yahoo Finance or Kite) and generates a synthetic matrix of 11 strikes (ATM, 5 ITM, 5 OTM) based on a strike step-size heuristic.

### 2. Open Interest (OI) & PCR
* **OI Generation:** Simulated mathematically using a Gaussian decay curve centered around the ATM strike to mirror a real option chain's bell curve. Uses a deterministic random number generator:
  ```python
  c_oi_factor = np.exp(-((s - (atm_strike + interval)) / (3 * interval))**2)
  c_oi = int(c_oi_factor * rng.integers(100_000, 1_000_000))
  ```
* **PCR (Put-Call Ratio):** Calculated directly from simulated Open Interest: `total_put_oi / total_call_oi`.

### 3. Implied Volatility (IV)
* **IV Modeling:** Synthesized using a fixed daily volatility assumption of `1.5%` scaled by the square root of time (`* 15.8` to annualize) and adjusted for strike skew:
  ```python
  base_iv = daily_volatility_pct * 15.8
  c_iv = base_iv * (1.0 + (s - spot_price) / spot_price * 0.5)
  ```

### 4. Options Greeks
* **Greeks Logic:** Fully implemented standard Black-Scholes equations for:
  * **Delta:** (`call_delta = nd1`, `put_delta = nd1 - 1.0`)
  * **Theta:** Full decay formulas for calls and puts divided by 365 days.
  * **Gamma & Vega:** Mathematically calculated via standard Cumulative Normal and probability density functions.
* **The Reality:** While the mathematical formulas are real and correct, the inputs (IV, Strikes, fixed 30-day expiry, risk-free rate of `6.5%`) are **completely synthetic**.

---

## Verdict: Real or Simulated?

> [!CAUTION]
> **VERDICT:** **100% SYNTHETIC AND SIMULATED.**
> 
> The option chain page does not present real-world data. It is a mathematical model generated dynamically from the spot price.
> * **Risk:** Your father must **NEVER** use these Option Greeks, Support/Resistance zones, or PCR ratios for real trading. They are simulated representations designed for terminal UI popups and contain random numbers.
