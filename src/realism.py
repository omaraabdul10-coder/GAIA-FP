"""
realism.py — checks of the simulation assumptions against what is actually measured (H in the research plan).
  R1  RVS epochs: uniform random times (used in sim.py) vs the REAL Gaia scan times of Gaia-4 and BH3
      (DR4 pre-release transits; RVS observes a subset of the astrometric transits).
  R2  analyst orbit uncertainty: the RVS template uses the astrometric orbit with sigma_P/P = 1% (sim default);
      Gaia orbits of short-period systems are far more precise — test 0.1%.
  R3  astrometric noise: per-transit uncertainty in the real pre-release data vs the error model used for RUWE proxy.
"""
import json, numpy as np, pandas as pd
from gaia_orbit import solve_kepler
from rvs_phase_test import K_sum_kms, phase_stat
from benchmark import sig_al

rng = np.random.default_rng(5)
def true_anom(t, P, e, T0):
    E = solve_kepler(np.mod(2*np.pi*(t-T0)/P, 2*np.pi), e); return 2*np.arctan2(np.sqrt(1+e)*np.sin(E/2), np.sqrt(1-e)*np.cos(E/2))

def z_stat(t, P, e, T0, om, K, f, sm, dP=0.01, sig0=11.0):
    nu = true_anom(t, P, e, T0); w = np.radians(om)
    dv = K*np.abs(np.cos(nu+w) + e*np.cos(w)); so = np.sqrt(sig0**2 + f*(1-f)*dv**2) + rng.normal(0, sm, len(t))
    s = phase_stat(t, P*(1+rng.normal(0, dP)), np.clip(e+rng.normal(0, .05), 0, .95), T0+rng.normal(0, .02*P), om+rng.normal(0, 10), so**2)
    return np.arctanh(np.clip(s, -.999, .999))*np.sqrt(len(t)-3)

real = {}
for nm in ('gaia4', 'bh3'):
    d = pd.read_csv(f'../data/{nm}.csv'); real[nm] = d
out = {'R1': {}, 'R2': {}}
for P in (150, 400, 800, 1500):
    K = K_sum_kms(.5, .475, P, .3, 60); row = {}
    for nm, d in real.items():
        tt = np.sort(d.iloc[:, 0].values)
        zr = [z_stat(np.sort(rng.choice(tt, min(40, len(tt)), replace=False)), P, .3, rng.uniform(0, P), rng.uniform(0, 360), K, .45, 4.0) for _ in range(300)]
        row[f'real_{nm}'] = float(np.mean(np.array(zr) > 2.326))
        span = tt.max()-tt.min()
        zu = [z_stat(np.sort(rng.uniform(0, span, 40)), P, .3, rng.uniform(0, P), rng.uniform(0, 360), K, .45, 4.0) for _ in range(300)]
        row[f'uniform_span_{nm}'] = float(np.mean(np.array(zu) > 2.326))
    out['R1'][P] = row
for P in (50, 150, 400):
    K = K_sum_kms(.5, .475, P, .3, 60)
    out['R2'][P] = {f'dP={dp}': float(np.mean(np.array([z_stat(np.sort(rng.uniform(0, 2000, 40)), P, .3, rng.uniform(0, P), rng.uniform(0, 360), K, .45, 4.0, dP=dp) for _ in range(300)]) > 2.326)) for dp in (0.01, 0.001)}
out['R3'] = {nm: dict(n_transits=len(d), median_err_mas=float(d['err_mas'].median()), span_days=float(np.ptp(d.iloc[:, 0])),
                      model_sig_al_G11=float(sig_al(11.0)), model_sig_al_G13=float(sig_al(13.0))) for nm, d in real.items()}
json.dump(out, open('../results/realism.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
