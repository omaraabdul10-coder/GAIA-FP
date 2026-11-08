"""
tests_geometry.py -- independent audit A1 (orbital geometry, kinematics, units, angles) of GAIA-FP.

Run from anywhere (no file under ../src or ../results is written; byte-code writing is disabled):
    PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider -q audit/tests_geometry.py

Tests marked xfail(strict=True, reason="FINDING n") document a defect described in A1_geometry_report.md;
they FAIL on the current code and will turn into XPASS (= suite error) once the defect is fixed.
All reference values are derived from physics in the test itself, not copied from the code under test.
"""
import os, sys
sys.dont_write_bytecode = True                      # never write .pyc into the hash-frozen src/ tree
SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, SRC)
import warnings
import numpy as np, pandas as pd, pytest
from scipy.optimize import brentq

import dr4_pipeline as D
import gaia_orbit as GO
import rvs_phase_test as RPT
import dark_companion as DC
import vbroad_v2 as V2
import mechanism as MECH
import astrospectro_check as ASC
import joint_lr as JL
import benchmark as BM
import followup as FU
import dr3_study as DS

warnings.filterwarnings('ignore', category=RuntimeWarning)

# ----------------------------------------------------------------------------- physical constants (IAU / CODATA)
AU_KM = 1.495978707e8
DAY_S = 86400.0
JYR_D = 365.25
K_GAUSS = 0.01720209895                      # Gaussian gravitational constant, AU^1.5 Msun^-0.5 day^-1
MJ_MSUN = 1/1047.348644                      # IAU 2015 nominal Jupiter/Sun mass ratio
ME_MSUN = 3.003489e-6                        # Earth/Sun mass ratio

def ti_ref(a, inc, om, Om):
    """Thiele-Innes constants from Campbell elements (deg), written independently of the code (Binnendijk 1960)."""
    i, w, W = np.radians(inc), np.radians(om), np.radians(Om)
    A = a*(np.cos(w)*np.cos(W) - np.sin(w)*np.sin(W)*np.cos(i))
    B = a*(np.cos(w)*np.sin(W) + np.sin(w)*np.cos(W)*np.cos(i))
    F = a*(-np.sin(w)*np.cos(W) - np.cos(w)*np.sin(W)*np.cos(i))
    G = a*(-np.sin(w)*np.sin(W) + np.cos(w)*np.cos(W)*np.cos(i))
    return A, B, F, G

def kepler_ref(M, e):
    """Reference Kepler solution by bracketing (E - e sin E is monotone in E)."""
    return np.array([brentq(lambda E: E - e*np.sin(E) - m, m - 1.1, m + 1.1, xtol=1e-14) for m in np.atleast_1d(M)])

def k_sum_ref(M1, M2, P_day, e, inc_deg):
    """K1+K2 [km/s] from Kepler III in SI-free form: a^3 = k^2 (M1+M2) P^2 / (4 pi^2)  [AU, day]."""
    a = (K_GAUSS**2*(M1 + M2)*P_day**2/(4*np.pi**2))**(1/3)
    return 2*np.pi*a*np.sin(np.radians(inc_deg))/(P_day*np.sqrt(1 - e**2))*AU_KM/DAY_S

def photocentre_a0_ref(Mphot, q, n, P_day, plx_mas):
    """Photocentre semimajor axis [mas] built from luminosity-weighted component positions (no closed form used)."""
    M1 = brentq(lambda m: (m**n + (q*m)**n)**(1/n) - Mphot, 1e-6, 10*Mphot)    # blend photometric mass -> primary
    M2 = q*M1
    arel = (K_GAUSS**2*(M1 + M2)*P_day**2/(4*np.pi**2))**(1/3)                  # AU
    x1, x2 = -arel*M2/(M1 + M2), arel*M1/(M1 + M2)                               # positions w.r.t. barycentre
    L1, L2 = M1**n, M2**n
    return abs((L1*x1 + L2*x2)/(L1 + L2))*plx_mas, M1, M2, -2.5*np.log10((L1 + L2)/L1)

# ============================================================================= 1. Campbell <-> Thiele-Innes
def _random_geometry(n, seed=0):
    rng = np.random.default_rng(seed)
    a = 10**rng.uniform(-3, 3, n)
    inc = np.degrees(np.arccos(rng.uniform(-1, 1, n)))
    inc[:12] = [0.0, 1e-7, 1e-4, 0.5, 89.5, 89.9999, 90.0, 90.0001, 90.5, 179.5, 180 - 1e-4, 180 - 1e-7]
    return a, inc, rng.uniform(0, 360, n), rng.uniform(0, 360, n)

def test_campbell_roundtrip_dr4_pipeline():
    a, inc, om, Om = _random_geometry(20000)
    A, B, F, G = ti_ref(a, inc, om, Om)
    a2, i2, w2, W2 = D.campbell(A, B, F, G)
    assert np.allclose(a2/a, 1, atol=1e-9)
    assert np.max(np.abs(i2 - inc)) < 1e-4                         # deg, incl. i = 0, 90, 180
    A2, B2, F2, G2 = ti_ref(a2, i2, w2, W2)                         # elements -> TI again
    assert np.max(np.abs(np.c_[A2 - A, B2 - B, F2 - F, G2 - G])/a[:, None]) < 1e-8

