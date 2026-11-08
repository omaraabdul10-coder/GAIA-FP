import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import new_hypotheses as N

def _lc(sid, P, amp, n=70, seed=0):
    rng = np.random.default_rng(seed); t = np.sort(rng.uniform(0, 2000, n)); err = np.full(n, 0.001)
    flux = 1e5*(1 + amp*np.cos(4*np.pi*t/P) + err*rng.standard_normal(n))
    return pd.DataFrame(dict(source_id=sid, g_obs_time=t, g_flux=flux, g_flux_error=err*1e5))

def test_ftest_detects_ellipsoidal_and_not_flat():
    F, p, _ = N.harmonic_ftest(*_lc('a', 37.3, 0.005).iloc[:, 1:].values.T, 37.3); assert p < 1e-6
    F, p, _ = N.harmonic_ftest(*_lc('b', 37.3, 0.0, seed=1).iloc[:, 1:].values.T, 37.3); assert p > 1e-3

def test_ftest_too_few_epochs():
    assert np.isnan(N.harmonic_ftest(*_lc('c', 10, 0.01, n=10).iloc[:, 1:].values.T, 10)[1])

def test_h17_end_to_end():
    ids = [str(i) for i in range(40)]; P = 50 + np.arange(40)
    lc = pd.concat([_lc(s, p, 0.004 if i < 12 else 0.0, seed=i) for i, (s, p) in enumerate(zip(ids, P))])
    fl = N.h17_flags(lc, dict(zip(ids, P)))
    assert fl.flag.sum() >= 10
    cat = pd.DataFrame(dict(source_id=ids, P_impostor=np.r_[np.full(12, 0.95), np.full(28, 0.4)], period=P))
    r = N.h17(cat, fl); assert r['status'] == 'CONDUCTED' and r['pass']

def test_fraction_test():
    r = N.fraction_test([1]*30 + [0]*2 + [-1]*50); assert r['pass_'] and r['n_resolved'] == 32
    assert N.fraction_test([1]*5 + [-1]*40)['status'] == 'NOT_CONDUCTED:BELOW_MIN_N'
    assert not N.fraction_test([1]*10 + [0]*10)['pass_']

def test_dark_assumed_m2_roundtrip():
    m1, m2, P = 1.0, 0.05, 400.0; plx = 10.0
    arel = ((m1 + m2)*(P/365.25)**2)**(1/3); a0 = arel*m2/(m1 + m2)*plx
    assert abs(N.dark_assumed_m2([a0], [plx], [P], [m1])[0] - m2) < 1e-6
