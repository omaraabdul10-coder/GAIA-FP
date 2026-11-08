"""Sensitivity tests. All tables/matrices are SYNTHETIC (analytic M_G(m) relations, invented covariances); no real isochrone or Gaia data."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src')); sys.path.insert(0, os.path.dirname(__file__))
try: import pytest
except ImportError: import _minipytest as pytest
import numpy as np, sensitivity as S

def parsec(offset=0.0, ages=(9.0, 9.5), mhs=(-0.1, 0.0)):
    L = ['# synthetic PARSEC-like table (NOT a real isochrone)', '#Zini MH logAge Mini int_IMF Mass logL logTe logg label Gmag G_BPmag G_RPmag']
    for a in ages:
        for mh in mhs:
            for m in np.linspace(0.3, 1.5, 13):
                g = 9.0 - 8.0 * np.log10(m) + offset + 0.3 * (a - 9.0) + 0.5 * mh
                L.append(f'0.01 {mh} {a} {m:.4f} 0 {m:.4f} 0 3.7 4.5 1 {g:.4f} {g+.5:.4f} {g-.4:.4f}')
            L.append('0.01 %s %s 1.6 0 1.6 0 3.8 4.0 4 3.0 3.5 2.6' % (mh, a))        # a non-MS point that must be ignored
    L.append('# Table comment trailer'); return '\n'.join(L)

def mist():
    L = ['# synthetic MIST-like table', '# EEP log10_isochrone_age_yr initial_mass [Fe/H] phase Gaia_G_EDR3']
    for m in np.linspace(0.3, 1.5, 13): L.append(f'100 9.0 {m:.4f} 0.0 0 {9.0 - 8.0*np.log10(m):.4f}')
    return '\n'.join(L)

def test_read_parsec_and_mist_formats():
    t = S.read_isochrone_table(parsec()); assert t.attrs['colmap']['G'] == 'Gmag' and t.attrs['colmap']['phase'] == 'label'
    t2 = S.read_isochrone_table(mist()); assert t2.attrs['colmap']['mass'] == 'initial_mass' and t2.attrs['colmap']['feh'] == '[Fe/H]'
    with pytest.raises(S.SensitivityError): S.read_isochrone_table('# nothing\n1 2 3')

def test_mass_relation_main_sequence_only_and_monotone():
    t = S.read_isochrone_table(parsec()); g, m, info = S.mass_relation(t, S.IsoAssumptions('a', 9.0, 0.0))
    assert (np.diff(g) > 0).all() and (np.diff(m) < 0).all() and m.max() <= 1.5 + 1e-9 and info['n_points'] == 13

def test_age_and_metallicity_assumptions_change_mass():
    t = S.read_isochrone_table(parsec()); A = [S.IsoAssumptions('ref', 9.0, 0.0), S.IsoAssumptions('older', 9.5, 0.0), S.IsoAssumptions('poor', 9.0, -0.1)]
    c = S.compare_assumptions([8.5, 9.5, 11.0], t, A, 'ref')
    assert c['vs_reference']['ref']['max_abs_diff'] == 0 and c['vs_reference']['older']['max_abs_diff'] > 0 and c['vs_reference']['poor']['max_abs_diff'] > 0

def test_extinction_requires_law_and_shifts_masses():
    t = S.read_isochrone_table(parsec())
    with pytest.raises(S.SensitivityError, match='ag_over_av'): S.mass_relation(t, S.IsoAssumptions('x', 9.0, 0.0, av=1.0))
    c = S.compare_assumptions([10.0], t, [S.IsoAssumptions('ref', 9.0, 0.0), S.IsoAssumptions('red', 9.0, 0.0, av=1.0, ag_over_av=0.8)], 'ref')
    assert c['mass_msun']['red'][0] > c['mass_msun']['ref'][0]       # extinguished star is intrinsically brighter -> more massive

def test_grid_tolerance_out_of_grid_nan_and_threshold_flips():
    t = S.read_isochrone_table(parsec())
    with pytest.raises(S.SensitivityError, match='nearest grid'): S.mass_relation(t, S.IsoAssumptions('x', 10.5, 0.0))
    c = S.compare_assumptions([-20.0, 10.0], t, [S.IsoAssumptions('ref', 9.0, 0.0), S.IsoAssumptions('old', 9.5, 0.0)], 'ref', thresholds_msun=[0.9])
    assert np.isnan(c['mass_msun']['ref'][0]) and c['vs_reference']['ref']['n_out_of_grid'] == 1 and 'n_side_change@0.9' in c['vs_reference']['old']

def test_null_calibration_reproducible_and_never_claims_completion():
    a = S.null_calibration(n_rep=40, n_boot=200, seed=5); b = S.null_calibration(n_rep=40, n_boot=200, seed=5)
    assert a == b and a['scientific_calibration_complete'] is False and a['data'].startswith('SYNTHETIC') and 'NOT a completed' in a['status']
    assert set(a['rejection']) == {'0.05', '0.025'} and sum(a['decile_counts']) == 40
    d = S.null_calibration(n_rep=20, n_boot=100, statistic='dauc', seed=1); assert d['rho'] == 0.7
    with pytest.raises(S.SensitivityError): S.null_calibration(statistic='nope')

def test_wilson_interval_sane():
    lo, hi = S.wilson(5, 100); assert lo < .05 < hi and 0 <= lo and hi <= 1

MU = [1.0, 2.0, -1.5, 0.8]; ERR = np.array([.1, .1, .1, .1])
def corr(r): C = np.eye(4); C[0, 3] = C[3, 0] = r; C[1, 2] = C[2, 1] = -r; return C
def corr_ab_fg(r): C = np.eye(4); C[0, 1] = C[1, 0] = r; C[2, 3] = C[3, 2] = r; return C

def test_covariance_validation():
    C = S.covariance_from_corr(ERR, corr(.8)); assert np.allclose(C, C.T)
    bad = C.copy(); bad[0, 1] += .5
    with pytest.raises(S.SensitivityError, match='symmetric'): S.validate_covariance(bad)
    nonpsd = S.covariance_from_corr(ERR, corr(.5)) * 1.0; nonpsd[0, 3] = nonpsd[3, 0] = .02    # corr 2 on a 0.1-error diagonal
    with pytest.raises(S.SensitivityError, match='positive semidefinite'): S.validate_covariance(nonpsd)
    with pytest.raises(S.SensitivityError): S.covariance_from_corr(ERR, np.eye(4) * 2)
    with pytest.raises(S.SensitivityError, match='inconsistent'): S.validate_covariance(C, errors=ERR * 2)
    with pytest.raises(S.SensitivityError): S.validate_covariance(np.eye(3))
    fixed = S.nearest_psd(nonpsd); assert np.linalg.eigvalsh(fixed).min() >= -1e-12     # explicit repair only

def test_correlated_sampling_reproduces_requested_correlation_and_diag_flag():
    X, meta = S.sample_ti(MU, cov=S.covariance_from_corr(ERR, corr(.8)), n=100000, seed=1)
    assert meta['full_covariance_used'] and abs(np.corrcoef(X.T)[0, 3] - .8) < .01 and abs(np.corrcoef(X.T)[1, 2] + .8) < .01
    Xd, md = S.sample_ti(MU, errors=ERR, n=100000, seed=1); assert md['diagonal_only'] and abs(np.corrcoef(Xd.T)[0, 3]) < .01
    assert np.allclose(X.mean(0), MU, atol=.005) and np.allclose(X.std(0), ERR, rtol=.02)

def test_singular_psd_covariance_samples_ok():
    C = S.covariance_from_corr(ERR, corr(1.0)); X, _ = S.sample_ti(MU, cov=C, n=2000, seed=0)
    assert np.allclose(X[:, 0] - MU[0], X[:, 3] - MU[3], atol=1e-6)      # perfectly correlated pair

def test_correlated_vs_diagonal_comparison_differs_for_strong_correlation():
    out = S.compare_correlated_vs_diagonal(MU, S.covariance_from_corr(ERR, corr_ab_fg(.9)), n=40000, seed=2)
    # for these synthetic means the A-B / F-G correlation inflates sigma(a0) by ~30% relative to diagonal-only sampling
    assert out['correlated']['a0_median'] > 0 and out['a0_std_ratio_corr_over_diag'] > 1.15 and out['max_abs_corr'] > .8
    same = S.compare_correlated_vs_diagonal(MU, np.diag(ERR**2), n=40000, seed=2); assert abs(same['a0_std_ratio_corr_over_diag'] - 1) < .03