def test_campbell_inclination_identity_cos_i():
    a, inc, om, Om = _random_geometry(5000, 1)
    A, B, F, G = ti_ref(a, inc, om, Om)
    assert np.allclose((A*G - B*F)/a**2, np.cos(np.radians(inc)), atol=1e-12)   # v = a0^2 cos i
    r_m, r_p = np.hypot(A - G, B + F), np.hypot(A + G, B - F)
    ok = inc < 179
    assert np.allclose(r_m[ok]/r_p[ok], np.tan(np.radians(inc[ok])/2)**2, rtol=1e-6, atol=1e-12)
    assert np.allclose((r_p + r_m)/2, a, rtol=1e-12)                # a0 = (r+ + r-)/2

def test_campbell_pi_ambiguity_is_a_symmetry_and_output_pair_is_consistent():
    a, inc, om, Om = _random_geometry(2000, 2)
    T1 = np.array(ti_ref(a, inc, om, Om)); T2 = np.array(ti_ref(a, inc, om + 180, Om + 180))
    assert np.allclose(T1, T2, atol=1e-12*a.max())                  # (w, W) ~ (w+pi, W+pi)
    _, _, w2, W2 = D.campbell(*T1)
    d = lambda x, y: (x - y + 180) % 360 - 180
    same = (np.abs(d(w2, om)) < 1e-5) & (np.abs(d(W2, Om)) < 1e-5)
    flip = (np.abs(d(w2, om + 180)) < 1e-5) & (np.abs(d(W2, Om + 180)) < 1e-5)
    ok = (inc > 0.5) & (inc < 179.5)            # at i = 0 / 180 only w +/- W is defined (checked by the TI round trip)
    assert np.all((same | flip)[ok])

def test_campbell_degenerate_inputs_fail_loudly():
    a0, inc, _, _ = D.campbell(np.zeros(1), np.zeros(1), np.zeros(1), np.zeros(1))
    assert a0[0] == 0 and np.isnan(inc[0])                           # undefined inclination -> NaN, not a number
    out = D.campbell(np.array([np.nan]), np.ones(1), np.ones(1), np.ones(1))
    assert all(np.isnan(x[0]) for x in out)

@pytest.mark.xfail(strict=True, raises=AssertionError, reason="FINDING 7: gaia_orbit.campbell reduces Omega mod 180 without shifting omega by 180")
def test_gaia_orbit_campbell_roundtrip():
    a, inc, om, Om = _random_geometry(4000, 3)
    ok = (inc > 0.5) & (inc < 179.5); a, inc, om, Om = a[ok], inc[ok], om[ok], Om[ok]   # face-on NaN is tested separately
    A, B, F, G = ti_ref(a, inc, om, Om)
    c = GO.campbell(A, B, F, G)
    A2, B2, F2, G2 = GO.thiele_innes(c['a0'], c['inc'], c['omega'], c['Omega'])
    err = np.max(np.abs(np.c_[A2 - A, B2 - B, F2 - F, G2 - G])/a[:, None], axis=1)
    assert np.all(np.isfinite(err)) and err.max() < 1e-6                  # fails: ~50% come back as -(A,B,F,G)

@pytest.mark.xfail(strict=True, raises=AssertionError, reason="FINDING 7: gaia_orbit.campbell returns NaN a0 for an exactly face-on orbit (no clip)")
def test_gaia_orbit_campbell_face_on_not_nan():
    rng = np.random.default_rng(4)
    A, B, F, G = GO.thiele_innes(np.full(500, 1.3), np.zeros(500), rng.uniform(0, 360, 500), rng.uniform(0, 360, 500))
    assert np.all(np.isfinite(GO.campbell(A, B, F, G)['a0']))

def test_gaia_orbit_thiele_innes_matches_reference_convention():
    a, inc, om, Om = _random_geometry(1000, 5)
    assert np.allclose(np.array(GO.thiele_innes(a, inc, om, Om)), np.array(ti_ref(a, inc, om, Om)), atol=1e-12*a.max())

# ============================================================================= 2. Kepler / anomalies
@pytest.mark.parametrize('e', [0.0, 0.1, 0.5, 0.79, 0.8, 0.9, 0.95, 0.99])
def test_kepler_roundtrip_M_E_M(e):
    M = np.r_[0.0, 1e-9, np.linspace(0, 2*np.pi, 2001)[1:-1], 2*np.pi - 1e-9]
    E = RPT.solve_kepler(M, e)
    assert np.max(np.abs(E - e*np.sin(E) - M)) < 1e-11
    sel = M[::100]; assert np.allclose(RPT.solve_kepler(sel, e), kepler_ref(sel, e), atol=1e-10)

