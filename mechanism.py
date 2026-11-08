"""
mechanism.py: tests M1-M4 and P0 of MECHANISM_PLAN.md (SHA-256 bc327170..., hashed before this file was run).

REAL DATA: Gaia DR3 AstroSpectroSB1 (results/dark_companion_scored.csv). Status: DEVELOPMENT (DR4 is the confirmatory run).
Question: is the vbroad excess of luminous-companion systems caused by line blending (needs light AND velocity separation),
and is the sample shaped by Gaia's single-lined (SB1) selection?
Run: cd src && python mechanism.py [path_to_scored_csv]
"""
import json, sys, numpy as np, pandas as pd
from scipy.stats import rankdata
import dark_companion as DC
from vbroad_v2 import maxsep_shape

SEED, NBOOT, NPERM = 7, 2000, 200
NPHASE = 4096        # phase samples for pavg/smax (audit A1-F6; the 64 of vbroad_v2 was up to x2.7 off at e = 0.95)
VKMS = 29.7847   # 2 pi AU / yr in km/s

# ---------------------------------------------------------------- per-system physics (no vbroad used)
def solve_m2(m1, A):
    """positive root of m2^3 - A (m1 + m2)^2 = 0 (vectorised bisection)."""
    lo, hi = np.full_like(m1, 1e-5), np.full_like(m1, 200.0)
    for _ in range(80):
        mid = 0.5*(lo + hi); f = mid**3 - A*(m1 + mid)**2
        lo, hi = np.where(f < 0, mid, lo), np.where(f < 0, hi, mid)
    return 0.5*(lo + hi)

def rho_sigma(X, n_mc=200, seed=SEED):
    rng = np.random.default_rng(seed); n = len(X)
    g = lambda k: X[k].values[:, None] + X[k+'_error'].values[:, None]*rng.standard_normal((n, n_mc))
    A, B, F, G = g('a_thiele_innes'), g('b_thiele_innes'), g('f_thiele_innes'), g('g_thiele_innes')
    C, H = g('c_thiele_innes'), g('h_thiele_innes'); plx = g('parallax')
    a0, inc, _, _ = DC.D.campbell(A, B, F, G)
    rho = (a0/plx)*np.sin(np.radians(inc))/np.hypot(C, H)
    return (np.nanpercentile(rho, 97.5, axis=1) - np.nanpercentile(rho, 2.5, axis=1))/3.92

def physics(X):
    X = X.copy()
    e = X.eccentricity.fillna(0).clip(0, 0.95).values; Pyr = X.period.values/365.25; s = np.sin(np.radians(X.inc.values))
    a1sini = np.hypot(X.c_thiele_innes.values, X.h_thiele_innes.values)
    m2 = solve_m2(X.m1.values, (a1sini/np.clip(s, 1e-3, None))**3/Pyr**2)
    B = m2/(X.m1.values + m2)
    X['m2dyn'], X['Bfrac'] = m2, B
    X['beta'] = np.clip(B*(1 - X.rho.values), 0, 0.5)
    X['K1'] = VKMS*a1sini/(Pyr*np.sqrt(1 - e**2)); X['Ksum'] = X.K1/B
    X['pavg'] = DC.phase_avg(e, X.om.values, n=NPHASE); X['smax'] = maxsep_shape(e, X.om.values, n=NPHASE)   # audit A1-F6: 64 -> 4096
    X['b'] = X.beta*(1 - X.beta)*np.minimum(X.Ksum**2*X.pavg, 30.0**2)
    X['k'] = X.K1**2*X.pavg
    X['Kmax'] = X.Ksum*X.smax
    X['logP'] = np.log10(X.period)
    return X

# ---------------------------------------------------------------- statistics
def rk(v): return rankdata(v)/len(v)

def resid(y, Z):
    Z1 = np.c_[np.ones(len(y)), Z]; return y - Z1 @ np.linalg.lstsq(Z1, y, rcond=None)[0]

def pcorr(y, x, Z):
    ry, rx = resid(y, Z), resid(x, Z); return float(np.corrcoef(ry, rx)[0, 1])

def prank(Y, cols):
    return {c: rk(Y[c].values) for c in cols}

def boot_pcorr(R, ycol, xcols, zcols, n=NBOOT, seed=SEED):
    """point estimates and percentile CIs for the partial correlations of ycol with each x in xcols, plus pairwise differences."""
    y = R[ycol]; Z = np.c_[[R[c] for c in zcols]].T
    est = {x: pcorr(y, R[x], Z) for x in xcols}
    rng = np.random.default_rng(seed); N = len(y); bs = {x: [] for x in xcols}
    for _ in range(n):
        i = rng.integers(0, N, N)
        for x in xcols: bs[x].append(pcorr(y[i], R[x][i], Z[i]))
    out = {x: [est[x], float(np.percentile(bs[x], 2.5)), float(np.percentile(bs[x], 97.5))] for x in xcols}
    if len(xcols) == 2:
        a, b = xcols; d = np.array(bs[a]) - np.array(bs[b])
        out[f'{a}_minus_{b}'] = [est[a] - est[b], float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]
    return out

