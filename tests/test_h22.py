import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import h22_likelihood_only as H
def mk(n1, n0, sep, prior_noise, seed=0):
    r = np.random.default_rng(seed); y = np.r_[np.ones(n1), np.zeros(n0)].astype(int)
    llr = r.normal(sep*y, 1); lp = r.normal(0, prior_noise, len(y))
    return pd.DataFrame(dict(y=y, log_lr=llr, P_impostor=1/(1+np.exp(-(llr+lp)))))
def test_pass_and_better():
    o = H.h22(mk(39, 26, 1.5, 3.0)); assert o['H22a']['registered_pass'] and o['H22b']['d_auc'] > 0
def test_null_fails():
    assert not H.h22(mk(39, 26, 0.0, 0.0, 3))['H22a']['registered_pass']
def test_too_few():
    assert H.h22(mk(3, 26, 1, 0))['status'].startswith('NOT_CONDUCTED')