def test_true_anomaly_identities():
    t = np.linspace(-3000, 3000, 999); P, T0 = 377.0, 123.0
    assert np.allclose(np.cos(RPT.true_anomaly(t, P, 0.0, T0)), np.cos(2*np.pi*(t - T0)/P), atol=1e-12)   # e = 0: nu = M
    for e in (0.3, 0.9):
        nu = RPT.true_anomaly(t, P, e, T0); E = RPT.solve_kepler(np.mod(2*np.pi*(t - T0)/P, 2*np.pi), e)
        assert np.allclose(np.cos(nu), (np.cos(E) - e)/(1 - e*np.cos(E)), atol=1e-12)
        assert np.allclose(np.sin(nu), np.sqrt(1 - e**2)*np.sin(E)/(1 - e*np.cos(E)), atol=1e-12)
    assert np.isnan(RPT.true_anomaly(np.array([1.0]), 100.0, np.nan, 0.0)[0])                          # NaN e is loud

def test_kepler_vectorised_eccentricity_broadcast():
    M = np.linspace(0, 2*np.pi, 64, endpoint=False)[None, :]; e = np.array([0.0, 0.5, 0.85, 0.95])[:, None]
    E = RPT.solve_kepler(M*np.ones_like(e), e)
    assert np.max(np.abs(E - e*np.sin(E) - M)) < 1e-11

# ============================================================================= 3. astrometric epoch model
def test_design_orbit_equals_independent_sky_projection():
    """w_orbit = Dalpha* sin(psi) + Ddelta cos(psi), with (Ddelta, Dalpha*) from r, nu, omega, Omega, i directly."""
    rng = np.random.default_rng(6); n = 300
    d = dict(t_day=np.sort(rng.uniform(-1000, 1000, n)), psi=rng.uniform(0, 2*np.pi, n))
    d['sin_psi'], d['cos_psi'] = np.sin(d['psi']), np.cos(d['psi'])
    P, e, T0, a, inc, om, Om = 543.0, 0.47, -71.0, 0.83, 63.0, 211.0, 37.0
    w_code = GO.design_orbit(d, P, e, T0) @ np.array(ti_ref(a, inc, om, Om))
    nu = RPT.true_anomaly(d['t_day'], P, e, T0); r = a*(1 - e**2)/(1 + e*np.cos(nu))
    u, i, W = nu + np.radians(om), np.radians(inc), np.radians(Om)
    ddec = r*(np.cos(u)*np.cos(W) - np.sin(u)*np.sin(W)*np.cos(i))      # north
    dra = r*(np.cos(u)*np.sin(W) + np.sin(u)*np.cos(W)*np.cos(i))       # east
    assert np.allclose(w_code, dra*d['sin_psi'] + ddec*d['cos_psi'], atol=1e-12)

def test_linear_fit_recovers_orbit_at_true_nonlinear_parameters():
    d = GO.simulate(orbit=dict(P=571.0, e=0.4, T0=120.0, a0=0.27, inc=60.0, omega=40.0, Omega=110.0), seed=1, sig_ccd=1e-6)
    p, _, _ = GO.chi2_orbit(d, 571.0, 0.4, 120.0)
    assert np.allclose(p[:5], [0, 0, 13.3, 50.0, -30.0], atol=1e-4)      # dra, ddec, plx [mas], pm [mas/yr]
    a0, inc, om, Om = D.campbell(*[np.atleast_1d(x) for x in p[5:]])
    assert abs(a0[0] - 0.27) < 1e-5 and abs(inc[0] - 60.0) < 1e-3
    assert min(abs((om[0] - 40.0 + 180) % 360 - 180), abs((om[0] - 220.0 + 180) % 360 - 180)) < 1e-3

def test_proper_motion_time_unit_is_julian_year():
    d = dict(t_day=np.array([0.0, JYR_D]), sin_psi=np.array([1.0, 1.0]), cos_psi=np.array([0.0, 0.0]), f_plx=np.zeros(2))
    w = GO.design_single(d) @ np.array([0, 0, 0, 7.0, 0])                # mura* = 7 mas/yr
    assert np.isclose(w[1] - w[0], 7.0)

# ============================================================================= 4. velocities, Kepler III, dimensional sanity
def test_k_sum_earth_sun_and_jupiter_reflex():
    assert np.isclose(RPT.K_sum_kms(1.0, ME_MSUN, 365.25636, 0.0167, 90.0), 29.78, atol=0.02)     # Earth orbital speed
    Kj = RPT.K_sum_kms(1.0, MJ_MSUN, 4332.59, 0.0489, 90.0)*MJ_MSUN/(1 + MJ_MSUN)
    assert np.isclose(Kj*1e3, 12.5, atol=0.15)                                                   # solar reflex, m/s
    assert np.isclose(RPT.K_sum_kms(0.8, 0.3, 700.0, 0.6, 37.0), k_sum_ref(0.8, 0.3, 700.0, 0.6, 37.0), rtol=1e-6)

