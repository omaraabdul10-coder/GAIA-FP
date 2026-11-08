"""
h6_runner.py — reproducible runner for H6 (registered in HYPOTHESIS_LEDGER.md; definition NOT changed here).

H6 (secondary): AUC(ML baseline trained on the Lammers & Winn simulator) - AUC(GAIA-FP), PAIRED STRATIFIED bootstrap
(2000 replicates, seed 7, percentile 95% CI -- identical procedure and helpers as dr4_evaluate.py).
Registered reading in the current v0.6 ledger: non-inferiority of GAIA-FP holds if the CI is NOT entirely above 0; the registered claim is falsified
if the CI is entirely above 0. A separate earlier project note records a -0.01 lower-bound rule with a different comparison direction; see H6_RULE_DISCREPANCY.md.
Statuses follow v0.6 A19: CONDUCTED / NOT_CONDUCTED:<reason> (never reported as FAIL).

Where the ML scores come from (exactly one):
  --ml-score-col COL   the catalogue already contains the ML score (trained elsewhere on the registered simulator);
  default              train tournament.ml_model on tournament.splits()[0]; this REQUIRES the simulator mocks
                        ../dl/GaiaForecasts/DR4_mock_planet_impostor_catalog.csv and DR4_mock_exoplanet_catalog.csv
                        and the tournament feature columns P,e,mfit,d,G,dm,z in the catalogue.
If anything is missing the runner writes a NOT_CONDUCTED report that lists exactly what is needed.  No numbers are invented.

    python h6_runner.py --catalogue CSV [--label-col y] [--ml-score-col ml_score] [--out h6_report.json]
    python h6_runner.py --selftest       # SYNTHETIC mechanics check only; prints a clearly labelled synthetic result
"""
import argparse, json, os, sys
import numpy as np, pandas as pd
import dr4_evaluate as E

MOCKS = ['../dl/GaiaForecasts/DR4_mock_planet_impostor_catalog.csv', '../dl/GaiaForecasts/DR4_mock_exoplanet_catalog.csv']
FEATURES = ['P', 'e', 'mfit', 'd', 'G', 'dm', 'z']          # = tournament.COLS (checked against the module when it is importable)

def needs(D=None, ml_score_col=None, label_col='y', mock_dir_base=None):
    """Return the list of concrete missing requirements (empty list = runnable)."""
    miss = []
    if D is None: return ['catalogue CSV with columns source_id, P_impostor and the label column']
    for c in (label_col, 'P_impostor'):
        if c not in D: miss.append(f'catalogue column {c!r}')
    if ml_score_col:
        if ml_score_col not in D: miss.append(f'catalogue column {ml_score_col!r} (ML score)')
    else:
        miss += [f'catalogue feature column {c!r}' for c in FEATURES if c not in D]
        base = mock_dir_base or os.getcwd()
        miss += [f'simulator file {m} (Lammers & Winn mocks)' for m in MOCKS if not os.path.exists(os.path.join(base, m))]
    return miss

def h6_from_scores(y, s_gaiafp, s_ml, n_boot=E.NBOOT, seed=E.SEED, min_class=E.MIN_CLASS):
    """Core registered computation on arrays (testable with synthetic data)."""
    y = np.asarray(y, int); s = np.asarray(s_gaiafp, float); m = np.asarray(s_ml, float)
    if not (len(y) == len(s) == len(m)): return E.not_conducted('LENGTH_MISMATCH')
    if not (np.isfinite(s).all() and np.isfinite(m).all()): return E.not_conducted('NONFINITE_SCORES')
    if set(np.unique(y)) - {0, 1} or min(int(y.sum()), int((y == 0).sum())) < min_class: return E.not_conducted('BELOW_MIN_N')
    bs = E.strat_boot(lambda i: E.auc(m[i], y[i]) - E.auc(s[i], y[i]), y, n=n_boot, seed=seed)
    lo, hi = float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
    am, ag = E.auc(m, y), E.auc(s, y)
    return dict(status='CONDUCTED', n=int(len(y)), n_impostor=int(y.sum()), n_substellar=int((y == 0).sum()), auc_ml=am, auc_gaiafp=ag,
                diff_ml_minus_gaiafp=am - ag, ci95=[lo, hi], bootstrap_replicates=n_boot, bootstrap_seed=seed,
                registered_falsified=bool(lo > 0), non_inferiority_holds=bool(not lo > 0))

def run_h6(D, label_col='y', ml_score_col=None, model=None, n_boot=E.NBOOT, seed=E.SEED, mock_dir_base=None):
    if model is not None:   # caller supplies an already-trained registered model: mocks are not needed, features are
        miss = [f'catalogue column {c!r}' for c in [label_col, 'P_impostor'] + FEATURES if c not in D]
    else:
        miss = needs(D, ml_score_col, label_col, mock_dir_base)
    if miss: return dict(E.not_conducted('DATA_OR_SCHEMA_MISSING'), required=miss)
    y = D[label_col].values
    if ml_score_col: m = D[ml_score_col].values
    else:
        if model is None:
            import tournament; assert tournament.COLS == FEATURES, 'feature list drifted from tournament.COLS'
            try: model = tournament.ml_model(tournament.splits()[0])
            except (FileNotFoundError, OSError) as e: return dict(E.not_conducted('DATA_ABSENT (simulator mocks)'), required=MOCKS, error=str(e))
        m = model.predict_proba(D[FEATURES].values.astype(float))[:, 1]
    return h6_from_scores(y, D['P_impostor'].values, m, n_boot, seed)

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument('--catalogue'); ap.add_argument('--label-col', default='y'); ap.add_argument('--ml-score-col')
    ap.add_argument('--out', default='h6_report.json'); ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args(argv)
    if a.selftest:
        rng = np.random.default_rng(0); y = np.r_[np.ones(40, int), np.zeros(40, int)]
        r = h6_from_scores(y, rng.normal(y*0.8), rng.normal(y*0.8)); r['DATA'] = 'SYNTHETIC SELFTEST - NOT A SCIENTIFIC RESULT'
    else:
        if not a.catalogue: print('--catalogue required (or --selftest)', file=sys.stderr); return 2
        D = pd.read_csv(a.catalogue, dtype={'source_id': str}); r = run_h6(D, a.label_col, a.ml_score_col); r['DATA'] = a.catalogue
    json.dump(r, open(a.out, 'w'), indent=1, default=float); print(json.dumps(r, indent=1, default=float)); return 0

if __name__ == '__main__':
    sys.exit(main())
