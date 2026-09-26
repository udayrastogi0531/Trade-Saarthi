# Option Chain Integration & Transparency Report

This report documents the status of options chain integrations, derivatives PCR and open interest calculations, and the safety measures taken to prevent misleading options assumptions.

---

## ⚙️ Derivatives Modeling & Greeks Solver

Because real-time, tick-by-tick options chains are highly premium data feeds and contain restricted exchange subscription requirements, the system leverages a **hybrid synthetic options chain solver** inside `backend/app/modules/market_data/option_chain.py` to allow simulated sandbox studies and capital safety alerts:

### 1. Strikes Selection Matrix
* **Logic:** ATM Strike is dynamically resolved based on the underlying stock spot price. Generates a symmetrical grid of 11 strikes (ATM, 5 Out-of-the-Money ITM/OTM calls and puts) based on a strike step-size heuristic.

### 2. Gaussian Open Interest & IV skew
* **Logic:** Open Interest (OI) and Change in OI are calculated dynamically using normal Gaussian distribution curves centered around the ATM strike to mirror real option chain distributions. Implied Volatility (IV) is simulated via localized strike-skew annualizations:
  ```python
  rng = np.random.default_rng(hash(symbol) % 2**32)
  c_oi_factor = np.exp(-((s - (atm_strike + interval)) / (3 * interval))**2)
  c_oi = int(c_oi_factor * rng.integers(100_000, 1_000_000))
  ```

### 3. Cumulative Black-Scholes Solvers
* **Logic:** Standard Black-Scholes solvers dynamically calculate option Greeks (Delta, Theta, Gamma, Vega) for both calls and puts using math solvers (`math.erf` to resolve normal cumulative probability):
  ```python
  d1 = (math.log(s / k) + (r + 0.5 * iv_dec**2) * t) / (iv_dec * math.sqrt(t))
  call_delta = nd1
  put_delta = nd1 - 1.0
  ```

---

## 🛡️ Honesty Labeling & st.warning Banners

To ensure your father is fully aware that options Greeks are synthetically simulated and is protected against severe derivatives capital risk, we successfully injected:

1. **API Metadata Entry:** Binds `"is_synthetic": True` and `"disclaimer"` in the option chain dictionary.
2. **Dashboard Visual Banner:** Upgraded the Streamlit dashboard in `frontend/dashboard/app.py` [L467-470](file:///d:/AI%20Trading/frontend/dashboard/app.py#L467-L470) to listen for this metadata and output a prominent orange warning card:
   > ⚠️ **DISCLAIMER:** *This options chain and its Greeks are synthetically modeled from stock spot prices for capital safety simulations. Do NOT execute real options contracts on these simulated parameters.*