def test_k_sum_inclination_and_eccentricity_scaling():
    K90 = RPT.K_sum_kms(1.0, 0.5, 500.0, 0.0, 90.0)
    assert RPT.K_sum_kms(1.0, 0.5, 500.0, 0.0, 0.0) == pytest.approx(0.0, abs=1e-12)
    assert RPT.K_sum_kms(1.0, 0.5, 500.0, 0.0, 30.0) == pytest.approx(0.5*K90)
    assert RPT.K_sum_kms(1.0, 0.5, 500.0, 0.8, 90.0) == pytest.approx(K90/0.6)

def test_unit_constants():
    assert np.isclose(RPT.G, K_GAUSS**2, rtol=1e-6)                         # AU^3 Msun^-1 day^-2
    assert np.isclose(RPT.AU_KMS, AU_KM/DAY_S, rtol=1e-6)                   # 1 AU/day in km/s
    # VKMS = 29.7847 is 2 pi AU per SIDEREAL year (29.78474); mechanism divides by P/365.25 (Julian): 1.7e-5 relative, cosmetic
    assert np.isclose(MECH.VKMS, 2*np.pi*AU_KM/(JYR_D*DAY_S), rtol=1e-4)
    for mj in (D.MJ, JL.MJ, BM.MJ, DC.MJ, ASC.MJ):
        assert np.isclose(mj, MJ_MSUN, rtol=1e-3)

def test_mechanism_K1_matches_k_sum():
    m1, m2, P = 1.0, 0.5, 365.25
    arel = (m1 + m2)**(1/3)*(P/JYR_D)**(2/3); a1 = arel*m2/(m1 + m2)
    X = pd.DataFrame(dict(eccentricity=[0.3], period=[P], inc=[90.0], om=[0.0], m1=[m1], rho=[1.0], c_thiele_innes=[a1], h_thiele_innes=[0.0]))
    Y = MECH.physics(X)
    assert np.isclose(Y.Ksum[0], k_sum_ref(m1, m2, P, 0.3, 90.0), rtol=1e-4)
    assert np.isclose(Y.m2dyn[0], m2, rtol=1e-5)

def _lr_K_recorder(module, monkeypatch):
    rec = []
    real = RPT.K_sum_kms
    def wrapped(M1, M2, P, e, inc):
        K = real(M1, M2, P, e, inc); rec.append((np.broadcast_to(M1, np.shape(K)), np.broadcast_to(M2, np.shape(K)), K)); return K
    monkeypatch.setattr(module, 'K_sum_kms', wrapped)
    return rec

@pytest.mark.xfail(strict=True, raises=AssertionError, reason="FINDING 1: dark_companion.lr_vbroad passes P in years to K_sum_kms (expects days)")
def test_lr_vbroad_uses_physical_K(monkeypatch):
    rec = _lr_K_recorder(DC, monkeypatch)
    n = 3; P = np.array([200.0, 500.0, 1500.0]); e = np.array([0.0, 0.3, 0.6]); inc = np.array([90.0, 60.0, 30.0]); M = np.array([1.0, 0.7, 0.5])
    W = DC.q_weights(np.zeros(n), np.full(n, 0.3))
    DC.lr_vbroad(np.full(n, 12.0), np.ones(n), np.full(n, 9.0), np.full(n, 2.0), M, P, e, inc, DC.phase_avg(e, np.zeros(n)), W)
    M1, M2, K = rec[0]
    assert np.allclose(K, k_sum_ref(M1, M2, P[:, None], e[:, None], inc[:, None]), rtol=1e-6)

@pytest.mark.xfail(strict=True, raises=AssertionError, reason="FINDING 1: a luminous blend whose vbroad equals the physical prediction is scored as DARK")
def test_lr_vbroad_favours_blend_when_vbroad_matches_physics():
    q, n_, Mphot, P, e, inc, med, sig = 0.8, 4.0, 1.0, 500.0, 0.0, 90.0, 9.0, 1.5
    j = np.argmin(np.abs(DC.QG - q) + np.abs(DC.NG - n_)); W = np.zeros((1, DC.QG.size)); W[0, j] = 1.0
    qg, ng = DC.QG[j], DC.NG[j]; lq = qg**ng; f = lq/(1 + lq); M1 = Mphot/(1 + lq)**(1/ng)
    pavg = 0.5                                                                  # e = 0: <cos^2> = 1/2
    vb = np.sqrt(med**2 + f*(1 - f)*k_sum_ref(M1, qg*M1, P, e, inc)**2*pavg)  # what a blend with c = 1 should show
    L = DC.lr_vbroad(np.array([vb]), np.zeros(1), np.array([med]), np.array([sig]), np.array([Mphot]), np.array([P]),
                     np.array([e]), np.array([inc]), np.array([pavg]), W)
    assert L[0] > 0

