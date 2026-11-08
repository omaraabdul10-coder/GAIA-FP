import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import h15_purity as H

def test_known_fraction_and_bins():
    rng = np.random.default_rng(0); n = 3000
    C = pd.DataFrame(dict(P_impostor=np.r_[np.ones(n // 2), np.zeros(n // 2)], mfit=rng.uniform(14, 79, n)))
    o = H.purity(C, n=300)
    assert abs(o['impostor_fraction'][0] - 0.5) < 1e-12 and o['impostor_fraction'][1] < 0.5 < o['impostor_fraction'][2]
    assert sum(o['raw_counts']) == n and abs(sum(o['weighted_counts']) - n / 2) < 1e-6 and all(o['contamination_dominated'])

def test_no_contamination_flag_when_clean():
    C = pd.DataFrame(dict(P_impostor=np.zeros(500), mfit=np.full(500, 30.0)))
    assert not any(H.purity(C, n=200)['contamination_dominated'])
