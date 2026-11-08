"""Core unit tests (SYNTHETIC fixtures only).  Run:  cd src && python -m pytest ../tests -q"""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import dr4_pipeline as D
from joint_lr import llr_a0_cmd
from hier_em import em
from scipy.special import expit

def _ti(a0, inc, om, Om):
    i, w, W = np.radians(inc), np.radians(om), np.radians(Om)
    A = a0*(np.cos(w)*np.cos(W)-np.sin(w)*np.sin(W)*np.cos(i)); B = a0*(np.cos(w)*np.sin(W)+np.sin(w)*np.cos(W)*np.cos(i))
    F = -a0*(np.sin(w)*np.cos(W)+np.cos(w)*np.sin(W)*np.cos(i)); G = -a0*(np.sin(w)*np.sin(W)-np.cos(w)*np.cos(W)*np.cos(i))
    return A, B, F, G

def test_campbell_roundtrip_a0_and_inclination():
    rng = np.random.default_rng(0)
    for _ in range(50):
        a0, inc = rng.uniform(0.1, 10), rng.uniform(5, 175)
        A, B, F, G = _ti(a0, inc, rng.uniform(0, 360), rng.uniform(0, 360))
        a, i, _, _ = D.campbell(np.array([A]), np.array([B]), np.array([F]), np.array([G]))
        assert abs(a[0]-a0) < 1e-9*max(1, a0)
        assert abs(min(i[0], 180-i[0]) - min(inc, 180-inc)) < 1e-6

def test_joint_llr_increases_with_overluminosity():
    n = 5; dm = np.linspace(0.2, -0.8, n)
    L = llr_a0_cmd(np.full(n, 0.5), np.full(n, 0.05), np.full(n, 500.), np.full(n, 0.6), np.full(n, 50.), dm, 0.3)
    assert np.all(np.diff(L) > 0)

def test_joint_llr_calibration_under_planet_hypothesis():
    """E_planet[LR] should be ~1 when the CMD scatter is correct (calibration identity)."""
    rng = np.random.default_rng(1); n = 4000
    L = llr_a0_cmd(np.full(n, 0.5), np.full(n, 0.05), np.full(n, 500.), np.full(n, 0.6), np.full(n, 50.), rng.normal(0, 0.3, n), 0.3)
    assert 0.8 < np.mean(np.exp(L)) < 1.25

def test_em_recovers_constant_mixture_fraction():
    rng = np.random.default_rng(2); n = 6000; y = rng.random(n) < 0.25
    L = np.where(y, rng.normal(2, 1.5, n), rng.normal(-2, 1.5, n))       # log LR with exact Gaussian-equal-variance form below
    # exact LR for N(2,1.5) vs N(-2,1.5): log LR = (4/1.5^2) x
    x = np.where(y, rng.normal(2, 1.5, n), rng.normal(-2, 1.5, n)); L = (4/1.5**2)*x
    F = np.zeros((n, 1)) + rng.normal(0, 1e-3, (n, 1))
    r, _ = em(L, F)
    assert abs(r.mean() - 0.25) < 0.03

def test_rvs_z_detects_phase_locked_width_and_not_constant():
    t = np.linspace(0, 2000, 40); P, e, T0, om = 400.0, 0.3, 50.0, 30.0
    from rvs_phase_test import true_anomaly
    nu = true_anomaly(t, P, e, T0); w = np.radians(om); g2 = (np.cos(nu+w) + e*np.cos(w))**2
    rng = np.random.default_rng(3)
    z_bin, _ = D.rvs_z(t, np.sqrt(121 + 0.25*(30**2)*g2) + rng.normal(0, 1, 40), P, e, T0, om)
    z_const, _ = D.rvs_z(t, 11 + rng.normal(0, 1, 40), P, e, T0, om)
    assert z_bin > 3 and abs(z_const) < 3

def test_three_way_verdict_thresholds():
    p = np.array([0.0, 0.15, 0.5, 0.85, 1.0])
    v = np.where(p <= D.T_ABSTAIN, 'likely_substellar', np.where(p >= 1-D.T_ABSTAIN, 'likely_impostor', 'ambiguous_followup_needed'))
    assert list(v) == ['likely_substellar', 'likely_substellar', 'ambiguous_followup_needed', 'likely_impostor', 'likely_impostor']

def test_ms_ridge_recovers_scatter():
    rng = np.random.default_rng(4); n = 20000; c = rng.uniform(0.5, 3.5, n)
    MG = 3 + (c-0.5)*10/3 + rng.normal(0, 0.3, n)
    r = D.fit_ms_ridge(pd.DataFrame(dict(phot_g_mean_mag=MG + 5*np.log10(50/10), bp_rp=c, parallax=20.0)))
    assert abs(np.median(r['sigma']) - 0.3) < 0.05