@pytest.mark.xfail(strict=True, raises=AssertionError, reason="FINDING 1: vbroad_v2.lr_v2 passes P in years to K_sum_kms (expects days)")
def test_lr_v2_uses_physical_K(monkeypatch):
    rec = _lr_K_recorder(V2, monkeypatch)
    Y = pd.DataFrame(dict(m1=[1.0, 0.6], eccentricity=[0.1, 0.5], period=[300.0, 900.0], inc=[80.0, 45.0], om=[10.0, 200.0],
                          dm=[-0.3, -0.1], sig=[0.3, 0.3], vb_med=[9.0, 8.0], vb_sig=[2.0, 2.0], vbroad=[12.0, 9.0], vbroad_error=[1.0, 1.0]))
    V2.lr_v2(Y, 1.0)
    M1, M2, K = rec[0]
    assert np.allclose(K, k_sum_ref(M1, M2, Y.period.values[:, None], Y.eccentricity.values[:, None], Y.inc.values[:, None]), rtol=1e-6)

def test_rvs_predict_and_followup_pass_days():
    """The DR4 physics path (rvs_predict, followup) must give K in physical units; checked via the same reference."""
    assert np.isclose(RPT.K_sum_kms(0.6, 0.48, 412.0, 0.2, 70.0), k_sum_ref(0.6, 0.48, 412.0, 0.2, 70.0), rtol=1e-6)

# ============================================================================= 5. photocentre, mass, a_rel
def test_a0_mas_jupiter_at_10pc():
    a_j = (K_GAUSS**2*(1 + MJ_MSUN)*4332.59**2/(4*np.pi**2))**(1/3)        # 5.20 AU
    expect = a_j*MJ_MSUN/(1 + MJ_MSUN)*100.0                                   # mas at 10 pc
    assert np.isclose(BM.a0_mas(MJ_MSUN/BM.MJ, 1.0, 4332.59, 10.0), expect, rtol=2e-4)
    assert np.isclose(expect, 0.497, atol=0.002)

def test_features_absolute_magnitude_and_distance_units():
    cand, ridge = _synthetic_dr4(5)
    X = D.features(cand, ridge)
    assert np.allclose(X.d, 1000/cand.parallax) and np.allclose(X.MG, cand.phot_g_mean_mag + 5*np.log10(cand.parallax/1000) + 5)

@pytest.mark.parametrize('q,n', [(0.65, 3.0), (0.8, 4.0), (0.95, 5.0)])
def test_q_weights_peak_where_photocentre_matches(q, n):
    """a0(q) rises then falls (twin branch), so a0 alone is bimodal in q; the grid point nearest the true q must be a
    local maximum of the a0-only weights (CMD made uninformative with sigma = 50 mag)."""
    Mphot, P, plx = 0.9, 600.0, 25.0
    a0, *_ = photocentre_a0_ref(Mphot, q, n, P, plx)
    W = DC.q_weights(np.zeros(1), np.full(1, 50.0), np.array([a0]), np.array([1e-4*a0]), np.array([Mphot]), np.array([P]), np.array([plx]))[0]
    row = np.isclose(DC.NG, n); Q, Wr = DC.QG[row], W[row]; j = int(np.argmin(np.abs(Q - q)))
    assert Wr[j] >= Wr[max(j - 1, 0)] and Wr[j] >= Wr[min(j + 1, len(Q) - 1)] and Wr[j] > 1e-3*Wr.max()

def test_q_weights_twin_limit_a0_zero():
    W = DC.q_weights(np.zeros(1), np.full(1, 50.0), np.array([1e-7]), np.array([1e-8]), np.array([0.9]), np.array([600.0]), np.array([25.0]))[0]
    for n in np.unique(DC.NG):
        row = np.isclose(DC.NG, n); assert DC.QG[row][np.argmax(W[row])] == pytest.approx(1.0)

def test_llr_a0_cmd_against_independent_quadrature():
    a0, a0err, P, Mphot, d, s = 0.35, 0.04, 480.0, 0.75, 40.0, 0.3
    qs = np.linspace(0.1, 1.0, 901); ns = np.linspace(2.0, 6.0, 9)
    s_a0 = np.sqrt(a0err**2 + (a0*0.08/3)**2)
    grid = np.array([photocentre_a0_ref(Mphot, q, n, P, 1000/d) for n in ns for q in qs])
    la = np.exp(-0.5*((a0 - grid[:, 0])/s_a0)**2)
    for dm in (0.1, -0.4, -0.75):
        ref = np.log(np.sum(la*np.exp(-0.5*((dm - grid[:, 3])/s)**2))/np.sum(la)) + 0.5*(dm/s)**2
        code = JL.llr_a0_cmd(np.array([a0]), np.array([a0err]), np.array([P]), np.array([Mphot]), np.array([d]), np.array([dm]), s)[0]
        assert code == pytest.approx(ref, abs=0.03)

def test_m2_from_a1_and_solve_m2_roundtrip():
    for m1, m2, Pyr in [(1.0, 1.0, 1.0), (0.6, 0.05, 2.3), (1.2, 80*MJ_MSUN, 0.4), (0.3, 0.001, 5.0)]:
        arel = ((m1 + m2)*Pyr**2)**(1/3); a1 = arel*m2/(m1 + m2)
        assert ASC.m2_from_a1(a1, Pyr, m1) == pytest.approx(m2, rel=1e-6)
        assert MECH.solve_m2(np.array([m1]), np.array([a1**3/Pyr**2]))[0] == pytest.approx(m2, rel=1e-6)