# ---------------------------------------------------------------- M3 forward model of catalogue entry
def forward(X, prior='uniform', ndraw=50, seed=SEED, tau_a=None, tau_k=None):
    rng = np.random.default_rng(seed + (0 if prior == 'uniform' else 1)); n = len(X)
    if prior == 'uniform': q = rng.uniform(0.1, 1.0, (n, ndraw))
    else: q = np.exp(rng.uniform(np.log(0.1), 0.0, (n, ndraw)))
    nn = rng.choice(np.arange(2.0, 6.01, 0.5), (n, ndraw))
    m1 = X.m1.values[:, None]; Pyr = X.period.values[:, None]/365.25
    e = X.eccentricity.fillna(0).clip(0, 0.95).values[:, None]; s = np.sin(np.radians(X.inc.values))[:, None]
    m2 = q*m1; arel = ((m1 + m2)*Pyr**2)**(1/3); B = m2/(m1 + m2); lq = q**nn; beta = lq/(1 + lq)
    a0 = arel*np.abs(B - beta)*X.parallax.values[:, None]
    K1 = VKMS*arel*B*s/(Pyr*np.sqrt(1 - e**2)); Ksum = K1/B; Kmax = Ksum*X.smax.values[:, None]
    det = (a0/X.a0err.values[:, None] >= tau_a) & (K1 >= tau_k)
    rho = 1 - beta/B + X.rho_sig.values[:, None]*rng.standard_normal((n, ndraw))
    bhat = np.clip(B*(1 - rho), 0, 0.5)
    return det, bhat, Kmax

def ratio(bhat, Kmax, w):
    hi, lo = (Kmax >= 30) & w, (Kmax < 15) & w
    fh = (bhat[hi] >= 0.2).mean() if hi.sum() else np.nan; fl = (bhat[lo] >= 0.2).mean() if lo.sum() else np.nan
    return fh/fl, fh, fl, int(hi.sum()), int(lo.sum())

def m3(Y, prior, seed=SEED):
    tau_a = np.percentile(Y.a0/Y.a0err, 1); tau_k = np.percentile(Y.K1, 1)
    det, bh, Km = forward(Y, prior, tau_a=tau_a, tau_k=tau_k)
    obs = ratio(Y.beta.values, Y.Kmax.values, np.ones(len(Y), bool)); mod = ratio(bh, Km, det)
    rng = np.random.default_rng(seed); D = []
    for _ in range(NBOOT):
        i = rng.integers(0, len(Y), len(Y))
        ro = ratio(Y.beta.values[i], Y.Kmax.values[i], np.ones(len(i), bool))[0]
        rm = ratio(bh[i], Km[i], det[i])[0]; D.append(ro/rm)
    D = np.array(D); D = D[~np.isnan(D)]                           # audit A2-F17: keep +inf replicates (extreme values), drop only 0/0
    if len(D) < 0.5*NBOOT:                                        # too few bright companions in a bin (small samples): no verdict
        D = np.array([np.nan])
    return dict(prior=prior, tau_a0_snr=float(tau_a), tau_K1=float(tau_k), detected_fraction=float(det.mean()),
                observed=dict(ratio=obs[0], f_high=obs[1], f_low=obs[2], n_high=obs[3], n_low=obs[4]),
                model_no_sb2_selection=dict(ratio=mod[0], f_high=mod[1], f_low=mod[2], n_high=mod[3], n_low=mod[4]),
                D=[float(obs[0]/mod[0]), float(np.percentile(D, 2.5)), float(np.percentile(D, 97.5))],
                pass_=bool(not np.isnan(D).any() and np.percentile(D, 97.5) < 0.5))

# ---------------------------------------------------------------- main
def retire_pre_erratum_s1(Y):
    """Prevent the legacy, pre-period-unit-fix S1 column from being mistaken for a valid score.

    H12/H13/H14 mechanism statistics do not use S1. The corrected H10 S1 comparison is
    separately generated by erratum_k_units.py and recorded in results/erratum_k_units.json.
    """
    if 'S1' in Y.columns and 'S1_pre_erratum_DO_NOT_USE' not in Y.columns:
        Y = Y.rename(columns={'S1': 'S1_pre_erratum_DO_NOT_USE'})
    return Y

