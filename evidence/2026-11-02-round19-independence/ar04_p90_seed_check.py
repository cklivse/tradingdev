"""Sampling spread of the AR(1) 0.4 diagnostic quantiles over six other seeds.

Run from the code checkout: uv run python <this file> <directory of simulate.py>
"""
import sys, numpy as np
sys.path.insert(0, sys.argv[1])
import simulate as sim
draw = sim.SCENARIOS["AR(1) 0.4"]
for seed in range(1, 7):
    seq = np.random.SeedSequence(seed)
    rng = np.random.default_rng(seq); bs = seq.generate_state(sim.DIAG_SERIES)
    r = []
    for i in range(sim.DIAG_SERIES):
        x = draw(rng, sim.N_OBS); L = sim._returns_block_size(x[:, None])
        r.append(sim.bootstrap_se(x, L, int(bs[i])) / sim.formula_se(x))
    r = np.array(r)
    boot = np.random.default_rng(0).choice(r, (2000, r.size)); se = np.quantile(boot, 0.9, axis=1).std()
    print(seed, np.round(np.quantile(r, [.1, .5, .9]), 3), "p90 bootstrap SE", round(se, 3))