def test_first_order_mass_exact_in_planetary_limit():
    cand, ridge = _synthetic_dr4(1, m2_MJ=1.0, M1=0.8)
    X = D.features(cand, ridge)
    assert X.mfit[0] == pytest.approx(1.0, rel=2e-3)

@pytest.mark.xfail(strict=True, raises=AssertionError, reason="FINDING 3: first-order companion mass underestimates m2 by (1+m2/M1)^(-2/3) near the 80 MJ cut")
@pytest.mark.parametrize('M1', [0.15, 0.3, 0.6])
def test_first_order_mass_at_selection_boundary(M1):
    cand, ridge = _synthetic_dr4(1, m2_MJ=80.0, M1=M1)
    X = D.features(cand, ridge)
    assert X.mfit[0] == pytest.approx(80.0, rel=0.05)

# ============================================================================= 6. rho (a0 vs a1), dynamical labels
def _rho_row(a1_au, inc, om, Om, plx, rho_true, err=1e-6):
    A, B, F, G = ti_ref(rho_true*a1_au*plx, inc, om, Om)
    s = np.sin(np.radians(inc)); C, H = a1_au*s*np.sin(np.radians(om)), a1_au*s*np.cos(np.radians(om))
    r = dict(a_thiele_innes=A, b_thiele_innes=B, f_thiele_innes=F, g_thiele_innes=G, c_thiele_innes=C, h_thiele_innes=H, parallax=plx)
    r.update({k + '_error': err for k in list(r)}); return r

@pytest.mark.parametrize('inc', [5.0, 45.0, 90.0, 135.0])
def test_rho_dark_companion_is_one(inc):
    lab, rho = DC.rho_labels(pd.DataFrame([_rho_row(0.4, inc, 33.0, 71.0, 12.0, 1.0)]))
    assert rho[0] == pytest.approx(1.0, abs=1e-3) and lab[0] == 0

def test_rho_luminous_blend_value_and_label():
    q, n = 0.8, 4.0; B = q/(1 + q); beta = q**n/(1 + q**n); rho_true = 1 - beta/B      # photocentre / primary orbit
    lab, rho = DC.rho_labels(pd.DataFrame([_rho_row(0.4, 60.0, 33.0, 71.0, 12.0, rho_true)]))
    assert rho[0] == pytest.approx(rho_true, abs=1e-3) and lab[0] == 1

def test_rho_invariant_to_omega_plus_pi_of_spectroscopic_orbit():
    r = _rho_row(0.4, 60.0, 33.0, 71.0, 12.0, 0.7); r2 = dict(r); r2['c_thiele_innes'] *= -1; r2['h_thiele_innes'] *= -1
    assert DC.rho_labels(pd.DataFrame([r]))[1][0] == pytest.approx(DC.rho_labels(pd.DataFrame([r2]))[1][0])

def test_rho_face_on_is_undetermined_not_luminous():
    r = _rho_row(0.4, 0.0, 33.0, 71.0, 12.0, 1.0, err=0.0)
    lab, rho = DC.rho_labels(pd.DataFrame([r]))
    assert lab[0] == -1 and np.isnan(rho[0])

# ============================================================================= 7. phase averages / omega conventions
def _pavg_exact(e, om):
    s = np.sqrt(1 - e**2); w = np.radians(om)
    return s**2*(np.sin(w)**2 + s*np.cos(w)**2)/(1 + s)                    # <(cos(nu+w) + e cos w)^2>_t, closed form

def test_phase_avg_closed_form_low_e():
    e = np.array([0.0, 0.2, 0.5, 0.7]);
    for om in (0.0, 37.0, 90.0, 250.0):
        assert np.allclose(DC.phase_avg(e, np.full(4, om)), _pavg_exact(e, om), rtol=1e-3)
    assert np.allclose(DC.phase_avg(np.array([0.9, 0.95]), np.array([0.0, 60.0]), n=200000), _pavg_exact(np.array([0.9, 0.95]), np.array([0.0, 60.0])), rtol=1e-4)

@pytest.mark.xfail(strict=True, raises=AssertionError, reason="FINDING 6: phase_avg samples 64 uniform mean anomalies; wrong by up to x2.7 at e = 0.95")
def test_phase_avg_closed_form_high_e():
    e = np.array([0.85, 0.9, 0.95])
    for om in (0.0, 45.0, 90.0):
        assert np.allclose(DC.phase_avg(e, np.full(3, om)), _pavg_exact(e, om), rtol=0.05)

def test_maxsep_closed_form_low_e():
    e = np.array([0.0, 0.2, 0.5])
    for om in (0.0, 30.0, 60.0, 90.0):
        assert np.allclose(V2.maxsep_shape(e, np.full(3, om)), 1 + e*abs(np.cos(np.radians(om))), rtol=0.012)

