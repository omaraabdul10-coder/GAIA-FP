"""H6 runner tests. SYNTHETIC scores only; the numbers are mechanics checks, not scientific results."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src')); sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd, h6_runner as H

def _y(): return np.r_[np.ones(40, int), np.zeros(40, int)]

def test_identical_scores_give_zero_difference_and_noninferiority():
    y = _y(); s = np.random.default_rng(0).normal(y * .7); r = H.h6_from_scores(y, s, s)
    assert r['status'] == 'CONDUCTED' and r['diff_ml_minus_gaiafp'] == 0 and r['non_inferiority_holds'] and not r['registered_falsified']

def test_much_better_ml_is_flagged_falsified_by_registered_rule():
    y = _y(); rng = np.random.default_rng(1); r = H.h6_from_scores(y, rng.normal(size=80), y + rng.normal(0, .3, 80))
    assert r['registered_falsified'] and r['ci95'][0] > 0

def test_reproducible_seed():
    y = _y(); rng = np.random.default_rng(2); a, b = rng.normal(y * .5), rng.normal(y * .5)
    assert H.h6_from_scores(y, a, b) == H.h6_from_scores(y, a, b)

def test_below_min_n_not_conducted():
    y = np.r_[np.ones(5, int), np.zeros(40, int)]; r = H.h6_from_scores(y, np.arange(45.), np.arange(45.)[::-1])
    assert r['status'] == 'NOT_CONDUCTED:BELOW_MIN_N'

def test_nonfinite_not_conducted():
    y = _y(); s = np.arange(80.); s[3] = np.nan; assert H.h6_from_scores(y, s, np.arange(80.))['status'].startswith('NOT_CONDUCTED')

def test_missing_inputs_list_exactly_what_is_needed():
    D = pd.DataFrame(dict(source_id=['1'], y=[1], P_impostor=[.5])); r = H.run_h6(D, mock_dir_base='/nonexistent')
    assert r['status'].startswith('NOT_CONDUCTED') and any('simulator file' in x for x in r['required']) and any("'P'" in x for x in r['required'])

class Stub:   # stands in for a trained registered model: SYNTHETIC
    def predict_proba(self, X): p = 1 / (1 + np.exp(-X[:, 0])); return np.c_[1 - p, p]
def test_runs_with_supplied_model_and_with_score_column():
    rng = np.random.default_rng(3); y = _y(); D = pd.DataFrame({c: rng.normal(size=80) for c in H.FEATURES}); D['y'] = y; D['P_impostor'] = rng.uniform(size=80)
    assert H.run_h6(D, model=Stub())['status'] == 'CONDUCTED'
    D['ml'] = rng.uniform(size=80); assert H.run_h6(D, ml_score_col='ml')['status'] == 'CONDUCTED'

def test_matches_legacy_dr4_evaluate_h6_on_identical_inputs():
    """Equivalence with the existing registered implementation (SYNTHETIC inputs, stub model; tournament training patched out)."""
    import dr4_evaluate as E, tournament
    sp, mm = tournament.splits, tournament.ml_model
    try:
        tournament.splits = lambda: (None, None); tournament.ml_model = lambda tr: Stub()
        rng = np.random.default_rng(5); D = pd.DataFrame({c: rng.normal(size=80) for c in H.FEATURES}); D['y'] = _y(); D['P_impostor'] = rng.uniform(size=80)
        a, b = E.h6(D), H.run_h6(D, model=Stub())
    finally: tournament.splits, tournament.ml_model = sp, mm
    for k in ('auc_ml', 'auc_gaiafp', 'ci95', 'registered_falsified'): assert a[k] == b[k], k



def test_h6_current_v06_ledger_holds_when_ci_includes_zero(monkeypatch):
    y = _y(); scores = np.random.default_rng(91).normal(size=80)
    monkeypatch.setattr(H.E, 'strat_boot', lambda *a, **k: np.full(2000, -0.001))
    r = H.h6_from_scores(y, scores, scores)
    assert r['ci95'][0] == -0.001
    assert r['non_inferiority_holds'] is True
    assert r['registered_falsified'] is False


def test_h6_current_v06_ledger_falsified_when_ci_entirely_above_zero(monkeypatch):
    y = _y(); scores = np.random.default_rng(92).normal(size=80)
    monkeypatch.setattr(H.E, 'strat_boot', lambda *a, **k: np.full(2000, 0.001))
    r = H.h6_from_scores(y, scores, scores)
    assert r['ci95'][0] == 0.001
    assert r['non_inferiority_holds'] is False
    assert r['registered_falsified'] is True