def main(path='../results/dark_companion_scored.csv'):
    X = pd.read_csv(path, dtype={'source_id': str})
    X['rho_sig'] = rho_sigma(X)
    X = physics(X)
    V = np.isfinite(X.vbroad) & (X.vbroad_nb_transits >= 5) & np.isfinite(X.vb_med) & (X.vb_sig > 0) & np.isfinite(X.VB)
    V &= np.isfinite(X[['b', 'k', 'beta', 'Kmax', 'grvs_mag', 'bp_rp', 'logP', 'eccentricity', 'dm', 'rho_sig']]).all(1)
    Y = X[V].reset_index(drop=True)
    out = dict(data='REAL: Gaia DR3 AstroSpectroSB1', status='DEVELOPMENT (DR3); confirmatory = DR4',
               plan_sha256='bc3271705233ea7ebd13a53a64814254cee62c9716cd58e6d2596540b388ddca', n_V=int(len(Y)))
    cov1 = ['grvs_mag', 'bp_rp', 'logP', 'eccentricity']; cov2 = cov1 + ['dm']
    R = prank(Y, ['VB', 'b', 'k'] + cov2)
    out['M1_and_M2b'] = boot_pcorr(R, 'VB', ['b', 'k'], cov1)
    out['M1'] = out['M1_and_M2b']['b']; out['M1_pass'] = out['M1'][1] > 0
    out['M2b'] = out['M1_and_M2b']['b_minus_k']; out['M2b_pass'] = out['M2b'][1] > 0
    out['M1s_with_dM'] = boot_pcorr(R, 'VB', ['b'], cov2)['b']
    dark = (Y.label == 0).values; Yd = Y[dark].reset_index(drop=True); Rd = prank(Yd, ['VB', 'k'] + cov1)
    out['n_dark'] = int(dark.sum())
    out['M2a_dark_k'] = boot_pcorr(Rd, 'VB', ['k'], cov1)['k']
    out['M2a_pass'] = out['M2a_dark_k'][2] < 0.10; out['A5_supported'] = out['M2a_dark_k'][1] > 0.10
    out['M3'] = m3(Y, 'uniform'); out['M3_sensitivity_logq'] = m3(Y, 'logq')
    sel = (Y.b >= 25).values; ratio_c = ((Y.vbroad**2 - Y.vb_med**2)/Y.b).values[sel]
    rng = np.random.default_rng(SEED); bc = [np.median(rng.choice(ratio_c, len(ratio_c))) for _ in range(NBOOT)]
    out['M4_c_hat'] = [float(np.median(ratio_c)), float(np.percentile(bc, 2.5)), float(np.percentile(bc, 97.5))]
    out['M4_n'] = int(sel.sum()); out['M4_consistent_with_theory'] = bool(out['M4_c_hat'][2] >= 2 and out['M4_c_hat'][1] <= 8)
    Z = np.c_[[R[c] for c in cov1]].T; rng = np.random.default_rng(SEED + 1)
    perm = [pcorr(R['VB'][rng.permutation(len(Y))], R['b'], Z) for _ in range(NPERM)]
    out['P0_perm_abs_p99'] = float(np.percentile(np.abs(perm), 99)); out['P0_pass'] = abs(out['M1'][0]) > out['P0_perm_abs_p99']
    out['verdict'] = dict(mechanism_B=bool(out['M1_pass'] and out['M2a_pass'] and out['M2b_pass']),
                          selection_S=bool(out['M3']['pass_']), A5_favoured=bool(out['A5_supported'] and not out['M2b_pass']))
    # descriptive curves for the poster (not tests)
    bins = [0, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5]
    Y['bbin'] = pd.cut(Y.beta, bins, include_lowest=True)
    out['curve_VB_by_beta'] = [dict(bin=str(k), n=int(len(g)), VB_median=float(g.VB.median()), b_median=float(g.b.median()))
                               for k, g in Y.groupby('bbin', observed=True)]
    Y['bdec'] = pd.qcut(Y.b.rank(method='first'), 10, labels=False)
    out['curve_VB_by_b_decile'] = [dict(decile=int(k), n=int(len(g)), b_median=float(g.b.median()), VB_median=float(g.VB.median()),
                                        vbroad_median=float(g.vbroad.median())) for k, g in Y.groupby('bdec')]
    out['power'] = dict(r_min_at_n={str(n): float(2.80/np.sqrt(n - 7)) for n in (200, 500, 1000, 2000, 5000)},
                        n_needed_for_half_M1=int(np.ceil((2.80/(out['M1'][0]/2))**2 + 7)) if out['M1'][0] > 0 else None)
    json.dump(out, open('../results/mechanism.json', 'w'), indent=1, default=float)
    Y = retire_pre_erratum_s1(Y)
    Y.drop(columns=['bbin', 'bdec']).to_csv('../results/mechanism_scored.csv', index=False)
    print(json.dumps({k: v for k, v in out.items() if not k.startswith('curve')}, indent=1, default=float))

if __name__ == '__main__':
    main(*sys.argv[1:])
