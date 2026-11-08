"""8 Nov 2026: H1 power at the weighted-Holm first-step level alpha = 0.4*0.025 = 0.01 (A31), computed directly
(the 7 Nov figure was interpolated between 0.0125 and 0.005). Same binormal model, 3000 runs, seed 1."""
import json, numpy as np
from scipy.stats import norm, mannwhitneyu
rng = np.random.default_rng(1); out = {}
for n1, n0 in [(39, 26), (30, 20)]:
    for A in (0.65, 0.70, 0.73, 0.80):
        d = np.sqrt(2)*norm.ppf(A)
        k = sum(mannwhitneyu(rng.normal(d, 1, n1), rng.normal(0, 1, n0), alternative='greater').pvalue <= 0.01 for _ in range(3000))
        out[f'{n1}v{n0}_AUC{A}'] = round(k/3000, 3)
print(json.dumps(out, indent=1)); json.dump(out, open('results/power_h1_alpha001.json', 'w'), indent=1)
