"""
astrospectro_check.py — INDEPENDENT physical labels for Gaia DR3 AstroSpectroSB1 candidates (REAL DATA; exploratory,
defined 9 Oct 2026 after the H7-DR3 run, BEFORE these labels were compared with any score).

For AstroSpectroSB1 solutions Gaia fits the photocentre orbit (A,B,F,G; mas) and the PRIMARY's radial-velocity orbit
(C,H; AU) with shared P, e, omega, T. Hence
    a1 sin i = sqrt(C^2 + H^2)            (true orbit of the primary, unaffected by light)
    rho      = (a0/parallax) sin i / (a1 sin i)   (= 1 for a dark companion, < 1 if the companion emits light)
and the dynamical companion mass follows from a1, P and m1 without any luminosity assumption.
The idea of using a0 vs a1 is not ours (Gaia DR3 binary_masses, Arenou et al. 2023); here it serves only as a label.

Label rules (fixed before comparison):
  impostor  if  m2_dyn 2.5th percentile > 80 MJ   OR   rho 97.5th percentile < 0.9
  genuine-consistent  if  m2_dyn 97.5th percentile < 80 MJ  AND  rho 2.5th percentile > 0.9
  otherwise undetermined (excluded)
Errors: Monte Carlo over the quoted 1-sigma errors of A,B,F,G,C,H, parallax and m1 (correlations ignored: a limitation).
"""
import json, numpy as np, pandas as pd
from scipy.optimize import brentq
from dr4_pipeline import campbell
from blind_eval import roc_auc
MJ = 1/1047.6

def m2_from_a1(a1, P_yr, m1):
    f = lambda m2: a1 - (m2/(m1+m2))*((m1+m2)*P_yr**2)**(1/3)
    try: return brentq(f, 1e-5, 50*m1)
    except ValueError: return np.nan

def main(real='../realdata/', out='../results/', n_mc=400, seed=0):
    rng = np.random.default_rng(seed)
    c = pd.read_csv(real+'dr3_candidates.csv'); c = c[c['nss_solution_type'] == 'AstroSpectroSB1'].drop_duplicates('source_id')
    ch = pd.read_csv(real+'dr3_astrospectro_ch.csv'); D = c.merge(ch, on='source_id')
    rows = []
    for _, r in D.iterrows():
        g = lambda k: r[k] + r[k+'_error']*rng.standard_normal(n_mc)
        A, B, F, G = g('a_thiele_innes'), g('b_thiele_innes'), g('f_thiele_innes'), g('g_thiele_innes')
        C, H = g('c_thiele_innes'), g('h_thiele_innes'); plx = g('parallax')
        m1 = np.clip(r['m1'] + 0.5*(r['m1_upper']-r['m1_lower'])*rng.standard_normal(n_mc), 0.08, None)
        a0, inc, _, _ = campbell(A, B, F, G); s = np.sin(np.radians(inc))   # campbell returns degrees
        a1sini = np.hypot(C, H); a1 = a1sini/np.clip(s, 1e-3, None)
        rho = (a0/plx)*s/a1sini
        P = r['period']/365.25
        m2 = np.array([m2_from_a1(a, P, m) for a, m in zip(a1[:150], m1[:150])])/MJ
        q = lambda x, p: float(np.nanpercentile(x, p))
        lab = 1 if (q(m2, 2.5) > 80 or q(rho, 97.5) < 0.9) else (0 if (q(m2, 97.5) < 80 and q(rho, 2.5) > 0.9) else -1)
        rows.append(dict(source_id=int(r['source_id']), rho=q(rho, 50), rho_lo=q(rho, 2.5), rho_hi=q(rho, 97.5),
                         m2_dyn=q(m2, 50), m2_lo=q(m2, 2.5), m2_hi=q(m2, 97.5), label=lab))
    T = pd.DataFrame(rows); T.to_csv(out+'astrospectro_labels.csv', index=False)
    res = dict(n=len(T), impostor=int((T.label == 1).sum()), genuine_consistent=int((T.label == 0).sum()), undetermined=int((T.label == -1).sum()),
               rho_median=float(T.rho.median()), m2dyn_median=float(T.m2_dyn.median()))
    # comparison with scores (only after labels are written)
    S = pd.read_csv(out+'dr3_candidates_scored.csv').merge(T, on='source_id')
    m = S.label >= 0; y = S.label[m].values
    if 0 < y.sum() < len(y):
        from scipy.special import expit, logit
        res['auc'] = {'GAIA-FP posterior (frozen, EM C=1)': float(roc_auc(S.P_impostor[m].values, y)),
                      'likelihood only (fixed prior)': float(roc_auc(S.log_lr[m].values, y)),
                      'B2 CMD excess': float(roc_auc(-S.dm[m].values, y)), 'B1 RUWE': float(roc_auc(S.ruwe[m].values, y))}
        res['frozen_verdicts_on_labelled'] = pd.crosstab(S.label[m], S.verdict[m]).to_dict()
    res['n_scored_labelled'] = int(m.sum())
    json.dump(res, open(out+'astrospectro_check.json', 'w'), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))
    return res

if __name__ == '__main__':
    main()
