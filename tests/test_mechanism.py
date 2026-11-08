import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import mechanism as M

def test_solve_m2_roundtrip():
    m1 = np.array([1.0, 0.8, 1.2]); m2 = np.array([0.5, 0.08, 1.0])
    A = m2**3/(m1 + m2)**2
    assert np.allclose(M.solve_m2(m1, A), m2, rtol=1e-6)

def test_physics_known_binary():
    # m1 = 1, m2 = 0.5 Msun, P = 1 yr, i = 90, e = 0, dark companion (rho = 1)
    arel = 1.5**(1/3); a1 = arel/3
    X = pd.DataFrame(dict(eccentricity=[0.0], period=[365.25], inc=[90.0], om=[0.0], m1=[1.0], rho=[1.0],
                          c_thiele_innes=[a1], h_thiele_innes=[0.0]))
    Y = M.physics(X)
    assert abs(Y.m2dyn[0] - 0.5) < 1e-5 and abs(Y.Bfrac[0] - 1/3) < 1e-6
    assert abs(Y.K1[0] - M.VKMS*a1) < 1e-6 and abs(Y.Ksum[0] - M.VKMS*arel) < 1e-5
    assert Y.beta[0] == 0 and Y.b[0] == 0            # dark companion: no blend term
    X['rho'] = 0.4; Y = M.physics(X)                 # luminous: beta = B (1 - rho) = 0.2
    assert abs(Y.beta[0] - 0.2) < 1e-6 and Y.b[0] > 0

def test_pcorr_removes_confounder():
    rng = np.random.default_rng(0); z = rng.normal(size=4000); x = z + rng.normal(size=4000); y = z + rng.normal(size=4000)
    assert abs(M.pcorr(y, x, z[:, None])) < 0.05 and np.corrcoef(x, y)[0, 1] > 0.4


def test_pre_erratum_s1_is_retired_from_mechanism_output():
    import pandas as pd
    Y = M.retire_pre_erratum_s1(pd.DataFrame({"S1": [0.1, 0.2], "B2": [1.0, 2.0]}))
    assert "S1" not in Y.columns
    assert "S1_pre_erratum_DO_NOT_USE" in Y.columns
    assert Y["S1_pre_erratum_DO_NOT_USE"].tolist() == [0.1, 0.2]
