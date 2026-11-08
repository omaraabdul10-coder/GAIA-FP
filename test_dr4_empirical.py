"""dr4_empirical: the A7 primary score (synthetic data only)."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from dr4_empirical import empirical_score

def test_overluminous_and_phase_signal_raise_score():
    X = pd.DataFrame(dict(dm=[0.0, -0.75, 0.0, -0.75], sig_cmd=[0.3]*4, z=[0.0, 0.0, 3.0, np.nan]))
    s = empirical_score(X)
    assert s[1] > s[0] and s[2] > s[0]          # CMD excess and RVS phase signal both count
    assert np.isclose(s[3], 0.75/0.3)           # missing RVS -> CMD only

def test_separates_synthetic_classes():
    rng = np.random.default_rng(0); n = 2000; y = rng.random(n) < 0.4
    X = pd.DataFrame(dict(dm=np.where(y, -0.6, 0) + rng.normal(0, .3, n), sig_cmd=0.3, z=np.where(y, 2.0, 0) + rng.normal(0, 1, n)))
    from dark_companion import auc
    assert auc(empirical_score(X), y.astype(int)) > 0.85
