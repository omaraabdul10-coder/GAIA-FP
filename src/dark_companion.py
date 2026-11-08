"""
dark_companion.py: H9 / H10 of DARK_COMPANION_PLAN.md (SHA-256 6bc7c01a..., written before the data download).

REAL DATA: Gaia DR3 (development data; the DR4 test stays blind).
  D3 = every AstroSpectroSB1 solution (parallax/error > 10): physical labels from rho = a0 sin i / (a1 sin i).
  D2 = field stars with vbroad: intrinsic line broadening by colour and G_RVS.
  D1 = vbroad of the 2102 substellar candidates (H9).

Scores (none fitted to labels):
  B2   = -dM_G / sigma_CMD                                  (no a0)
  AMRF = -(a0/plx) / (M1^(1/3) P_yr^(2/3))                  (uses a0)
  VB   = (vbroad - field median) / field robust sigma       (no a0)
  S1   = CMD-LR + vbroad-LR, q posterior from dM_G only     (no a0)   <- primary, H10a
  S2   = joint a0|CMD LR + vbroad-LR, q posterior from a0, dM_G (uses a0, flagged)
Blend model (frozen): vb_pred^2 = vb_int^2 + c * f(1-f) * K_sum^2 * <(cos(nu+w) + e cos w)^2>_t,
with c = 1 (primary). The kernel-variance value c = 4 is reported as a LABELLED sensitivity run.
Run: cd src && python dark_companion.py
"""
import json, numpy as np, pandas as pd
from scipy.stats import norm, rankdata
from scipy.special import logsumexp
import dr4_pipeline as D
from joint_lr import llr_a0_cmd
from rvs_phase_test import K_sum_kms, true_anomaly

REAL, OUT, SEED = '../realdata/', '../results/', 7
MJ = 1/1047.6

# ---------------------------------------------------------------- statistics (rank AUC, stratified bootstrap)
def auc(s, y):
    s, y = np.asarray(s, float), np.asarray(y, int); r = rankdata(s); n1 = y.sum(); n0 = len(y) - n1
    return float((r[y == 1].sum() - n1*(n1+1)/2)/(n1*n0))

def boot(fn, y, n=2000, seed=SEED):
    rng = np.random.default_rng(seed); pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    return [fn(np.r_[rng.choice(pos, len(pos)), rng.choice(neg, len(neg))]) for _ in range(n)]

def auc_ci(s, y):
    v = boot(lambda i: auc(s[i], y[i]), y); return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]

def dauc_ci(s1, s2, y):
    v = boot(lambda i: auc(s1[i], y[i]) - auc(s2[i], y[i]), y)
    return [float(auc(s1, y) - auc(s2, y)), float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]

# ---------------------------------------------------------------- vbroad field calibration
def vb_field(field, nc=15):
    f = field[np.isfinite(field.vbroad) & np.isfinite(field.bp_rp) & np.isfinite(field.grvs_mag) & (field.vbroad_nb_transits >= 5)]
    ce = np.quantile(f.bp_rp, np.linspace(0, 1, nc+1)); ge = np.array([-np.inf, 10.0, 11.0, np.inf])
    tab = {}
    for i in range(nc):
        for j in range(3):
            m = (f.bp_rp >= ce[i]) & (f.bp_rp <= ce[i+1]) & (f.grvs_mag > ge[j]) & (f.grvs_mag <= ge[j+1]); x = f.vbroad[m].values
            if len(x) >= 30: med = np.median(x); tab[(i, j)] = (med, 1.4826*np.median(np.abs(x-med)), len(x))
    return ce, ge, tab

def vb_lookup(cal, c, g):
    ce, ge, tab = cal; i = np.clip(np.searchsorted(ce, c) - 1, 0, len(ce)-2); j = np.clip(np.searchsorted(ge, g) - 1, 0, 2)
    med = np.full(len(c), np.nan); sig = np.full(len(c), np.nan)
    for k in range(len(c)):
        v = tab.get((int(i[k]), int(j[k])))
        if v is None:                        # nearest populated grvs bin in the same colour bin
            v = next((tab[(int(i[k]), jj)] for jj in (1, 0, 2) if (int(i[k]), jj) in tab), None)
        if v is not None: med[k], sig[k] = v[0], v[1]
    return med, sig

