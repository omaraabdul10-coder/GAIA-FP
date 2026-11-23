"""h19_desert.py: the brown-dwarf desert after removing luminous impostors, by mass bin (H19_DESERT_PLAN.md).

Reporting only, no new test. It reuses the H19 table of new_hypotheses.h18_h19 (dynamical labels from combined
astrometric + spectroscopic orbits, independent of the GAIA-FP score), so it is not circular.

usage:  python h19_desert.py --dev-dr3                        (DR3 development values)
        python h19_desert.py --dr4 STD/mech_scored.csv OUT/h19_desert.json
"""
import sys, json
import numpy as np, pandas as pd
from scipy.stats import beta
import new_hypotheses as N

MJ = 9.546e-4
BINS_MJ = [1, 13, 30, 50, 80]


def cp(k, n, a=0.05):
    if n == 0:
        return (np.nan, np.nan)
    lo = beta.ppf(a / 2, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(1 - a / 2, k + 1, n - k) if k < n else 1.0
    return float(lo), float(hi)


def by_mass(Y):
    m = Y.m2dark / MJ
    rows = []
    for a, b in zip(BINS_MJ[:-1], BINS_MJ[1:]):
        s = Y[(m >= a) & (m < b) & (Y.label >= 0)]
        n, k = len(s), int((s.label == 1).sum())
        lo, hi = cp(k, n)
        lum = s[s.label == 1]
        rows.append(dict(bin_MJ=f'{a}-{b}', n=n, n_luminous=k, frac_luminous=(k / n) if n else None,
                         cp95_lo=lo, cp95_hi=hi, n_dark_consistent=n - k,
                         median_true_over_dark_mass=float((lum.m2dyn / lum.m2dark).median()) if len(lum) else None))
    return rows


def main(argv):
    if '--dev-dr3' in argv:
        X = pd.read_csv('../results/dark_companion_scored.csv', dtype={'source_id': str})
        _, Y = N.h18_h19(X)
        res = dict(status='DR3 development values, not a test', bins=by_mass(Y),
                   note='Combined orbits favour massive companions; fractions describe that subsample only.')
        json.dump(res, open('../results/h19_desert_dev_dr3.json', 'w'), indent=1)
        print(pd.DataFrame(res['bins']).round(3).to_string(index=False)); return
    if '--dr4' in argv:
        i = argv.index('--dr4'); X = pd.read_csv(argv[i + 1], dtype={'source_id': str})
        _, Y = N.h18_h19(X); res = dict(plan='H19_DESERT_PLAN.md', bins=by_mass(Y))
        json.dump(res, open(argv[i + 2], 'w'), indent=1); print(pd.DataFrame(res['bins']).to_string(index=False)); return
    print(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
