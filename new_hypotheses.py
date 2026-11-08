"""
new_hypotheses.py: secondary hypotheses H17-H19 of amendment v0.6 (A32-A34). Written 7 Nov 2026, before any DR4 data.

H17  Gaia DR4 epoch photometry (independent channel). A stellar companion often modulates the light at the orbital period
     (reflection/eclipses, harmonic 1) or at half of it (ellipsoidal, harmonic 2); a substellar companion practically never
     does at Gaia precision. Flag = F-test of a 2-harmonic Fourier model at the KNOWN orbital period against a constant,
     p < 1e-3. Prediction: the frozen DR4 P_impostor is higher for flagged candidates (AUC > 0.5, one-sided 95% bound).
H18  Compact-object impostors. Among NEW DR4 combined (astrometric + SB1) orbits with dynamical companion mass >= 1.4 Msun
     (neutron-star / black-hole range), most resolved systems show companion light (rho label = luminous), i.e. they are
     not compact objects (inner binaries / triples). Prediction: luminous fraction > 0.5 (one-sided 97.5% Clopper-Pearson).
H19  Brown-dwarf-desert contamination. Among NEW DR4 combined orbits whose ASTROMETRY ALONE (dark-companion assumption)
     gives 13-80 MJ, most resolved systems are luminous stellar companions. Same test as H18.
All three are SECONDARY (not in the weighted-Holm family, never headlined as confirmed).

    python new_hypotheses.py --dev-dr3                                  # DR3 development values (not tests)
    python new_hypotheses.py --h18-h19 ../results/dr4_new_scored.csv    # DR4 day, after dr4_mechanism.py
    python new_hypotheses.py --h17 <frozen DR4 catalogue> <epoch photometry csv>
"""
import json, sys, numpy as np, pandas as pd
from scipy.stats import f as fdist, beta as betadist
from scipy.optimize import brentq

MJ = 0.000954588                      # Jupiter mass in solar masses
SEED, NBOOT = 7, 2000
H17_P_FLAG, H17_MIN_EPOCHS, H17_MIN_FLAGGED, H17_MIN_UNFLAGGED = 1e-3, 20, 5, 10
H18_MIN_LABELLED = 10
COMPACT_MSUN = 1.4
BD_RANGE_MJ = (13.0, 80.0)

# ------------------------------------------------------------------ H17
def harmonic_ftest(t, flux, ferr, period, nharm=2):
    """Weighted least squares: constant vs constant + nharm harmonics of the known period. Returns (F, p, amplitude_frac)."""
    t, y, s = (np.asarray(v, float) for v in (t, flux, ferr))
    ok = np.isfinite(t) & np.isfinite(y) & np.isfinite(s) & (s > 0) & (y > 0)
    t, y, s = t[ok], y[ok], s[ok]
    if len(t) < H17_MIN_EPOCHS: return np.nan, np.nan, np.nan
    med = np.median(y); mad = 1.4826*np.median(np.abs(y - med))
    keep = np.abs(y - med) <= 5*mad if mad > 0 else np.ones(len(y), bool)          # fixed 5-MAD outlier rule
    t, y, s = t[keep], y[keep]/med, s[keep]/med
    if len(t) < H17_MIN_EPOCHS: return np.nan, np.nan, np.nan
    w = 1/s; ph = 2*np.pi*t/period
    X0 = np.ones((len(t), 1)); X1 = np.column_stack([X0] + [f(k*ph) for k in range(1, nharm+1) for f in (np.sin, np.cos)])
    def rss(X):
        c, *_ = np.linalg.lstsq(X*w[:, None], y*w, rcond=None); return np.sum(((y - X@c)*w)**2), c
    r0, _ = rss(X0); r1, c = rss(X1); d1, d2 = X1.shape[1] - 1, len(t) - X1.shape[1]
    if d2 <= 0 or r1 <= 0: return np.nan, np.nan, np.nan
    F = ((r0 - r1)/d1)/(r1/d2)
    amp = float(np.sqrt(np.sum(c[1:]**2)))
    return float(F), float(fdist.sf(F, d1, d2)), amp

def h17_flags(lc, periods):
    """lc: long table source_id, g_obs_time (days), g_flux, g_flux_error. periods: dict source_id -> period (days)."""
    rows = []
    for sid, g in lc.groupby('source_id'):
        P = periods.get(str(sid))
        if P is None or not np.isfinite(P): continue
        F, p, amp = harmonic_ftest(g.g_obs_time.values, g.g_flux.values, g.g_flux_error.values, P)
        rows.append(dict(source_id=str(sid), n_epochs=len(g), F=F, p=p, amp=amp, flag=bool(np.isfinite(p) and p < H17_P_FLAG)))
    return pd.DataFrame(rows)

def _auc(s, y):
    from scipy.stats import rankdata
    r = rankdata(s); n1 = int(y.sum()); n0 = len(y) - n1
    return (r[y == 1].sum() - n1*(n1 + 1)/2)/(n1*n0)