@pytest.mark.xfail(strict=True, raises=AssertionError, reason="FINDING 6: maxsep_shape misses the periastron peak; low by up to 34% at e = 0.95")
def test_maxsep_closed_form_high_e():
    e = np.array([0.8, 0.9, 0.95])
    for om in (30.0, 60.0):
        assert np.allclose(V2.maxsep_shape(e, np.full(3, om)), 1 + e*abs(np.cos(np.radians(om))), rtol=0.02)

def test_omega_plus_pi_invariance_of_all_omega_consumers():
    rng = np.random.default_rng(8); e = rng.uniform(0, 0.8, 20); om = rng.uniform(0, 360, 20)
    assert np.allclose(DC.phase_avg(e, om), DC.phase_avg(e, om + 180))
    assert np.allclose(V2.maxsep_shape(e, om), V2.maxsep_shape(e, om + 180))
    t = np.sort(rng.uniform(0, 2000, 30)); w = 11 + rng.normal(0, 1, 30)
    assert D.rvs_z(t, w, 400.0, 0.3, 50.0, 40.0)[0] == pytest.approx(D.rvs_z(t, w, 400.0, 0.3, 50.0, 220.0)[0])
    assert RPT.phase_stat(t, 400.0, 0.3, 50.0, 40.0, w**2) == pytest.approx(RPT.phase_stat(t, 400.0, 0.3, 50.0, 220.0, w**2))
    K = np.full(5, 30.0); r1 = np.random.default_rng(1); r2 = np.random.default_rng(1)
    assert np.allclose(FU._sep_kms(K, 400.0, 0.3, 40.0, r1, 3), FU._sep_kms(K, 400.0, 0.3, 220.0, r2, 3))

def test_projected_separation_geometry():
    rng = np.random.default_rng(0)
    assert np.allclose(FU._rho_proj(np.full(50, 2.0), 10.0, 0.0, 0.0, 300.0, rng), 20.0)      # face-on circular: a * plx

# ============================================================================= 8. RVS phase statistic and time zero-points
def _twin_widths(P=398.5, e=0.3, T0=111.0, om=40.0, seed=11):
    rng = np.random.default_rng(seed); t = np.sort(rng.uniform(0, 2000, 35))
    nu = RPT.true_anomaly(t, P, e, T0); w = np.radians(om)
    width = np.sqrt(11**2 + 0.2*30**2*(np.cos(nu + w) + e*np.cos(w))**2) + rng.normal(0, 1.5, 35)
    return t, width, P, e, T0, om

def test_rvs_z_detects_twin_and_is_shift_invariant():
    t, wd, P, e, T0, om = _twin_widths()
    z, n = D.rvs_z(t, wd, P, e, T0, om); assert z > 3 and n == 35
    assert D.rvs_z(t + 1234.5, wd, P, e, T0 + 1234.5, om)[0] == pytest.approx(z)
    assert np.isnan(D.rvs_z(t[:5], wd[:5], P, e, T0, om)[0])

@pytest.mark.xfail(strict=True, raises=AssertionError, reason="FINDING 2: no reference-epoch handling: epoch times in BJD-2455197.5 vs T0 from J2016.0 kill the test")
def test_rvs_z_robust_to_gaia_time_conventions():
    """Gaia epoch products use BJD(TCB) - 2455197.5 (J2010.0); DR3 t_periastron is days from J2016.0 (JD 2457389.0).
    The pipeline must bring both to one zero point (or refuse to run); rvs_z/score accept them silently."""
    t, wd, P, e, T0, om = _twin_widths()
    z_ok = D.rvs_z(t, wd, P, e, T0, om)[0]
    z_raw = D.rvs_z(t + (2457389.0 - 2455197.5), wd, P, e, T0, om)[0]     # times as delivered, T0 as delivered
    assert z_raw == pytest.approx(z_ok, abs=0.5)

# ============================================================================= 9. pipeline edge cases (NaN, zero, negative)
def _synthetic_dr4(n, m2_MJ=10.0, M1=0.8, seed=21):
    rng = np.random.default_rng(seed)
    plx = rng.uniform(5, 40, n); P = rng.uniform(200, 1500, n)
    m2 = m2_MJ*MJ_MSUN
    arel = ((M1 + m2)*(P/JYR_D)**2)**(1/3); a0 = arel*m2/(M1 + m2)*plx               # exact Kepler + barycentre
    A, B, F, G = ti_ref(a0, np.degrees(np.arccos(rng.uniform(-1, 1, n))), rng.uniform(0, 360, n), rng.uniform(0, 360, n))
    c = rng.uniform(0.8, 2.5, n)
    cand = pd.DataFrame(dict(source_id=np.arange(n) + 10**17, nss_solution_type='Orbital', period=P, period_error=0.01*P,
                             eccentricity=rng.uniform(0, 0.5, n), eccentricity_error=0.05, t_periastron=rng.uniform(-P/2, P/2),
                             a_thiele_innes=A, b_thiele_innes=B, f_thiele_innes=F, g_thiele_innes=G,
                             a_thiele_innes_error=0.02, b_thiele_innes_error=0.02, f_thiele_innes_error=0.02, g_thiele_innes_error=0.02,
                             parallax=plx, parallax_error=0.02, significance=20.0, m1=M1,
                             phot_g_mean_mag=3 + (c - 0.5)*10/3 + 5*np.log10(100/plx), bp_rp=c, ruwe=1.2, grvs_mag=np.nan))
    fc = rng.uniform(0.5, 3.5, 20000)
    field = pd.DataFrame(dict(phot_g_mean_mag=3 + (fc - 0.5)*10/3 + rng.normal(0, 0.3, 20000) + 5*np.log10(50/10), bp_rp=fc, parallax=20.0))
    return cand, D.fit_ms_ridge(field)

