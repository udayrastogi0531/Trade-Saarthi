# Option Intelligence Guide

The Option Intelligence module computes comprehensive derivative statistics and Option Greeks derived analytically via Black-Scholes pricing.

## Model-Based Statistics

* **PCR (Put-Call Ratio):** Total Put OI / Total Call OI. Reflects overall derivative writing bias.
* **Max Pain Strike:** Price point where options buyers face the highest loss.
* **Support & Resistance Strikes:** Pinpointed by the strikes holding the highest Put OI and Call OI respectively.

## Black-Scholes Option Greeks

Each strike in the Option Strikes Matrix displays full Greeks:

* **Call/Put Delta:** Measures the option's sensitivity to a ₹1 change in the underlying stock price.
* **Gamma:** Measures the rate of change of Delta per ₹1 change in stock price.
* **Call/Put Theta:** Measures the daily time-decay rate of options premiums.
* **Vega:** Measures the option sensitivity to a 1% change in Implied Volatility (IV).

All calculations are executed in pure Python using standard normal distributions for maximum execution speed and absolute runtime stability.