def h17(cat, flags, annual_sensitivity=True):
    D = cat.merge(flags[np.isfinite(flags.p)], on='source_id'); y = D.flag.values.astype(int); s = D.P_impostor.values
    n1, n0 = int(y.sum()), int((y == 0).sum())
    out = dict(n_tested=len(D), n_flagged=n1, n_unflagged=n0)
    if n1 < H17_MIN_FLAGGED or n0 < H17_MIN_UNFLAGGED: return out | dict(status='NOT_CONDUCTED:BELOW_MIN_N')
    rng = np.random.default_rng(SEED); i1, i0 = np.where(y == 1)[0], np.where(y == 0)[0]; bs = []
    for _ in range(NBOOT):
        i = np.r_[rng.choice(i1, len(i1)), rng.choice(i0, len(i0))]; bs.append(_auc(s[i], y[i]))
    bs = np.array(bs)
    out |= dict(status='CONDUCTED', auc=float(_auc(s, y)), ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                p=float((np.sum(bs <= 0.5) + 1)/(NBOOT + 1)))
    out['pass'] = out['ci95'][0] > 0.5
    if annual_sensitivity and 'period' in D:          # periods near 1 yr or the 63-d precession can alias with the scanning law
        m = ~((np.abs(D.period/365.25 - 1) < 0.1) | (np.abs(D.period/62.97 - 1) < 0.1))
        if m.sum() and 0 < y[m].sum() < m.sum(): out['auc_excl_scan_aliases'] = float(_auc(s[m.values], y[m.values]))
    return out

# ------------------------------------------------------------------ H18 / H19
def dark_assumed_m2(a0_mas, plx_mas, period_d, m1):
    """Companion mass if the companion were dark (photocentre = primary orbit)."""
    fm = (np.asarray(a0_mas)/np.asarray(plx_mas))**3/(np.asarray(period_d)/365.25)**2
    return np.array([brentq(lambda m: m**3/(a + m)**2 - f, 1e-7, 1e3) if np.isfinite(f) and f > 0 and np.isfinite(a) else np.nan
                     for a, f in zip(np.asarray(m1, float), fm)])

def fraction_test(lab):
    """lab: rho labels (1 luminous, 0 dark, -1 unresolved). Luminous fraction among resolved, one-sided 97.5% CP lower bound."""
    lab = np.asarray(lab); k, n = int((lab == 1).sum()), int((lab >= 0).sum())
    out = dict(n_total=int(len(lab)), n_resolved=n, n_luminous=k, n_dark=n - k, n_unresolved=int((lab < 0).sum()))
    if n < H18_MIN_LABELLED: return out | dict(status='NOT_CONDUCTED:BELOW_MIN_N')
    lo = float(betadist.ppf(0.025, k, n - k + 1)) if k > 0 else 0.0
    hi = float(betadist.ppf(0.975, k + 1, n - k)) if k < n else 1.0
    return out | dict(status='CONDUCTED', fraction=k/n, ci95=[lo, hi], pass_=lo > 0.5)

def h18_h19(X):
    """X: scored table with label, rho, m1, inc, om, eccentricity, period, parallax, a0, c/h_thiele_innes (dark_companion.h10 output)."""
    import mechanism as M
    Y = M.physics(X)
    Y['m2dark'] = dark_assumed_m2(Y.a0, Y.parallax, Y.period, Y.m1)
    cmp_ = Y[Y.m2dyn >= COMPACT_MSUN]
    bd = Y[(Y.m2dark >= BD_RANGE_MJ[0]*MJ) & (Y.m2dark < BD_RANGE_MJ[1]*MJ)]
    r18 = fraction_test(cmp_.label.values); r18['median_m2dyn_Msun'] = float(cmp_.m2dyn.median()) if len(cmp_) else None
    r19 = fraction_test(bd.label.values)
    lum = bd[bd.label == 1]
    r19['median_true_m2_of_luminous_MJ'] = float((lum.m2dyn/MJ).median()) if len(lum) else None
    return dict(H18=r18, H19=r19), Y

def main(argv):
    sys.path.insert(0, '.')
    if '--dev-dr3' in argv:
        X = pd.read_csv('../results/dark_companion_scored.csv', dtype={'source_id': str})
        res, _ = h18_h19(X)
        res['status'] = 'DRY RUN on DR3 (development values, not a test)'
        res['note'] = ('AstroSpectroSB1 needs a detectable RV orbit, which favours massive companions: the DR3 fractions describe '
                       'that selection, not all Gaia orbits.')
        print(json.dumps(res, indent=1)); json.dump(res, open('../results/new_hypotheses_dev_dr3.json', 'w'), indent=1); return
    if '--h18-h19' in argv:
        X = pd.read_csv(argv[argv.index('--h18-h19') + 1], dtype={'source_id': str})
        res, _ = h18_h19(X); json.dump(res, open('../results/dr4_h18_h19.json', 'w'), indent=1); print(json.dumps(res, indent=1)); return
    if '--h17' in argv:
        i = argv.index('--h17'); cat = pd.read_csv(argv[i+1], dtype={'source_id': str}); lc = pd.read_csv(argv[i+2], dtype={'source_id': str})
        per = dict(zip(cat.source_id, cat.P if 'P' in cat else cat.period))
        fl = h17_flags(lc, per); fl.to_csv('../results/dr4_h17_flags.csv', index=False)
        if 'period' not in cat and 'P' in cat: cat = cat.assign(period=cat.P)
        res = h17(cat[['source_id', 'P_impostor', 'period']], fl)
        json.dump(res, open('../results/dr4_h17.json', 'w'), indent=1); print(json.dumps(res, indent=1)); return
    print(__doc__)

if __name__ == '__main__':
    main(sys.argv[1:])
