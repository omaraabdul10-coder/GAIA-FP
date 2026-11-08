"""
sensitivity.py — sensitivity / uncertainty tooling (task 4).  Does not touch any registered hypothesis, threshold or frozen file.

  A. Mass/isochrone sensitivity  : read PARSEC or MIST tables, build M_G -> mass relations for chosen age / [M/H] / A_V, compare them.
  B. Bootstrap null calibration  : reproducible null simulations of the registered one-sided percentile-bootstrap p rule
                                    (dr4_evaluate.p_one_sided), with Monte-Carlo-uncertainty diagnostics.
  C. Correlated Thiele-Innes     : full 4x4 covariance (validated), correlated vs diagonal-only sampling and the effect on a0 and inclination.

STATUS WORDING: B produces a *diagnostic on a synthetic null*.  `scientific_calibration_complete` is always False here: a completed
calibration needs the real score distributions, the registered n per class, and a pre-stated tolerance, none of which this module decides.
Isochrone tables are NOT bundled; every mass number is conditional on the table, age, [M/H], A_V and A_G/A_V the caller supplies.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
import numpy as np, pandas as pd
from scipy.stats import rankdata, kstest, norm

class SensitivityError(ValueError): pass

# ================================================================== A. isochrones
SYN = dict(age=['logAge', 'log10_isochrone_age_yr'], feh=['MH', '[Fe/H]', 'feh', '[Fe/H]_init'],
           mass=['Mini', 'initial_mass', 'star_mass'], phase=['label', 'phase'],
           G=['Gmag', 'Gaia_G_EDR3', 'Gaia_G_MAW', 'Gaia_G_DR2Rev', 'G'])
MAIN_SEQUENCE = {'label': 1, 'phase': 0}          # PARSEC label 1 = MS; MIST phase 0 = main sequence

def read_isochrone_table(path_or_text, columns=None):
    """Read a PARSEC (CMD web output) or MIST (.iso.cmd) table. Comment lines start with '#'; the column header is the last
    comment line that contains recognisable column names. `columns` may override: dict(age=, feh=, mass=, phase=, G=)."""
    text = path_or_text if '\n' in str(path_or_text) else open(path_or_text).read()
    header, rows = None, []
    known = {c for v in SYN.values() for c in v}
    for line in text.splitlines():
        s = line.strip()
        if not s: continue
        if s.startswith('#'):
            toks = s.lstrip('#').split()
            if len(known & set(toks)) >= 3: header = toks
            continue
        rows.append(s.split())
    if header is None: raise SensitivityError('no header line with recognisable PARSEC/MIST column names (give columns=...)')
    w = {len(r) for r in rows}
    if not rows or w != {len(header)}: raise SensitivityError(f'data rows have widths {sorted(w)} but header has {len(header)} columns')
    df = pd.DataFrame(rows, columns=header).apply(pd.to_numeric, errors='coerce')
    cm = {}
    for k, syn in SYN.items():
        name = (columns or {}).get(k)
        hit = [name] if name else [c for c in syn if c in df.columns]
        if len(hit) != 1 or hit[0] not in df.columns: raise SensitivityError(f'column for {k!r}: matches {hit}; available {list(df.columns)} (override with columns=)')
        cm[k] = hit[0]
    df.attrs['colmap'] = cm
    return df

@dataclass
class IsoAssumptions:
    """All assumptions explicit.  log_age: log10(yr); mh: [M/H] (dex); av: V-band extinction [mag]; ag_over_av: A_G/A_V (must be
    supplied by the caller from a documented extinction law whenever av != 0)."""
    name: str; log_age: float; mh: float; av: float = 0.0; ag_over_av: float | None = None
    age_tol: float = 0.05; mh_tol: float = 0.1; max_mass: float | None = None
    def a_g(self):
        if self.av == 0: return 0.0
        if self.ag_over_av is None: raise SensitivityError(f'{self.name}: av != 0 requires ag_over_av from a documented extinction law')
        return float(self.av) * float(self.ag_over_av)

def mass_relation(table: pd.DataFrame, a: IsoAssumptions):
    """Return (MG_intrinsic_grid ascending, mass_grid, info) for the main sequence at the grid point nearest (age, [M/H])."""
    cm = table.attrs['colmap']; ages = np.sort(table[cm['age']].unique()); fehs = np.sort(table[cm['feh']].unique())
    ia, ih = ages[np.argmin(abs(ages - a.log_age))], fehs[np.argmin(abs(fehs - a.mh))]
    if abs(ia - a.log_age) > a.age_tol: raise SensitivityError(f'{a.name}: requested logAge {a.log_age} but nearest grid {ia} (tol {a.age_tol})')
    if abs(ih - a.mh) > a.mh_tol: raise SensitivityError(f'{a.name}: requested [M/H] {a.mh} but nearest grid {ih} (tol {a.mh_tol})')
    sub = table[(table[cm['age']] == ia) & (table[cm['feh']] == ih) & (table[cm['phase']] == MAIN_SEQUENCE.get(cm['phase'], MAIN_SEQUENCE['label']))]
    sub = sub.dropna(subset=[cm['mass'], cm['G']]).sort_values(cm['mass'])
    if a.max_mass is not None: sub = sub[sub[cm['mass']] <= a.max_mass]
    if len(sub) < 3: raise SensitivityError(f'{a.name}: fewer than 3 main-sequence points at the selected grid')
    m, g = sub[cm['mass']].to_numpy(float), sub[cm['G']].to_numpy(float)
    k = int(np.argmin(g)) + 1                      # cut at the turn-off: MG must fall monotonically with mass
    m, g = m[:k], g[:k]; keep = np.r_[True, np.diff(g) < 0]; n_drop = int((~keep).sum()); m, g = m[keep], g[keep]
    if len(m) < 3: raise SensitivityError(f'{a.name}: monotone M_G(mass) segment has < 3 points')
    g_eff = g + a.a_g()                            # observed-frame M_G = intrinsic + A_G ; invert at observed (extinguished) value
    o = np.argsort(g_eff)
    return g_eff[o], m[o], dict(grid_log_age=float(ia), grid_mh=float(ih), n_points=int(len(m)), n_nonmonotone_dropped=n_drop, a_g=a.a_g(),
                                mg_range=[float(g_eff.min()), float(g_eff.max())])

def compare_assumptions(MG_obs, table, assumptions, reference, thresholds_msun=()):
    """Masses [M_sun] for observed M_G under each assumption set (no extrapolation: NaN outside the grid), differences to `reference`,
    and, if `thresholds_msun` is given, how many objects change side of each threshold relative to the reference."""
    x = np.asarray(MG_obs, float)
    if not np.isfinite(x).all(): raise SensitivityError('non-finite M_G')
    names = [a.name for a in assumptions]
    if reference not in names: raise SensitivityError(f'reference {reference!r} not in {names}')
    out = dict(reference=reference, relations={}, vs_reference={})
    M = {}
    for a in assumptions:
        g, m, info = mass_relation(table, a); M[a.name] = np.interp(x, g, m, left=np.nan, right=np.nan); out['relations'][a.name] = info
    for n in names:
        d = M[n] - M[reference]; both = np.isfinite(d)
        s = dict(n_compared=int(both.sum()), n_out_of_grid=int((~np.isfinite(M[n])).sum()),
                 median_diff=float(np.median(d[both])) if both.any() else None, max_abs_diff=float(np.max(abs(d[both]))) if both.any() else None,
                 median_frac_diff=float(np.median(d[both] / M[reference][both])) if both.any() else None)
        for t in thresholds_msun:
            s[f'n_side_change@{t}'] = int(np.sum((M[n][both] < t) != (M[reference][both] < t)))
        out['vs_reference'][n] = s
    out['mass_msun'] = {n: v.tolist() for n, v in M.items()}
    return out

# ================================================================== B. bootstrap null calibration
def _auc_rows(S, y):
    """AUC for each row of S (n_boot x n) with labels y (n,) shared across rows -> vectorised."""
    R = rankdata(S, axis=1); n1 = int(y.sum()); n0 = len(y) - n1
    return (R[:, y == 1].sum(axis=1) - n1 * (n1 + 1) / 2) / (n1 * n0)

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return float(c - h), float(c + h)

def null_calibration(n_rep=500, n_pos=39, n_neg=26, n_boot=2000, statistic='auc', rho=0.7, alphas=(0.05, 0.025), seed=20261101):
    """Type-I diagnostic for the registered rule p = (#{boot stat <= null} + 1)/(B + 1) (dr4_evaluate.p_one_sided, side='greater').
    statistic='auc'   : null = both classes ~ N(0,1) (AUC = 0.5), as H1 with the registered class sizes (default 39 vs 26).
    statistic='dauc'  : two correlated scores (correlation rho) both uninformative; statistic = AUC(s1) - AUC(s2), null = 0 (H2/A5/H6-type).
    All data are SYNTHETIC noise.  Returns rejection rates with Wilson CIs, a KS test of p against U(0,1), and a decile histogram."""
    if statistic not in ('auc', 'dauc'): raise SensitivityError('statistic must be auc or dauc')
    rng = np.random.default_rng(seed); y = np.r_[np.ones(n_pos, int), np.zeros(n_neg, int)]; n = len(y)
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]; P = np.empty(n_rep)
    for r in range(n_rep):
        s1 = rng.normal(size=n)
        s2 = rho * s1 + np.sqrt(1 - rho**2) * rng.normal(size=n)
        idx = np.concatenate([rng.choice(pos, (n_boot, n_pos)), rng.choice(neg, (n_boot, n_neg))], axis=1)    # stratified, as strat_boot
        yb = np.r_[np.ones(n_pos, int), np.zeros(n_neg, int)]
        stat = _auc_rows(s1[idx], yb) if statistic == 'auc' else _auc_rows(s1[idx], yb) - _auc_rows(s2[idx], yb)
        null = 0.5 if statistic == 'auc' else 0.0
        P[r] = (np.sum(stat <= null) + 1) / (n_boot + 1)
    res = dict(statistic=statistic, n_rep=n_rep, n_pos=n_pos, n_neg=n_neg, n_boot=n_boot, seed=seed, rho=rho if statistic == 'dauc' else None,
               data='SYNTHETIC NULL (pure noise)', rejection={}, ks_vs_uniform_p=float(kstest(P, 'uniform').pvalue),
               decile_counts=np.histogram(P, bins=np.linspace(0, 1, 11))[0].tolist(), p_median=float(np.median(P)))
    for a in alphas:
        k = int(np.sum(P <= a)); lo, hi = wilson(k, n_rep)
        res['rejection'][str(a)] = dict(rate=k / n_rep, wilson95=[lo, hi], nominal_inside_wilson95=bool(lo <= a <= hi))
    res['scientific_calibration_complete'] = False
    res['status'] = 'IMPLEMENTED_AND_TESTED_DIAGNOSTIC (synthetic null); NOT a completed scientific calibration'
    return res

# ================================================================== C. correlated Thiele-Innes errors
TI_NAMES = ('A', 'B', 'F', 'G')

def covariance_from_corr(errors, corr):
    e = np.asarray(errors, float); C = np.asarray(corr, float)
    if e.shape != (4,) or C.shape != (4, 4): raise SensitivityError('need 4 errors and a 4x4 correlation matrix (order A,B,F,G)')
    if (e <= 0).any() or not np.isfinite(e).all(): raise SensitivityError('errors must be finite and > 0')
    if not np.allclose(np.diag(C), 1.0, atol=1e-8): raise SensitivityError('correlation matrix diagonal must be 1')
    if (abs(C) > 1 + 1e-12).any(): raise SensitivityError('correlation entries must lie in [-1, 1]')
    return validate_covariance(C * np.outer(e, e))

def validate_covariance(cov, errors=None, sym_tol=1e-10, psd_tol=1e-10, diag_rtol=0.05):
    """Finite, symmetric, positive semidefinite (min eigenvalue >= -psd_tol * max|eig|), diagonal consistent with `errors` if given."""
    C = np.asarray(cov, float)
    if C.shape != (4, 4) or not np.isfinite(C).all(): raise SensitivityError('covariance must be a finite 4x4 matrix')
    if not np.allclose(C, C.T, rtol=0, atol=sym_tol * max(1.0, np.abs(C).max())): raise SensitivityError('covariance is not symmetric')
    w = np.linalg.eigvalsh((C + C.T) / 2)
    if w.min() < -psd_tol * max(abs(w).max(), 1e-300): raise SensitivityError(f'covariance is not positive semidefinite (min eigenvalue {w.min():.3g})')
    if (np.diag(C) < 0).any(): raise SensitivityError('negative variance on the diagonal')
    if errors is not None and not np.allclose(np.sqrt(np.diag(C)), errors, rtol=diag_rtol): raise SensitivityError('covariance diagonal inconsistent with reported errors')
    return (C + C.T) / 2

def nearest_psd(cov, floor=0.0):
    """EXPLICIT repair (eigenvalue clipping) — never applied automatically; the caller must log it as a deviation."""
    w, V = np.linalg.eigh((np.asarray(cov, float) + np.asarray(cov, float).T) / 2); return (V * np.maximum(w, floor)) @ V.T

def sample_ti(mean, cov=None, errors=None, n=20000, seed=0):
    """Draw (A,B,F,G). `cov` -> correlated; else diagonal from `errors` (flag `diagonal_only`)."""
    mu = np.asarray(mean, float)
    if mu.shape != (4,) or not np.isfinite(mu).all(): raise SensitivityError('mean must be 4 finite numbers')
    if cov is not None: C = validate_covariance(cov, errors); full = True
    else:
        if errors is None: raise SensitivityError('need cov or errors')
        e = np.asarray(errors, float)
        if (e <= 0).any(): raise SensitivityError('errors must be > 0')
        C = np.diag(e**2); full = False
    # eigen-decomposition sampler: valid for PSD (singular) matrices too
    w, V = np.linalg.eigh(C); L = V * np.sqrt(np.maximum(w, 0))
    X = mu + np.random.default_rng(seed).normal(size=(int(n), 4)) @ L.T
    return X, dict(full_covariance_used=full, diagonal_only=not full)

def _campbell(A, B, F, G):
    u = (A**2 + B**2 + F**2 + G**2) / 2; v = A * G - B * F
    a0 = np.sqrt(u + np.sqrt(np.maximum((u + v) * (u - v), 0)))
    inc = np.degrees(np.arccos(np.clip(v / a0**2, -1, 1))); return a0, inc

def compare_correlated_vs_diagonal(mean, cov, n=50000, seed=0):
    """Same means, same marginal errors: correlated vs diagonal-only sampling -> spread of a0 [mas] and inclination [deg]."""
    cov = validate_covariance(cov); err = np.sqrt(np.diag(cov))
    Xc, _ = sample_ti(mean, cov=cov, n=n, seed=seed); Xd, _ = sample_ti(mean, errors=err, n=n, seed=seed + 1)
    out = dict(data='caller-supplied mean/covariance; provenance (synthetic or real) is NOT determined by this function - the caller must label it', n=int(n),
               max_abs_corr=float(np.max(abs(np.corrcoef(Xc.T) - np.eye(4)))))
    for lab, X in (('correlated', Xc), ('diagonal', Xd)):
        a0, inc = _campbell(*X.T)
        out[lab] = dict(a0_median=float(np.median(a0)), a0_std=float(np.std(a0)), a0_p16_p84=np.percentile(a0, [16, 84]).tolist(),
                        inc_median=float(np.median(inc)), inc_std=float(np.std(inc)))
    out['a0_std_ratio_corr_over_diag'] = out['correlated']['a0_std'] / out['diagonal']['a0_std']
    out['inc_std_ratio_corr_over_diag'] = out['correlated']['inc_std'] / out['diagonal']['inc_std']
    return out
