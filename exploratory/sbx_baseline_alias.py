"""Exploratory (24 Nov 2026): do Gaia DR3 orbits of stars with a KNOWN long-period orbit (SBX, P > 1500 d)
lock onto periods near the DR3 baseline (~1038 d)? External ground truth for H21's mechanism.
Inputs (realdata/external/sbx_long/): sbx_long_systems.csv (SBX TAP), gaia_match.csv (Gaia archive TAP upload join,
1 arcsec, gaiadr3.nss_two_body_orbit). No sealed object is among the matches."""
import pandas as pd, numpy as np, json
from scipy.stats import binomtest
D = 'realdata/external/sbx_long/'
g = pd.read_csv(D + 'gaia_match.csv'); s = pd.read_csv(D + 'sbx_long_systems.csv')
s['plist'] = s.periods.astype(str).str.split(';').apply(lambda L: [float(x) for x in L])
d = g.merge(s[['sn', 'plist']], on='sn'); d = d[d.nss_solution_type != 'EclipsingBinary']
def cls(r):
    P, L = r.period, r.plist
    if any(abs(p - P) / p < 0.25 for p in L): return 'agrees'
    if any(abs(P / p - k) < 0.1 or abs(p / P - k) < 0.1 for p in L for k in (2, 3)): return 'harmonic'
    if 600 <= P <= 1400 and max(L) >= 1.8 * P: return 'baseline_alias'
    return 'other'
d['class'] = d.apply(cls, axis=1); d['ratio'] = d.apply(lambda r: max(r.plist) / r.period, axis=1)
win = d.period.between(600, 1400)
un = d[d['class'].isin(['baseline_alias', 'other']) & (d.period < 1500)]
k, n = int(un.period.between(600, 1400).sum()), len(un); p0 = np.log(1400 / 600) / np.log(1500)
out = dict(n_sbx_systems=len(s), n_gaia_solutions=len(d), n_in_600_1400=int(win.sum()),
           classes_in_window=d[win]['class'].value_counts().to_dict(),
           unmatched_lt1500=n, unmatched_in_window=k, expected_frac_loguniform=p0,
           binom_p_greater=binomtest(k, n, p0, alternative='greater').pvalue,
           alias_median_ratio=float(d[d['class'] == 'baseline_alias'].ratio.median()))
json.dump(out, open('exploratory/sbx_baseline_alias.json', 'w'), indent=1, default=float); print(json.dumps(out, indent=1, default=float))
