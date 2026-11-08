"""A2 statistics audit tests (synthetic data only; never reads sealed labels).
Run from GAIA-FP/audit:  PYTHONDONTWRITEBYTECODE=1 python -m pytest tests_stats.py -q -p no:cacheprovider
Tests marked xfail(strict=True) expose a real bug (FINDING n in A2_stats_report.md); they must fail until it is fixed."""
import sys, os, warnings
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import numpy as np, pandas as pd, pytest
from scipy.stats import binomtest
from sklearn.metrics import roc_auc_score
from scipy.special import expit


# ------------------------------------------------------------------ null calibration of z
def _null_z(n, sm, rng, reps):
    import dr4_pipeline as D
    out = []
    for _ in range(reps):
        P = np.exp(rng.uniform(np.log(30), np.log(3000))); e = rng.uniform(0, .8)
        t = np.sort(rng.uniform(0, 2000, n)); w = 11.0 + rng.normal(0, sm, n)
        out.append(D.rvs_z(t, w, P, e, rng.uniform(0, P), rng.uniform(0, 360))[0])
    return np.array(out)

@pytest.mark.parametrize('n', [6, 10, 20, 40])
def test_z_null_sd_is_one(n):
    z = _null_z(n, 5.0, np.random.default_rng(n), 4000)
    assert abs(z.mean()) < 0.06 and abs(z.std() - 1) < 0.05

@pytest.mark.xfail(strict=True, reason='FINDING 9: null upper tail of z heavier than N(0,1) (P(z>2.326) ~1.5-2%)')
def test_z_null_upper_tail_matches_normal():
    z = _null_z(20, 5.0, np.random.default_rng(1), 20000)
    assert np.mean(z > 2.326) < 0.013

def test_rvs_z_short_series_is_nan():
    import dr4_pipeline as D
    assert np.isnan(D.rvs_z(np.arange(5.), np.full(5, 11.), 400., .3, 0., 30.)[0])

@pytest.mark.xfail(strict=True, reason='FINDING 13: constant widths return z = 0.0 (evidence) instead of NaN (no information)')
def test_rvs_z_constant_widths_not_finite_evidence():
    import dr4_pipeline as D
    assert not np.isfinite(D.rvs_z(np.linspace(0, 2000, 20), np.full(20, 11.), 400., .3, 0., 30.)[0])


# ------------------------------------------------------------------ RVS likelihood (rvs_predict)
def _row(z, **kw):
    r = dict(nep=39, z=z, M=0.60, P=216., e=0.20, inc=160., T0=0., om=30., srv=5.0, span=2000., sigP=0.01); r.update(kw)
    return pd.Series(r)

@pytest.mark.xfail(strict=True, reason='FINDING 2: LLR_RVS(z) is not monotone; strong phase signal (z>~8) scored as planet evidence')
def test_llr_rvs_monotone_in_z():
    import rvs_predict as RP
    L = [RP.llr_rvs_physics(_row(z), n_draw=400, rng=np.random.default_rng(0)) for z in (2, 4, 6, 8, 10, 14)]
    assert np.all(np.diff(L) >= -1e-9)

@pytest.mark.xfail(strict=True, reason='FINDING 3: 40-draw KDE Monte Carlo noise: seed SD of log LR >> 0.3 nat at z = 4')
def test_llr_rvs_mc_noise_small():
    import rvs_predict as RP
    v = [RP.llr_rvs_physics(_row(4.0, P=568., e=.29, inc=38., M=.74, nep=23), rng=np.random.default_rng(s)) for s in range(8)]
    assert np.std(v) < 0.3

@pytest.mark.xfail(strict=True, reason='FINDING 4: llr_rvs result for a candidate depends on the order of the other rows')
def test_llr_rvs_order_independent():
    import lik
    X = pd.DataFrame([_row(2.0, P=p, e=e) for p, e in ((216, .2), (568, .29), (894, .5), (1200, .1), (300, .4))])
    a = lik.llr_rvs(X, seed=0); b = lik.llr_rvs(X.iloc[::-1].reset_index(drop=True), seed=0)[::-1]
    assert np.allclose(a, b)

@pytest.mark.xfail(strict=True, reason='FINDING 14: invalid input (e NaN / M<0) silently gives log LR = 0 instead of an error')
def test_llr_rvs_invalid_input_fails_loudly():
    import rvs_predict as RP
    with pytest.raises(Exception):
        RP.llr_rvs_physics(_row(2.0, e=np.nan), rng=np.random.default_rng(0))