# ---------------------------------------------------------------- likelihood pieces
QG, NG = np.meshgrid(np.linspace(0.1, 1.0, 120), np.linspace(2.0, 6.0, 9)); QG, NG = QG.ravel(), NG.ravel()
MU = -2.5*np.log10(1 + QG**NG)

def phase_avg(e, om_deg, n=64):
    M = np.linspace(0, 2*np.pi, n, endpoint=False); w = np.radians(om_deg)
    nu = true_anomaly(M[None, :]*1.0, 2*np.pi, np.minimum(e, 0.95)[:, None], 0.0)
    return np.mean((np.cos(nu + w[:, None]) + e[:, None]*np.cos(w)[:, None])**2, axis=1)

def lr_cmd_only(dm, s):
    return logsumexp(norm.logpdf(dm[:, None], MU[None, :], s[:, None]), axis=1) - np.log(MU.size) - norm.logpdf(dm, 0, s)

def q_weights(dm, s, a0=None, a0err=None, M=None, P=None, plx=None):
    lw = norm.logpdf(dm[:, None], MU[None, :], s[:, None])
    if a0 is not None:                       # same physics as joint_lr: a0 predicted by (q, n)
        lq = QG**NG; beta = lq/(1+lq); M1 = M[:, None]/(1+lq)**(1/NG)
        arel = ((M1*(1+QG))*(P[:, None]/365.25)**2)**(1/3); a0t = arel*np.abs(QG/(1+QG)-beta)*plx[:, None]
        sa = np.sqrt(a0err**2 + (a0*0.08/3)**2)[:, None]; lw = lw + norm.logpdf(a0[:, None], a0t, sa)
    return np.exp(lw - logsumexp(lw, axis=1, keepdims=True))

def lr_vbroad(vb, vberr, med, sig, M, P, e, inc, pavg, W, c=1.0):
    """log p(vb | luminous blend) - log p(vb | dark companion); q,n averaged with posterior weights W."""
    lq = QG**NG; f = lq/(1+lq); M1 = M[:, None]/(1+lq)**(1/NG); M2 = QG*M1
    K = K_sum_kms(M1, M2, P[:, None]/365.25, np.minimum(e, 0.95)[:, None], inc[:, None])
    vpred = np.sqrt(med[:, None]**2 + c*f*(1-f)*K**2*pavg[:, None])
    s = np.sqrt(sig**2 + vberr**2)[:, None]
    lt = logsumexp(np.log(np.clip(W, 1e-300, None)) + norm.logpdf(vb[:, None], vpred, s), axis=1)
    return lt - norm.logpdf(vb, med, s[:, 0])

# ---------------------------------------------------------------- H10
def rho_labels(X, n_mc=200, seed=SEED):
    rng = np.random.default_rng(seed); n = len(X)
    g = lambda k: X[k].values[:, None] + X[k+'_error'].values[:, None]*rng.standard_normal((n, n_mc))
    A, B, F, G = g('a_thiele_innes'), g('b_thiele_innes'), g('f_thiele_innes'), g('g_thiele_innes')
    C, H = g('c_thiele_innes'), g('h_thiele_innes'); plx = g('parallax')
    a0, inc, _, _ = D.campbell(A, B, F, G)
    rho = (a0/plx)*np.sin(np.radians(inc))/np.hypot(C, H)
    lo, hi = np.nanpercentile(rho, 2.5, axis=1), np.nanpercentile(rho, 97.5, axis=1)
    lab = np.where(hi < 0.9, 1, np.where(lo > 0.9, 0, -1))
    return lab, np.nanmedian(rho, axis=1)

