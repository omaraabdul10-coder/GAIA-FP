"""Contamination as a function of fitted companion mass and magnitude, estimated WITHOUT labels (v3 + EM)."""
import json, warnings, numpy as np, pandas as pd; warnings.filterwarnings('ignore')
import benchmark as B, hier_em as H
from eval_lib import scores
im = B.im.sample(frac=1, random_state=11).reset_index(drop=True).iloc[575:]
pl = pd.read_csv(B.R+'DR4_mock_exoplanet_catalog.csv').sample(6000, random_state=3).reset_index(drop=True).iloc[3000:]
X = H.build(pl, im, 0.30, 21); y = X['y'].values
L = scores(X, 0.30, 1)['v3']; r, pi = H.em(L, H.phi(X))
rs = np.random.default_rng(1); res = {}
for name, col, edges in [('mass_MJ', 'mfit', [0, 3, 8, 13, 30, 80]), ('G_mag', 'G', [0, 10, 12, 14, 16, 21])]:
    rows = []
    print(f"\nby {name}:   bin        n    true   estimate [95% CI]")
    for a, b in zip(edges[:-1], edges[1:]):
        m = (X[col] >= a) & (X[col] < b); m = m.values
        if m.sum() < 20: continue
        bo = [r[m][rs.integers(0, m.sum(), m.sum())].mean() for _ in range(500)]
        lo, hi = np.percentile(bo, [2.5, 97.5])
        print(f"   {a:>5}-{b:<5} {m.sum():5d}  {y[m].mean():.3f}   {r[m].mean():.3f} [{lo:.3f},{hi:.3f}]")
        rows.append(dict(lo=a, hi=b, n=int(m.sum()), true=float(y[m].mean()), est=float(r[m].mean()), ci=[float(lo), float(hi)]))
    res[name] = rows
json.dump(res, open('../results/contamination_bins.json', 'w'), indent=1)
