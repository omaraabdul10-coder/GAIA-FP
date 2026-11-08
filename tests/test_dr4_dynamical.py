"""Regression: the DR4 dynamical-label module must reproduce the frozen DR3 labels exactly (same rules, same draws)."""
import sys, os, numpy as np, pandas as pd, pytest
HERE = os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import dr4_dynamical as DD

def test_reproduces_dr3_astrospectro_labels():
    R = os.path.join(HERE, '..', 'realdata')
    c = pd.read_csv(os.path.join(R, 'dr3_candidates.csv')); c = c[c['nss_solution_type'] == 'AstroSpectroSB1'].drop_duplicates('source_id')
    D = c.merge(pd.read_csv(os.path.join(R, 'dr3_astrospectro_ch.csv')), on='source_id')
    T = DD.labels(D)
    ref = pd.read_csv(os.path.join(HERE, '..', 'results', 'astrospectro_labels.csv'), dtype={'source_id': str})
    M = ref.merge(T, on='source_id', suffixes=('_ref', ''))
    assert len(M) == len(ref) == len(T)
    assert (M.label_ref == M.label).all()
    assert np.allclose(M.rho_ref, M.rho, equal_nan=True) and np.allclose(M.m2_dyn_ref, M.m2_dyn, equal_nan=True)

def test_missing_columns_stop():
    with pytest.raises(SystemExit): DD.labels(pd.DataFrame(dict(source_id=['1'])))