def h10(d3, field_cmd, cal, c=1.0):
    X = d3.drop_duplicates('source_id').reset_index(drop=True)
    sealed = set(pd.read_csv(REAL+'excluded_sealed_ids.csv').source_id)
    X = X[~X.source_id.isin(sealed)].reset_index(drop=True)
    n0 = len(X)
    ridge = D.fit_ms_ridge(field_cmd)
    X['MG'] = X.phot_g_mean_mag + 5*np.log10(X.parallax/100)
    if 'm1' not in X: X['m1'] = D.mass_from_MG(X.MG.values)   # deviation 10 (VizieR has no binary_masses)
    ms = np.interp(X.bp_rp, ridge['color'], ridge['ridge']); X['sig'] = np.interp(X.bp_rp, ridge['color'], ridge['sigma']); X['dm'] = X.MG - ms
    keep = (X.bp_rp >= ridge['color'].min()) & (X.bp_rp <= ridge['color'].max()) & (X.dm > -2.0) & np.isfinite(X.m1) & (X.m1 > 0)
    keep &= np.isfinite(X[['a_thiele_innes', 'c_thiele_innes', 'h_thiele_innes', 'c_thiele_innes_error', 'a_thiele_innes_error']]).all(1)
    X = X[keep].reset_index(drop=True)
    X['label'], X['rho'] = rho_labels(X)
    a0, inc, om, _ = D.campbell(*(X[k].values for k in ('a_thiele_innes', 'b_thiele_innes', 'f_thiele_innes', 'g_thiele_innes')))
    X['a0'], X['inc'], X['om'] = a0, inc, om
    X['a0err'] = np.sqrt(np.mean([X[k+'_thiele_innes_error'].values**2 for k in 'abfg'], axis=0))
    X['B2'] = -X.dm/X.sig
    X['AMRF'] = -(X.a0/X.parallax)/(X.m1**(1/3)*(X.period/365.25)**(2/3))
    med, sig = vb_lookup(cal, X.bp_rp.values, X.grvs_mag.values); X['vb_med'], X['vb_sig'] = med, sig
    X['VB'] = (X.vbroad - med)/sig
    hasvb = np.isfinite(X.vbroad) & (X.vbroad_nb_transits >= 5) & np.isfinite(med) & (sig > 0)
    L_cmd = lr_cmd_only(X.dm.values, X.sig.values)
    L_joint = llr_a0_cmd(X.a0.values, X.a0err.values, X.period.values, X.m1.values, 1000/X.parallax.values, X.dm.values, X.sig.values[:, None])
    pavg = phase_avg(X.eccentricity.fillna(0).values, X.om.values)
    Lvb1 = np.zeros(len(X)); Lvb2 = np.zeros(len(X)); idx = np.where(hasvb)[0]
    for ch in np.array_split(idx, max(1, len(idx)//2000)):
        sub = X.iloc[ch]
        W1 = q_weights(sub.dm.values, sub.sig.values)
        W2 = q_weights(sub.dm.values, sub.sig.values, sub.a0.values, sub.a0err.values, sub.m1.values, sub.period.values, sub.parallax.values)
        args = (sub.vbroad.values, sub.vbroad_error.fillna(0).values, sub.vb_med.values, sub.vb_sig.values, sub.m1.values,
                sub.period.values, sub.eccentricity.fillna(0).values, sub.inc.values, pavg[ch])
        Lvb1[ch] = lr_vbroad(*args, W1, c=c); Lvb2[ch] = lr_vbroad(*args, W2, c=c)
    X['S1'] = L_cmd + Lvb1; X['S2'] = L_joint + Lvb2; X['CMDLR'] = L_cmd; X['JOINT'] = L_joint
    lab = X.label.values; m = lab >= 0; mv = m & hasvb.values
    res = dict(data='REAL: Gaia DR3 AstroSpectroSB1', c=c, n_query=int(len(d3)), n_unique_after_sealed=int(n0), n_after_cuts=int(len(X)),
               n_labelled=int(m.sum()), n_luminous=int((lab == 1).sum()), n_dark=int((lab == 0).sum()),
               n_labelled_with_vbroad=int(mv.sum()), n_luminous_with_vbroad=int((lab[mv] == 1).sum()))
    y = lab[mv]
    if 0 < y.sum() < len(y):
        S = {k: X[k].values[mv] for k in ('B2', 'AMRF', 'VB', 'S1', 'S2', 'CMDLR', 'JOINT')}
        res['vbroad_subset_auc'] = {k: [auc(v, y)] + auc_ci(v, y) for k, v in S.items()}
        res['H10a_dAUC_S1_minus_B2'] = dauc_ci(S['S1'], S['B2'], y)
        res['H10a_pass'] = res['H10a_dAUC_S1_minus_B2'][1] > 0
        res['H10b_VB_auc'] = res['vbroad_subset_auc']['VB']; res['H10b_pass'] = res['H10b_VB_auc'][1] > 0.5
        res['H10c_dAUC_S2_minus_B2'] = dauc_ci(S['S2'], S['B2'], y)
        res['H10c_dAUC_AMRF_minus_B2'] = dauc_ci(S['AMRF'], S['B2'], y)
    y2 = lab[m]
    res['all_labelled_auc'] = {k: [auc(X[k].values[m], y2)] + auc_ci(X[k].values[m], y2) for k in ('B2', 'AMRF', 'JOINT')}
    return res, X

def h9(d1, cal):
    S = pd.read_csv(OUT+'dr3_candidates_scored.csv')
    V = d1.drop_duplicates('source_id')[['source_id', 'vbroad', 'vbroad_error', 'vbroad_nb_transits', 'grvs_mag']]
    S = S.merge(V, on='source_id', how='left')
    med, sig = vb_lookup(cal, S.bp_rp.values, S.grvs_mag.values); S['VB'] = (S.vbroad - med)/sig
    ok = np.isfinite(S.VB) & (S.vbroad_nb_transits >= 5)
    res = dict(data='REAL: Gaia DR3 substellar candidates', n=int(len(S)), n_with_vbroad=int(ok.sum()))
    y = S.sb2_any.astype(int).values
    res['survey_sb2_with_vbroad'] = int(y[ok].sum())
    try:
        L = pd.read_csv(OUT+'astrospectro_labels.csv')[['source_id', 'label']]; S = S.merge(L, on='source_id', how='left')
        md = ok & (S.label >= 0); res['dynamical_labelled_with_vbroad'] = int(md.sum()); res['dynamical_luminous_with_vbroad'] = int((S.label[md] == 1).sum())
        if 0 < (S.label[md] == 1).sum() < md.sum():
            yy = (S.label[md] == 1).astype(int).values
            res['dynamical_auc'] = {k: auc(S[k][md].values, yy) for k in ('VB',)} | {'B2': auc(-(S.dm/S.sig_cmd)[md].values, yy)}
    except FileNotFoundError:
        pass
    if 0 < y[ok].sum() < ok.sum():
        res['survey_pu_auc'] = {'VB': auc(S.VB[ok].values, y[ok]), 'B2': auc(-(S.dm/S.sig_cmd)[ok].values, y[ok])}
    res['status'] = 'exploratory (fewer than 10 positives)' if y[ok].sum() < 10 else 'reported'
    S.to_csv(OUT+'dr3_candidates_vbroad.csv', index=False)
    return res

def main():
    field_cmd = pd.read_csv(REAL+'dr3_field.csv'); ridge = D.fit_ms_ridge(field_cmd)
    field = pd.read_csv(REAL+'dr3_field_vbroad.csv')
    # deviation 9: the same main-sequence cut as the targets (M_G > ridge - 2.0, colour inside the ridge range)
    MGf = field.phot_g_mean_mag + 5*np.log10(field.parallax/100)
    msf = (field.bp_rp >= ridge['color'].min()) & (field.bp_rp <= ridge['color'].max()) & (MGf > np.interp(field.bp_rp, ridge['color'], ridge['ridge']) - 2.0)
    cal = vb_field(field[msf]); n_field_ms = int(msf.sum())
    out_cal = dict(n_field=len(field), n_field_main_sequence=n_field_ms)
    import os
    have_d3 = os.path.exists(REAL+'dr3_astrospectro_all.csv')
    out = {'calibration_bins': len(cal[2]), **out_cal}
    if have_d3:
        d3 = pd.read_csv(REAL+'dr3_astrospectro_all.csv')
        out['H10'], X = h10(d3, field_cmd, cal, c=1.0)
        out['H10_sensitivity_c4'], _ = h10(d3, field_cmd, cal, c=4.0)
        X.to_csv(OUT+'dark_companion_scored.csv', index=False)
    out['H9'] = h9(pd.read_csv(REAL+'dr3_candidates_vbroad_raw.csv'), cal)
    json.dump(out, open(OUT+'dark_companion.json', 'w'), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))

if __name__ == '__main__':
    main()
