import sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "followup"))
import shamakhy_forward as sf


def test_centroid_reproduces_photocentre_in_blend_limit():
    # blended centroid amplitude = K_sum (B - f): the same as the photocentre if f equals the astrometric light fraction
    q, M1, P, e, inc = 0.9, 1.0, 400.0, 0.3, 60.0
    B, f = q / (1 + q), sf.beta(q, sf.N_G)
    Ksum = sf.K_of(sf.a_rel_AU(M1, q, P), P, e, inc)
    mu, sig, s0, _ = sf.profile_moments(Ksum * B, -Ksum * (1 - B), f, 56000)
    a0 = sf.a_rel_AU(M1, q, P) * (B - f)
    assert np.isclose(mu, sf.K_of(a0, P, e, inc), rtol=1e-9)
    assert sig > s0                      # the blend is wider than one line


def test_q_solver_reproduces_a0():
    M1, P = 1.0, 400.0
    q0 = 0.93
    a0 = sf.a_rel_AU(M1, q0, P) * (q0 / (1 + q0) - sf.beta(q0, sf.N_G))
    q = sf.solve_q_imp(a0, M1, P)
    assert abs(q - q0) < 1e-6


def test_dark_companion_is_single_lined():
    mu, sig, s0, peaks = sf.profile_moments(3.0, 0.0, 0.0, 56000)
    assert peaks == 1 and np.isclose(sig, s0)


def test_resolved_twin_is_double_lined():
    _, _, s0, peaks = sf.profile_moments(15.0, -15.0, 0.45, 56000)
    assert peaks == 2
