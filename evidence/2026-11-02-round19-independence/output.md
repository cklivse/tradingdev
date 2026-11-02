# Round 19 independence-assumption simulation

seed 20261102; code 8994a61; Python 3.14.2; NumPy 2.5.4; arch 8.0.0; pandas 3.0.6
Scenarios: unit marginal variance plus mean 0.05; t(5) iid; AR(1) and GARCH(1,1) with normal innovations, 500 burn-in periods.

## 1. PSR under H0 (true per-period SR = benchmark = 0.05)
n = 365, samples per scenario = 20000

| scenario | P(PSR>0.95) | 95% MC band | SD(SR) | mean formula SE | ratio |
| --- | --- | --- | --- | --- | --- |
| iid t(5) | 5.49% | ±0.32% | 0.0528 | 0.0523 | 1.009 |
| AR(1) 0.2 | 9.03% | ±0.40% | 0.0646 | 0.0525 | 1.231 |
| AR(1) 0.4 | 13.94% | ±0.48% | 0.0797 | 0.0525 | 1.517 |
| AR(1) -0.2 | 2.31% | ±0.21% | 0.0431 | 0.0525 | 0.822 |
| GARCH(0.10,0.85) | 5.41% | ±0.31% | 0.0527 | 0.0525 | 1.004 |

Max |PSR from formula SE - probabilistic_sharpe_ratio| = 2.22e-16

## 2. ddof
|PSR(ddof=0 SR) - PSR(ddof=1 SR)| over all 100000 samples: mean 0.00038, max 0.00085
iid t(5) only: mean 0.00039, max 0.00085
DSR hurdle, N=3: std(ddof=0)/std(ddof=1) = 0.8165 (sqrt(2/3) = 0.8165, 18.4% lower)

## 3. SE-ratio diagnostic (bootstrap SE / formula SE)
n = 365, series per scenario = 300, resamples = 1000, block = _returns_block_size

| scenario | true ratio | p10 | median | p90 | share n/L<20 | median L |
| --- | --- | --- | --- | --- | --- | --- |
| iid t(5) | 1.01 | 0.94 | 1.00 | 1.05 | 0% | 2 |
| AR(1) 0.2 | 1.23 | 1.06 | 1.15 | 1.26 | 0% | 4 |
|  ↳ median captures 64% of (true - 1) | | | | | | |
| AR(1) 0.4 | 1.52 | 1.24 | 1.38 | 1.55 | 0% | 6 |
|  ↳ median captures 74% of (true - 1) | | | | | | |
| AR(1) -0.2 | 0.82 | 0.75 | 0.85 | 0.93 | 0% | 5 |
|  ↳ median captures 84% of (true - 1) | | | | | | |
| GARCH(0.10,0.85) | 1.00 | 0.83 | 0.98 | 1.08 | 18% | 6 |

## 4. KD(14,3,3) BTC/USDT 1h 2024 fixture, daily returns
n = 366, L = 3, n/L = 122
per-period SR = -0.3960, g3 = -1.584, g4 = 8.702
PSR denominator 1 - g3*SR + (g4-1)/4*SR^2 = 1 + (-0.627) + 0.302 = 0.675
  kurtosis term / leading 1 = 30%; |skew term| / leading 1 = 63%; higher-moment terms shift the denominator by -33%
  (normal returns would give 1 + SR^2/2 = 1.078)
SE ratio over bootstrap seeds [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]: 1.050, 0.999, 1.009, 1.036, 1.034, 1.024, 1.030, 1.044, 1.035, 1.027; range 0.999-1.050

