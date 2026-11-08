"""Parallel and serial scoring must give identical catalogues (per-candidate seeds make the RVS term order-independent)."""
import sys, os, numpy as np, pandas as pd
HERE = os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import dr4_run

def test_parallel_equals_serial():
    R = os.path.join(HERE, '..', 'realdata')
    cand = pd.read_csv(os.path.join(R, 'dr3_candidates.csv'), dtype={'source_id': str}).drop_duplicates('source_id').head(120)
    field = pd.read_csv(os.path.join(R, 'dr3_field.csv'))
    rng = np.random.default_rng(0); rvs = {}
    for s in cand.source_id.str.strip():
        n = 20; rvs[s] = dict(t=np.sort(rng.uniform(-1000, 1000, n)), width=rng.normal(10, 1.5, n), width_err=np.full(n, 1.5))
    a, _ = dr4_run.score(cand, field, rvs=rvs, v31=False, workers=1)
    b, _ = dr4_run.score(cand, field, rvs=rvs, v31=False, workers=2)
    for c in ('z', 'llr_rvs', 'P_impostor', 'P_impostor_noA6'):
        assert np.allclose(a[c].values, b[c].values, equal_nan=True), c
