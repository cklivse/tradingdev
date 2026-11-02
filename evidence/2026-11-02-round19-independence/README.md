# Round 19: independence assumptions of PSR / DSR, SE-ratio diagnostic

- `simulate.py` → `output.md`: PSR false-positive rate and true SD(SR) / formula SE
  under iid t(5), AR(1) 0.2 / 0.4 / −0.2 and GARCH(0.10, 0.85); ddof effects;
  the bootstrap-SE / formula-SE diagnostic (300 series × 1000 resamples per
  scenario, block length `sharpe._returns_block_size`); the KD fixture.
  Seed 20261102, code `feat/stats-py314` 8994a61.
- `ar04_p90_seed_check.py` → `.out`: the AR(1) 0.4 diagnostic quantiles over
  seeds 1–6, to judge the sampling error of the p90.

PSR is computed by the project's `probabilistic_sharpe_ratio`, called once per
sample; the script also re-derives it from the formula SE and reports the largest
gap (2.2e-16), confirming the SE it divides by is the one PSR uses.