# ------------------------------------------------------------------ K units (dark_companion / vbroad_v2)
def test_K_sum_days_convention():
    from rvs_phase_test import K_sum_kms
    assert abs(K_sum_kms(1.0, 1e-9, 365.25, 0., 90.) - 29.785) < 0.01

@pytest.mark.xfail(strict=True, reason='FINDING 1: dark_companion.lr_vbroad passes P in years to K_sum_kms (K x7.148)')
def test_lr_vbroad_uses_days():
    import dark_companion as DC
    called = {}
    orig = DC.K_sum_kms
    def spy(M1, M2, P, e, inc): called['P'] = np.asarray(P).ravel()[0]; return orig(M1, M2, P, e, inc)
    DC.K_sum_kms = spy
    try:
        n = 1; W = np.full((n, DC.QG.size), 1.0/DC.QG.size)
        DC.lr_vbroad(np.r_[12.], np.r_[1.], np.r_[9.], np.r_[2.], np.r_[0.8], np.r_[500.], np.r_[.2], np.r_[60.], np.r_[.5], W)
    finally:
        DC.K_sum_kms = orig
    assert abs(called['P'] - 500.) < 1e-9


# ------------------------------------------------------------------ AUC, Clopper-Pearson, operating point, Brier
def test_auc_matches_sklearn_with_ties():
    import blind_eval as BE, dark_companion as DC, dr4_evaluate as EV
    rng = np.random.default_rng(0)
    for _ in range(200):
        n = int(rng.integers(6, 60)); y = (rng.random(n) < .4).astype(int)
        if y.sum() in (0, n): continue
        s = rng.integers(0, 4, n).astype(float); ref = roc_auc_score(y, s)
        assert abs(BE.roc_auc(s, y) - ref) < 1e-12 and abs(DC.auc(s, y) - ref) < 1e-12 and abs(EV.auc(s, y) - ref) < 1e-12

def test_clopper_pearson_matches_scipy():
    import blind_eval as BE, dr4_evaluate as EV
    for n in range(1, 70):
        for k in range(n+1):
            ci = binomtest(k, n).proportion_ci(0.95, 'exact')
            for f in (BE.clopper_pearson, EV.clopper_pearson):
                lo, hi = f(k, n); assert abs(lo - ci.low) < 1e-10 and abs(hi - ci.high) < 1e-10

@pytest.mark.xfail(strict=True, reason='FINDING 15: clopper_pearson silently returns NaN for k>n or k<0')
def test_clopper_pearson_rejects_invalid():
    import blind_eval as BE
    with pytest.raises(Exception): BE.clopper_pearson(3, 2)

@pytest.mark.xfail(strict=True, reason='FINDING 5: rejection at 95% retention uses interpolated quantile; achieved retention 92.3% for 26 substellar')
@pytest.mark.parametrize('n_sub', [26, 13, 12])
def test_operating_point_achieves_nominal_retention(n_sub):
    import blind_eval as BE, dr4_evaluate as EV
    s0 = np.sort(np.random.default_rng(n_sub).normal(0, 1, n_sub))
    y = np.r_[np.zeros(n_sub, int), np.ones(5, int)]; s = np.r_[s0, np.full(5, 9.)]
    op = BE.operating_point(s, y, 0.95); kept = op['planet_retention'][0]
    thr = np.quantile(s0, 0.95)       # dr4_evaluate.rejection_at_retention uses the same threshold
    assert kept/n_sub >= 0.95 and np.mean(s0 <= thr) >= 0.95

@pytest.mark.xfail(strict=True, reason='FINDING 6: blind_eval.roc_auc returns a finite wrong AUC when a score is NaN')
def test_roc_auc_nan_fails_loudly():
    import blind_eval as BE
    s = np.r_[np.nan, 11., 12., 13., 14., 0., 1., 2., 3., 4.]; y = np.r_[np.ones(5), np.zeros(5)].astype(int)
    assert not np.isfinite(BE.roc_auc(s, y))

@pytest.mark.xfail(strict=True, reason='FINDING 6: rejection_at_retention returns 0.0 if a substellar score is NaN')
def test_rejection_at_retention_nan_fails_loudly():
    import dr4_evaluate as EV
    s = np.r_[np.nan, np.zeros(11), np.full(10, 5.)]; y = np.r_[np.zeros(12), np.ones(10)].astype(int)
    assert not np.isfinite(EV.rejection_at_retention(s, y))

