"""
dr4_dynamical.py: H8 dynamical labels (amendment v0.4 A3) for DR4 combined astrometric + SB1 solutions.

Same rules and the same Monte Carlo as src/astrospectro_check.py (frozen; it is written for the DR3 file layout):
  impostor            if m2_dyn 2.5th pct > 80 MJ  OR  rho 97.5th pct < 0.9
  genuine-consistent  if m2_dyn 97.5th pct < 80 MJ AND rho 2.5th pct > 0.9
  otherwise -1 (excluded).  n_mc = 400, seed 0, m2 from the first 150 draws (as in the DR3 code).
Primary mass: m1, m1_lower, m1_upper if the release provides them (DR3: binary_masses). Otherwise (fixed now, v0.6 A21):
  m1 = dr4_pipeline.mass_from_MG(M_G) with a 10 % one-sigma error, i.e. m1_upper - m1_lower = 0.2 m1.
The regression test tests/test_dr4_dynamical.py checks that this module reproduces results/astrospectro_labels.csv exactly on DR3.
"""
import sys, numpy as np, pandas as pd
from astrospectro_check import m2_from_a1, MJ
from dr4_pipeline import campbell, mass_from_MG

NEED = ['source_id', 'period', 'parallax', 'parallax_error'] + [f'{k}_thiele_innes{e}' for k in 'abfgch' for e in ('', '_error')]

def labels(D, n_mc=400, seed=0):
    miss = [c for c in NEED if c not in D]
    if miss: raise SystemExit(f'dynamical labels: missing columns {miss}: stop')
    D = D.copy()
    if not {'m1', 'm1_lower', 'm1_upper'} <= set(D.columns):
        MG = D.phot_g_mean_mag + 5*np.log10(D.parallax/100); D['m1'] = mass_from_MG(MG.values)
        D['m1_lower'], D['m1_upper'] = 0.9*D.m1, 1.1*D.m1
    rng = np.random.default_rng(seed); rows = []
    for _, r in D.iterrows():
        g = lambda k: r[k] + r[k+'_error']*rng.standard_normal(n_mc)
        A, B, F, G = g('a_thiele_innes'), g('b_thiele_innes'), g('f_thiele_innes'), g('g_thiele_innes')
        C, H = g('c_thiele_innes'), g('h_thiele_innes'); plx = g('parallax')
        m1 = np.clip(r['m1'] + 0.5*(r['m1_upper']-r['m1_lower'])*rng.standard_normal(n_mc), 0.08, None)
        a0, inc, _, _ = campbell(A, B, F, G); s = np.sin(np.radians(inc))
        a1sini = np.hypot(C, H); a1 = a1sini/np.clip(s, 1e-3, None)
        rho = (a0/plx)*s/a1sini
        P = r['period']/365.25
        m2 = np.array([m2_from_a1(a, P, m) for a, m in zip(a1[:150], m1[:150])])/MJ
        q = lambda x, p: float(np.nanpercentile(x, p))
        lab = 1 if (q(m2, 2.5) > 80 or q(rho, 97.5) < 0.9) else (0 if (q(m2, 97.5) < 80 and q(rho, 2.5) > 0.9) else -1)
        rows.append(dict(source_id=str(r['source_id']), rho=q(rho, 50), rho_lo=q(rho, 2.5), rho_hi=q(rho, 97.5),
                         m2_dyn=q(m2, 50), m2_lo=q(m2, 2.5), m2_hi=q(m2, 97.5), label=lab))
    T = pd.DataFrame(rows)
    assert (T.rho_lo.dropna() > -1).all(), 'rho far below 0: unit error?'           # physical-impossibility guard
    assert (T.m2_dyn.dropna() > 0).all(), 'non-positive dynamical mass'
    return T

if __name__ == '__main__':
    D = pd.read_csv(sys.argv[1], dtype={'source_id': str})
    labels(D).to_csv(sys.argv[2] if len(sys.argv) > 2 else '../results/dr4_dynamical_labels.csv', index=False)
