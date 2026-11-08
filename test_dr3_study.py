"""Unit tests for the real-data study utilities (SYNTHETIC fixtures only — no real data here).
Run:  cd src && python -m pytest ../tests -q
"""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import dr3_study as S
from blind_eval import roc_auc

def test_propagation_zero_pm_is_identity():
    ra, de = S.propagate(np.array([10.0]), np.array([20.0]), np.array([0.0]), np.array([0.0]))
    assert abs(ra[0]-10) < 1e-12 and abs(de[0]-20) < 1e-12

def test_propagation_moves_by_pm_times_dt():
    # 1000 mas/yr in Dec over -16 yr -> -16 arcsec
    _, de = S.propagate(np.array([0.0]), np.array([0.0]), np.array([0.0]), np.array([1000.0]))
    assert abs(de[0]*3600 + 16.0) < 1e-6

def test_separation_known_value():
    s = S.sep_arcsec(np.array([0.0]), np.array([0.0]), np.array([0.0]), np.array([1/3600]))
    assert abs(s[0]-1.0) < 1e-6

def test_positional_match_unique_and_ambiguous():
    ra = np.array([10.0, 50.0, 80.0]); de = np.array([0.0, 0.0, 0.0])
    cra = np.array([10.0+0.5/3600, 50.0+0.4/3600, 50.0-0.4/3600, 200.0]); cde = np.zeros(4)
    n, idx, sep = S.positional_match(ra, de, cra, cde, 2.0)
    assert list(n) == [1, 2, 0]
    assert idx[0] == 0 and np.isnan(sep[2])

def _cand(n=6):
    return pd.DataFrame(dict(source_id=np.arange(1, n+1), ra=np.linspace(10, 60, n), dec=np.zeros(n), pmra=0.0, pmdec=0.0,
                             dr2_source_id=np.arange(101, 101+n), dr2_angular_distance=np.full(n, 10.0)))

def test_labels_rules():
    c = _cand()
    lam = pd.DataFrame(dict(gaia_dr3_source_id=[1]))
    gal = pd.DataFrame(dict(gaia_dr2_source_id=[102]))
    apo = pd.DataFrame(dict(ra=[c.ra[2]+0.3/3600, c.ra[3]+0.3/3600, c.ra[3]-0.3/3600], dec=[0, 0, 0]))
    cov = pd.DataFrame(dict(gaia_dr2_source_id=[101, 104, 105, 106], n_epochs=[3, 5, 1, 2]))
    L = S.build_labels(c, lam, gal, apo, cov)
    assert list(L['sb2_lamost']) == [True, False, False, False, False, False]
    assert list(L['sb2_galah']) == [False, True, False, False, False, False]
    assert list(L['sb2_apogee']) == [False, False, True, False, False, False]
    assert bool(L['apogee_ambiguous'][3])
    # P1 population: LAMOST observed >=2 epochs or LAMOST SB2; ambiguous excluded
    assert list(L['label_P1']) == [1, -1, -1, -1, -1, 0]

def test_dr2_far_neighbour_not_used():
    c = _cand(); c.loc[1, 'dr2_angular_distance'] = 5000.0
    L = S.build_labels(c, pd.DataFrame(dict(gaia_dr3_source_id=[])), pd.DataFrame(dict(gaia_dr2_source_id=[102])),
                       pd.DataFrame(dict(ra=[], dec=[])), pd.DataFrame(dict(gaia_dr2_source_id=[], n_epochs=[])))
    assert not L['sb2_galah'][1]

def test_evaluate_underpowered_and_success():
    rng = np.random.default_rng(0)
    y = np.r_[np.ones(5), np.zeros(50)].astype(int); s = np.r_[rng.normal(2, 1, 5), rng.normal(0, 1, 50)]
    r = S.evaluate({'GAIA-FP': s, 'B4 random': rng.random(55)}, y)
    assert r['status'].startswith('UNDERPOWERED')
    y = np.r_[np.ones(40), np.zeros(200)].astype(int); s = np.r_[rng.normal(2, 1, 40), rng.normal(0, 1, 200)]
    r = S.evaluate({'GAIA-FP': s, 'B4 random': rng.random(240)}, y)
    assert r['status'] == 'SUCCESS' and r['auc']['GAIA-FP'] > 0.8

def test_roc_auc_basic():
    assert roc_auc(np.array([3, 2, 1, 0.]), np.array([1, 1, 0, 0])) == 1.0
