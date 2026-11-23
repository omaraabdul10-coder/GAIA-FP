"""DR4 catalogue scan (exploratory; plan: DR4_CATALOGUE_SCAN_PLAN.md).

Turns the frozen GAIA-FP scores of every DR4 astrometric companion candidate into:
  1. the estimated impostor fraction, with and without the covariate prior (bootstrap 95% CI);
  2. a ranked list of the N candidates GAIA-FP finds most impostor-like among those with
     fitted companion mass < 80 MJ (ranked by log_lr, the prior-free score of H22; ties by P_impostor);
  3. baseline-trap flags (P >= 0.85 x the data baseline), H21's mechanism;
  4. the subset bright enough for a 2-m telescope (G <= 11) and north enough for Shamakhy (dec >= -10 deg).
No score, threshold or model is changed. Sealed evaluation objects are removed before anything is computed.

Usage:
  python dr4_catalogue_scan.py SCORED.csv --baseline-days 2010 --out-dir ../results/dr4_scan [--coords coords.csv] [--top 20]
  (dry run on DR3: SCORED=../results/dr3_candidates_scored.csv --baseline-days 1038)
"""
import argparse, json, os
import numpy as np, pandas as pd
from h21_baseline import drop_sealed

SEED, B = 24, 2000


def expit(x):
    return 1.0 / (1.0 + np.exp(-x))


def boot_mean(x, rng):
    idx = rng.integers(0, len(x), size=(B, len(x)))
    m = x[idx].mean(axis=1)
    return float(x.mean()), [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def scan(df, baseline_days, top=20, coords=None):
    rng = np.random.default_rng(SEED)
    n_in = len(df)
    df = drop_sealed(df)
    n_sealed_removed = n_in - len(df)
    cand = df[df.mfit < 80].copy()
    p_prior = cand.P_impostor.to_numpy(float)
    p_flat = expit(cand.log_lr.to_numpy(float))          # pi = 0.5: likelihood only
    cand['x_baseline'] = cand.P / baseline_days
    cand['baseline_trap'] = cand.x_baseline >= 0.85
    # A primary more than 1.5 mag above the main sequence is evolved; the CMD term then says nothing
    # about a companion. Such stars are flagged and left out of the ranked list (reporting rule only).
    cand['evolved_flag'] = cand.dm < -1.5
    if coords is not None:
        cand = cand.merge(coords[['source_id', 'ra', 'dec']], on='source_id', how='left')
        cand['shamakhy_ok'] = (cand.G <= 11) & (cand.dec >= -10)
    else:
        cand['shamakhy_ok'] = np.nan
    m1, ci1 = boot_mean(p_prior, rng)
    m2, ci2 = boot_mean(p_flat, rng)
    ranked = cand[~cand.evolved_flag].sort_values(['log_lr', 'P_impostor'], ascending=[False, False])
    cols = [c for c in ['source_id', 'G', 'P', 'e', 'mfit', 'M', 'dm', 'log_lr', 'P_impostor', 'verdict',
                        'x_baseline', 'baseline_trap', 'evolved_flag', 'ra', 'dec', 'shamakhy_ok'] if c in ranked]
    summary = dict(
        n_input=n_in, n_sealed_removed=n_sealed_removed, n_candidates_mfit_lt_80=int(len(cand)),
        impostor_fraction_with_prior=dict(mean=m1, ci95=ci1),
        impostor_fraction_likelihood_only=dict(mean=m2, ci95=ci2),
        n_P_gt_0p5_with_prior=int((p_prior > 0.5).sum()), n_P_gt_0p5_likelihood_only=int((p_flat > 0.5).sum()),
        n_baseline_trap=int(cand.baseline_trap.sum()), n_evolved_flagged=int(cand.evolved_flag.sum()),
        n_shamakhy_ok=(int(cand.shamakhy_ok.sum()) if coords is not None else None),
        baseline_days=baseline_days, seed=SEED, n_boot=B)
    return summary, ranked[cols].head(top), cand


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('scored'); ap.add_argument('--baseline-days', type=float, required=True)
    ap.add_argument('--out-dir', required=True); ap.add_argument('--coords'); ap.add_argument('--top', type=int, default=20)
    a = ap.parse_args()
    df = pd.read_csv(a.scored, dtype={'source_id': str})
    coords = pd.read_csv(a.coords, dtype={'source_id': str}) if a.coords else None
    s, top, cand = scan(df, a.baseline_days, a.top, coords)
    os.makedirs(a.out_dir, exist_ok=True)
    json.dump(s, open(os.path.join(a.out_dir, 'scan_summary.json'), 'w'), indent=1)
    top.to_csv(os.path.join(a.out_dir, 'most_suspicious.csv'), index=False)
    cand[cand.baseline_trap].to_csv(os.path.join(a.out_dir, 'baseline_trap_flags.csv'), index=False)
    print(json.dumps(s, indent=1))


if __name__ == '__main__':
    main()
