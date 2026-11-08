"""8 Nov 2026: H1 power with the REGISTERED procedure itself (dr4_evaluate.h1: stratified bootstrap p-value, B = 2000),
at the weighted-Holm first-step level alpha = 0.01, plus the false-positive rate under AUC = 0.5 (calibration check of the
bootstrap p-value, audit A2). Binormal scores; 400 simulated data sets per cell; seed 11."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, '../src'); import dr4_evaluate as E
from scipy.stats import norm
rng = np.random.default_rng(11); out = {}
for n1, n0 in [(39, 26), (30, 20)]:
    for A in (0.5, 0.65, 0.70, 0.73, 0.80):
        d = np.sqrt(2)*norm.ppf(A); hits = 0; R = 400
        for _ in range(R):
            s = np.r_[rng.normal(d, 1, n1), rng.normal(0, 1, n0)]; y = np.r_[np.ones(n1, int), np.zeros(n0, int)]
            r = E.h1(pd.DataFrame(dict(y=y, P_impostor=1/(1 + np.exp(-s)))))
            hits += r['p'] <= 0.01
        out[f'{n1}v{n0}_AUC{A}'] = round(hits/R, 3)
        print(n1, n0, A, out[f'{n1}v{n0}_AUC{A}'], flush=True)
json.dump(out, open('../results/power_h1_bootstrap.json', 'w'), indent=1)
