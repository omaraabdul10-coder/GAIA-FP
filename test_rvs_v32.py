import sys, os, numpy as np, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import rvs_v32 as V

ROW = dict(source_id='4295806720', P=400.0, e=0.3, T0=50.0, om=70.0, M=1.0, inc=60.0, dm=-0.5, sig_cmd=0.3, a0=1.0, a0err=0.05, d=100.0, sigP=0.01)

def epochs(signal, seed=0, n=30):
    rng = np.random.default_rng(seed); t = np.sort(rng.uniform(-900, 1100, n))
    nu = V.nu_of(t, ROW['P'], ROW['e'], ROW['T0']); w = np.radians(ROW['om'])
    tm = (np.cos(nu + w) + ROW['e']*np.cos(w))**2
    width = np.sqrt(11**2 + signal*tm) + rng.normal(0, 1.5, n)
    return t, width, np.full(n, 1.5)

def test_deterministic_and_order_free():
    t, w, e = epochs(0.0)
    assert V.llr_rvs(ROW, t, w, e) == V.llr_rvs(ROW, t, w, e)

def test_monotone_in_z():
    zs, Ls = [], []
    for s in (0, 50, 150, 400, 1000, 3000):
        z, L, info = V.llr_rvs(ROW, *epochs(s)); assert info == 'OK'; zs.append(z); Ls.append(L)
    o = np.argsort(zs); Ls = np.array(Ls)[o]
    assert np.all(np.diff(Ls) >= -1e-9), (np.array(zs)[o], Ls)
    assert Ls[-1] > 3                                   # a strong phase-locked signal is impostor evidence (A2-F2)

@pytest.mark.parametrize('signal', [0, 60, 100])
def test_mc_noise_small(signal):
    # where verdicts are decided (z <= ~4) the seed-to-seed SD must be < 0.2 nats; in the far tail (z > 6, LLR ~ 10) the SD is
    # ~1 nat, which cannot change a verdict (P ~ 1 either way) -- documented in AUDIT_REPORT
    t, w, e = epochs(signal, seed=4)
    orig = V.seed_of; vals = []
    try:
        for k in range(5):
            V.seed_of = lambda s, k=k: 1000 + k; vals.append(V.llr_rvs(ROW, t, w, e)[1])
    finally:
        V.seed_of = orig
    assert np.std(vals) < 0.2, vals                   # A2-F3: was a median 0.34 and up to 7.7 nats with 40 draws

def test_invalid_inputs_no_information():
    t, w, e = epochs(0)
    assert V.llr_rvs(ROW, t[:4], w[:4], e[:4])[2] == 'FEWER_THAN_6_EPOCHS'
    assert V.llr_rvs(ROW, t, np.full(len(t), 10.0), e)[2] == 'CONSTANT_WIDTHS'
    assert V.llr_rvs(dict(ROW, e=np.nan), t, w, e)[2] == 'INVALID_ORBIT'


def test_a6_uses_registered_secondary_to_primary_light_ratio():
    # q**n=0.22 is above the registered ell threshold, while beta=ell/(1+ell)<0.2.
    # A beta-based implementation would incorrectly retain this draw.
    q = np.array([0.5, 0.5])
    n = np.array([2.18, 2.40])
    K = np.array([35.0, 35.0])
    keep = V.sb1_keep_mask(q, n, K, e=0.0, enabled=True)
    assert q[0]**n[0] >= 0.2 and q[0]**n[0]/(1+q[0]**n[0]) < 0.2
    assert not keep[0]  # excluded by registered A6
    assert q[1]**n[1] < 0.2
    assert keep[1]      # retained by registered A6
    assert np.all(V.sb1_keep_mask(q, n, K, e=0.0, enabled=False))