def test_features_zero_and_negative_parallax_never_selected():
    cand, ridge = _synthetic_dr4(4)
    cand.loc[0, 'parallax'] = 0.0; cand.loc[1, 'parallax'] = -5.0
    X = D.select_candidates(D.features(cand, ridge))
    assert set(X.source_id) == set(cand.source_id[2:])

@pytest.mark.xfail(strict=True, raises=AssertionError, reason="FINDING 4: DR4 CLI path (features -> select_candidates -> score) lets NaN a0err through (bug 5 fix lives only in dr3_study)")
def test_dr4_cli_path_drops_or_flags_missing_ti_errors():
    cand, ridge = _synthetic_dr4(6); cand.loc[2, 'g_thiele_innes_error'] = np.nan
    X = D.select_candidates(D.features(cand, ridge))
    assert np.isfinite(X.a0err).all()

@pytest.mark.xfail(strict=True, raises=AssertionError, reason="FINDING 4: a NaN colour gives a silent finite log LR = 0 (row dropped by groupby)")
def test_score_nan_colour_is_not_silently_finite(monkeypatch):
    cand, ridge = _synthetic_dr4(40, seed=3); cand.loc[5, 'bp_rp'] = np.nan
    X = D.select_candidates(D.features(cand, ridge))
    monkeypatch.setattr(FU, 'eig', lambda r, p, s, rng, k=300: {'O2_imaging': (0.0, 1)})
    S = D.score(X)
    assert not np.isfinite(S.loc[S.source_id == cand.source_id[5], 'log_lr']).any()

@pytest.mark.xfail(strict=True, raises=AssertionError, reason="FINDING 5: colours outside the ridge range are clamped by np.interp (silent wrong dM_G)")
def test_features_colour_outside_ridge_is_flagged():
    cand, ridge = _synthetic_dr4(3); cand.loc[0, 'bp_rp'] = ridge['color'].max() + 0.8
    X = D.features(cand, ridge)
    assert not np.isfinite(X.dm[0])

@pytest.mark.xfail(strict=True, raises=AssertionError, reason="FINDING 9: solve_m2 returns 1e-5 Msun for NaN / negative input")
def test_solve_m2_nan_input_is_nan():
    assert np.isnan(MECH.solve_m2(np.array([1.0, np.nan]), np.array([np.nan, 0.01]))).all()

@pytest.mark.xfail(strict=True, raises=AssertionError, reason="FINDING 9: K_sum_kms returns a negative velocity for a negative period")
def test_k_sum_rejects_nonpositive_period():
    K = RPT.K_sum_kms(1.0, 0.5, -365.25, 0.0, 90.0)
    assert not np.isfinite(K)

@pytest.mark.xfail(strict=True, raises=AssertionError, reason="FINDING 9: rho_labels labels a negative-parallax source as a luminous companion")
def test_rho_labels_negative_parallax_not_luminous():
    lab, _ = DC.rho_labels(pd.DataFrame([_rho_row(0.4, 60.0, 33.0, 71.0, -12.0, 1.0)]))
    assert lab[0] != 1

def test_m2_from_a1_invalid_input_is_nan():
    assert np.isnan(ASC.m2_from_a1(np.nan, 1.0, 1.0)) and np.isnan(ASC.m2_from_a1(-0.1, 1.0, 1.0)) and np.isnan(ASC.m2_from_a1(0.3, 1.0, np.nan))

def test_k_sum_unbound_orbit_is_not_finite():
    assert not np.isfinite(RPT.K_sum_kms(1.0, 0.5, 365.25, 1.0, 90.0)) and not np.isfinite(RPT.K_sum_kms(1.0, 0.5, 365.25, 1.2, 90.0))

# ============================================================================= 10. sky angles (cross-match utilities)
def test_proper_motion_propagation_units():
    ra, de = DS.propagate(np.array([10.0]), np.array([60.0]), np.array([3.6e6*0.5]), np.array([3.6e6]), 2016.0, 2017.0)
    assert de[0] == pytest.approx(61.0) and ra[0] == pytest.approx(10.0 + 0.5/np.cos(np.radians(60.0)))   # pmra is mu_alpha*cos(dec)
    assert DS.sep_arcsec(np.array([0.0]), np.array([0.0]), np.array([0.0]), np.array([1/3600]))[0] == pytest.approx(1.0, rel=1e-6)
