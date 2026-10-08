"""
rvs_predict.py — candidate-specific physics prediction of the RVS phase statistic under H_t (twin impostor).

For each candidate with RVS epochs we know (from Gaia alone): the astrometric orbit (P, e, i, T0, omega),
the apparent stellar mass M (photometry), number of RVS epochs and per-epoch line-width precision.
Under H_t we draw q ~ U(0.5, 1), split M into M1, M2, compute K1+K2 and the light fraction f(q),
and simulate the phase statistic z with the candidate's own cadence and noise. The empirical
distribution of simulated z (Gaussian KDE) is p(z | H_t). Under H_p, z ~ N(0, 1).
Nothing is tuned to labelled data or to mock catalogues.
"""
import numpy as np
from scipy.stats import norm
from rvs_phase_test import simulate_stat, K_sum_kms

def llr_rvs_physics(row, n_draw=40, rng=None, bw=0.5, n_ml=4.0):
    rng = np.random.default_rng() if rng is None else rng
    if not row['nep'] or not np.isfinite(row['z']):
        return 0.0
    zs = np.empty(n_draw)
    for k in range(n_draw):
        q = rng.uniform(0.5, 1.0); n_ml = rng.uniform(2.0, 6.0)
        M1 = row['M']/(1 + q**n_ml)**(1/n_ml)   # photometric mass of the blend -> primary mass
        M2 = q*M1
        K = K_sum_kms(M1, M2, row['P'], min(row['e'], 0.95), row['inc'])
        f = q**n_ml/(1+q**n_ml)
        s = simulate_stat(True, row['P'], row['e'], row['T0'], row['om'], K, f, int(row['nep']), float(row['srv']), rng, span=float(row['span']) if 'span' in row else 2000.0, dP=float(row['sigP']) if 'sigP' in row else 0.01)
        zs[k] = np.arctanh(np.clip(s, -.999, .999))*np.sqrt(row['nep']-3)
    pt = np.mean(norm.pdf(row['z'], zs, np.sqrt(bw**2)))
    pp = norm.pdf(row['z'], 0, 1)
    return float(np.clip(np.log(max(pt, 1e-300)) - np.log(pp), -30, 30))
