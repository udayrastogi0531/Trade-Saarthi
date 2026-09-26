# Option Chain Provider Integration Audit

This report audits the data source origin for option strikes, Open Interest (OI), Put-Call Ratio (PCR), Implied Volatility (IV), and Options Greeks.

---

## Options Parameters Evaluation

### 1. Source of Option Strikes Chain
* **Data Source:** **NONE.** No options contracts are downloaded from Zerodha Kite or the NSE.
* **Verdict:** **SYNTHETIC.** Generated mathematically using a step-size step heuristic centered around the stock spot price (ATM strike ± 5 strikes).

### 2. Source of Open Interest (OI) & PCR
* **Data Source:** **NONE.** 
* **Verdict:** **SYNTHETIC.** Calculated dynamically using normal Gaussian distribution decay bell curves to simulate ATM/OTM OI distributions. PCR is computed as a direct quotient: `total_put_oi / total_call_oi`.

### 3. Source of Implied Volatility (IV)
* **Data Source:** **NONE.**
* **Verdict:** **SYNTHETIC.** Calculated using a fixed daily volatility assumption scaled to an annualized standard deviation and modified by strike-skew functions.

### 4. Source of Options Greeks
* **Greeks Logic:** **REAL FORMULAS (SYNTHETIC INPUTS).**
* **Verdict:** **SYNTHETIC.** The Black-Scholes formulas for Delta, Gamma, Theta, and Vega are mathematically correct and fully implemented in Python, but because they are fed simulated strikes, IVs, and a fixed 30-day expiry time, the resulting Greeks are completely synthetic.

---

## Verdict Summary

| Derivatives Parameter | Source Engine | Data Type | Real-Market Value |
| :--- | :--- | :--- | :--- |
| **Option Strikes Matrix** | Heuristic Steps generator | **Synthetic** | **NO** (Simulated ATM ± 5) |
| **Open Interest (OI)** | normal Gaussian bell curve | **Synthetic** | **NO** (Simulated bell curve) |
| **Put-Call Ratio (PCR)** | Direct OI Quotient calculator | **Synthetic** | **NO** (Simulated quotient) |
| **Implied Volatility (IV)** | Annualized strike skew calculator | **Synthetic** | **NO** (Simulated skew) |
| **Options Greeks** | Python Black-Scholes solver | **Synthetic** | **NO** (Synthesized parameters) |