@pytest.mark.xfail(strict=True, reason='FINDING 15: calibration()/Brier accept scores outside [0,1]')
def test_calibration_rejects_non_probabilities():
    import blind_eval as BE
    with pytest.raises(Exception): BE.calibration(np.array([-3., .5, 4., .1]), np.array([0, 1, 1, 0]))

def test_brier_and_reliability_basic():
    import blind_eval as BE
    p = np.array([.1, .1, .9, .9, .5]); y = np.array([0, 1, 1, 1, 0])
    tab, br = BE.calibration(p, y)
    assert abs(br - np.mean((p-y)**2)) < 1e-12 and sum(r[2] for r in tab) == 5

def test_stratified_boot_never_empty_class():
    import dark_companion as DC
    y = np.r_[1, np.zeros(30, int)]; v = DC.boot(lambda i: y[i].sum(), y, n=200)
    assert min(v) == 1

def test_holm_stepdown():
    import dr4_evaluate as EV
    r = EV.holm({'a': 0.001, 'b': 0.02, 'c': 0.013}, alpha=0.025)
    assert r['a']['rejected'] and not r['c']['rejected'] and not r['b']['rejected']

def test_three_way_verdict_boundaries():
    import dr4_pipeline as D
    assert 1 - D.T_ABSTAIN == 0.85


# ------------------------------------------------------------------ EM
def test_em_recovers_covariate_prior():
    import hier_em as H
    rng = np.random.default_rng(3); n = 4000; F = rng.normal(size=(n, 2)); pit = expit(1.5*F[:, 0] - .8); y = rng.random(n) < pit
    L = 2.0*np.where(y, rng.normal(1, 1, n), rng.normal(-1, 1, n))
    r, pi = H.em(L, (F - F.mean(0))/F.std(0))
    assert abs(pi.mean() - pit.mean()) < 0.03 and np.corrcoef(pi, pit)[0, 1] > 0.95 and (r >= 0).all() and (r <= 1).all()

def test_em_start_independent():
    import hier_em as H
    rng = np.random.default_rng(4); n = 2000; y = rng.random(n) < .3; L = 2*np.where(y, rng.normal(1, 1, n), rng.normal(-1, 1, n))
    F = rng.normal(size=(n, 2)); a, _ = H.em(L, F, pi0=0.05); b, _ = H.em(L, F, pi0=0.9)
    assert np.max(np.abs(a - b)) < 1e-3

def test_prior_select_constant_when_uninformative():
    import prior_select as PS
    rng = np.random.default_rng(0); n = 3000; F = rng.normal(size=(n, 3)); y = rng.random(n) < .3
    L = np.where(y, rng.normal(1.5, 1.5, n), rng.normal(-1.5, 1.5, n))
    assert PS.select(L, F)[0] == 0.0

@pytest.mark.xfail(strict=True, reason='FINDING 8: phi contains G and ln d (exact linear combination = M_G); EM prior re-learns CMD evidence')
def test_em_prior_does_not_relearn_cmd():
    import hier_em as H
    rng = np.random.default_rng(1); n = 3000; yy = rng.random(n) < .3
    d = np.exp(rng.uniform(np.log(20), np.log(300), n)); dm = np.where(yy, -.6, 0) + rng.normal(0, .3, n)
    G = rng.uniform(4, 10, n) + dm + 5*np.log10(d) - 5
    L = (-.5*((dm+.6)/.3)**2) - (-.5*(dm/.3)**2)
    X = pd.DataFrame(dict(G=G, P=np.exp(rng.uniform(5, 7, n)), e=rng.uniform(0, .6, n), d=d, mfit=rng.uniform(2, 60, n)))
    _, pi = H.em(L, H.phi(X))
    assert abs(np.corrcoef(np.log(pi/(1-pi)), dm)[0, 1]) < 0.1


