"""
h15_purity.py: H15 (amendment v0.6 A29), population purity of Gaia's substellar candidate list. DESCRIPTIVE: no pass/fail.
(a) impostor fraction = mean P_impostor (v3.2) over all scored candidates, bootstrap 95% CI (2000, seed 7); no labels used.
(b) companion-mass histogram 13-80 MJ in 6 log bins: raw counts and counts weighted by (1 - P_impostor), with bootstrap CIs;
    a bin is "contamination-dominated" if the raw count lies above the upper CI of the weighted count.
Run: cd src && python h15_purity.py <catalogue.csv> [out.json]
"""
import sys, json, numpy as np, pandas as pd

EDGES = np.geomspace(13, 80, 7); SEED, NBOOT = 7, 2000

def purity(C, n=NBOOT, seed=SEED):
    p = C.P_impostor.values.astype(float); m = C.mfit.values.astype(float)
    if not (np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()): raise SystemExit('P_impostor invalid: stop')
    rng = np.random.default_rng(seed); N = len(p); idx = [rng.integers(0, N, N) for _ in range(n)]
    frac = np.array([p[i].mean() for i in idx])
    b = np.digitize(m, EDGES) - 1; ok = (b >= 0) & (b < 6)
    raw = np.bincount(b[ok], minlength=6); w = np.bincount(b[ok], weights=1 - p[ok], minlength=6)
    wb = np.array([np.bincount(b[i][ok[i]], weights=1 - p[i][ok[i]], minlength=6) for i in idx])
    lo, hi = np.percentile(wb, 2.5, 0), np.percentile(wb, 97.5, 0)
    return dict(status='DESCRIPTIVE (no pass/fail)', n=int(N), impostor_fraction=[float(p.mean()), float(np.percentile(frac, 2.5)), float(np.percentile(frac, 97.5))],
                mass_bins_MJ=[[float(a), float(c)] for a, c in zip(EDGES[:-1], EDGES[1:])], raw_counts=raw.tolist(),
                weighted_counts=w.round(2).tolist(), weighted_ci95=[lo.round(2).tolist(), hi.round(2).tolist()],
                contamination_dominated=[bool(r > h) for r, h in zip(raw, hi)], n_outside_13_80=int((~ok).sum()))

if __name__ == '__main__':
    C = pd.read_csv(sys.argv[1]); out = purity(C)
    json.dump(out, open(sys.argv[2] if len(sys.argv) > 2 else '../results/h15_purity.json', 'w'), indent=1); print(json.dumps(out, indent=1))