# ------------------------------------------------------------------ pipeline edge cases
def _synthetic_candidates(n=200, seed=7):
    rng = np.random.default_rng(seed); plx = rng.uniform(5, 30, n); P = rng.uniform(200, 1500, n); m1 = rng.uniform(.4, 1., n)
    a0 = (m1*(P/365.25)**2)**(1/3)*rng.uniform(5, 60, n)*9.546e-4/m1*plx
    i, w, W = np.radians(rng.uniform(10, 170, n)), np.radians(rng.uniform(0, 360, n)), np.radians(rng.uniform(0, 360, n))
    A = a0*(np.cos(w)*np.cos(W)-np.sin(w)*np.sin(W)*np.cos(i)); B = a0*(np.cos(w)*np.sin(W)+np.sin(w)*np.cos(W)*np.cos(i))
    F = -a0*(np.sin(w)*np.cos(W)+np.cos(w)*np.sin(W)*np.cos(i)); G = -a0*(np.sin(w)*np.sin(W)-np.cos(w)*np.cos(W)*np.cos(i))
    MGms = np.interp(m1, [.4, 1.], [9.7, 4.6]); MG = MGms + rng.normal(0, .3, n)
    cand = pd.DataFrame(dict(source_id=np.arange(n), nss_solution_type='Orbital', period=P, period_error=.02*P, eccentricity=rng.uniform(0, .6, n),
        t_periastron=rng.uniform(-500, 500, n), a_thiele_innes=A, b_thiele_innes=B, f_thiele_innes=F, g_thiele_innes=G,
        a_thiele_innes_error=.05*a0, b_thiele_innes_error=.05*a0, f_thiele_innes_error=.05*a0, g_thiele_innes_error=.05*a0,
        parallax=plx, parallax_error=.02*plx, significance=20., phot_g_mean_mag=MG + 5*np.log10(1000/plx/10), bp_rp=.5+.3*(MGms-3), ruwe=1.2))
    c = rng.uniform(.5, 3.5, 4000)
    field = pd.DataFrame(dict(phot_g_mean_mag=3+(c-.5)*10/3+rng.normal(0, .3, 4000)+5*np.log10(5), bp_rp=c, parallax=20.))
    return cand, field

@pytest.mark.xfail(strict=True, reason='FINDING 7: dr4_pipeline.score gives log_lr = 0 silently to rows with NaN sig_cmd (groupby drops NaN keys)')
def test_score_nan_sigma_not_silently_neutral():
    import dr4_pipeline as D, followup
    cand, field = _synthetic_candidates(); cand.loc[0, 'bp_rp'] = np.nan
    X = D.select_candidates(D.features(cand, D.fit_ms_ridge(field)))
    orig = followup.eig; followup.eig = lambda r, p, s, rng: {'O1_RV_3ep': (0.1, 3)}
    try:
        try: S = D.score(X)
        except Exception: return            # failing loudly is acceptable
    finally:
        followup.eig = orig
    assert not np.isfinite(S.loc[0, 'log_lr'])

def test_negative_parallax_never_scored():
    import dr4_pipeline as D
    cand, field = _synthetic_candidates(); cand.loc[0, 'parallax'] = -5.
    X = D.select_candidates(D.features(cand, D.fit_ms_ridge(field)))
    assert 0 not in set(X.source_id)

def test_joint_llr_zero_a0err_finite():
    from joint_lr import llr_a0_cmd
    L = llr_a0_cmd(np.r_[.5], np.r_[0.], np.r_[500.], np.r_[.6], np.r_[50.], np.r_[-.3], .3)
    assert np.isfinite(L).all()

@pytest.mark.xfail(strict=True, reason='FINDING 12: importing hier_em silences all warnings process-wide (warnings.filterwarnings("ignore"))')
def test_import_does_not_silence_warnings():
    import subprocess
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')
    code = ("import sys; sys.dont_write_bytecode=True; sys.path.insert(0, %r); import warnings, numpy as np; import hier_em\n"
            "with warnings.catch_warnings(record=True) as w:\n    np.float64(0.)/np.float64(0.)\nprint(len(w))") % src
    r = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, cwd=src, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    assert r.stdout.strip().endswith('1'), r.stdout + r.stderr

@pytest.mark.xfail(strict=True, reason='FINDING 16: followup.eig O3 EIG can be negative (q and n drawn with independent indices; CMD partly double counted)')
def test_eig_nonnegative():
    import followup as FU
    S = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'dr3_candidates_scored.csv'))
    amb = S[(S.P_impostor > .15) & (S.P_impostor < .85)].reset_index(drop=True)
    vals = [FU.eig(amb.iloc[i], amb.P_impostor[i], float(amb.sig_cmd[i]), np.random.default_rng(s))['O3_spec_1ep'][0]
            for i in range(min(120, len(amb))) for s in range(5)]
    assert min(vals) >= -1e-9
