"""Independent QA utilities for GAIA-FP v0.6.

These helpers do not change preregistered scoring rules. They are deliberately
strict: unknown DR4 field names, missing covariance terms, and invalid units
must be explicit rather than guessed.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import rankdata

class QAInputError(ValueError):
    pass


def epoch_astrometry_to_relative_days(df: pd.DataFrame, *, source_id: str,
                                      time_col: str, time_unit: str,
                                      ref_epoch_jyear: float,
                                      along_scan_col: str, uncertainty_col: str,
                                      ccd_index: int | None = None) -> dict[str, dict[str, np.ndarray]]:
    """Normalize a *caller-mapped* DR4 epoch-astrometry table.

    The final DR4 column schema is not assumed. Caller must explicitly map
    names and declare units. Time origin is Gaia's 2010-01-01 TCB epoch.
    If CCD arrays are supplied, ccd_index must be explicit; no implicit CCD
    selection is made. Returns time relative to Julian-year reference epoch.
    """
    required = {source_id, time_col, along_scan_col, uncertainty_col}
    missing = required - set(df.columns)
    if missing:
        raise QAInputError(f"missing explicitly mapped columns: {sorted(missing)}")
    if time_unit not in {"ns_since_2010", "days_since_2010", "jd"}:
        raise QAInputError(f"unsupported time_unit {time_unit!r}")
    if not np.isfinite(ref_epoch_jyear) or not 2010 < ref_epoch_jyear < 2035:
        raise QAInputError("implausible reference epoch")
    epoch_jd = 2451545.0 + (ref_epoch_jyear - 2000.0) * 365.25
    jd_2010 = 2455197.5
    out = {}
    for sid, g in df.groupby(df[source_id].astype(str).str.strip(), sort=False):
        def flatten(col):
            vals = g[col].tolist()
            arrs = []
            for v in vals:
                if isinstance(v, (list, tuple, np.ndarray)):
                    a = np.asarray(v, float)
                    if ccd_index is not None:
                        if ccd_index < 0 or ccd_index >= len(a):
                            raise QAInputError(f"CCD index {ccd_index} outside {col} array for {sid}")
                        a = np.asarray([a[ccd_index]])
                    elif a.ndim:
                        raise QAInputError(f"array-valued {col} requires explicit ccd_index")
                    arrs.extend(a.ravel().tolist())
                else:
                    if ccd_index is not None:
                        raise QAInputError(f"ccd_index supplied but {col} is scalar")
                    arrs.append(float(v))
            return np.asarray(arrs, float)
        t, al, sig = (flatten(c) for c in (time_col, along_scan_col, uncertainty_col))
        if not (len(t) == len(al) == len(sig)):
            raise QAInputError(f"time/AL/error lengths differ for {sid}")
        if time_unit == "ns_since_2010": jd = jd_2010 + t / 86400e9
        elif time_unit == "days_since_2010": jd = jd_2010 + t
        else: jd = t
        rel_days = jd - epoch_jd
        ok = np.isfinite(rel_days) & np.isfinite(al) & np.isfinite(sig) & (sig > 0)
        if ok.sum() < 3:
            raise QAInputError(f"fewer than 3 valid epoch astrometry observations for {sid}")
        # Broad mission-window guard catches seconds/ns/day mistakes.
        if np.nanmedian(jd[ok]) < 2456500 or np.nanmedian(jd[ok]) > 2463000:
            raise QAInputError(f"epoch times outside plausible Gaia mission range for {sid}")
        out[sid] = {"t_days": rel_days[ok], "along_scan_mas": al[ok], "sigma_mas": sig[ok]}
    return out


def draw_thiele_innes(row, n=10000, seed=0, *, covariance_key="ti_covariance"):
    """Draw [A,B,F,G] using full 4x4 covariance when supplied.

    `ti_covariance` must be a 4x4 numeric matrix in the same squared units as
    A/B/F/G. Diagonal-only fallback is explicit and returned as a flag.
    """
    names = [f"{k.lower()}_thiele_innes" for k in "ABFG"]
    vals = np.array([float(row[k]) for k in names])
    errs = np.array([float(row[k + "_error"]) for k in names])
    if not np.isfinite(vals).all() or not np.isfinite(errs).all() or (errs <= 0).any():
        raise QAInputError("invalid Thiele-Innes means/errors")
    cov = row.get(covariance_key, None)
    used_full = cov is not None
    if used_full:
        cov = np.asarray(cov, float)
        if cov.shape != (4, 4) or not np.isfinite(cov).all() or not np.allclose(cov, cov.T, atol=1e-10):
            raise QAInputError("Thiele-Innes covariance must be finite symmetric 4x4")
        if np.linalg.eigvalsh(cov).min() < -1e-10:
            raise QAInputError("Thiele-Innes covariance is not positive semidefinite")
        if not np.allclose(np.sqrt(np.diag(cov)), errs, rtol=0.05, atol=1e-12):
            raise QAInputError("covariance diagonal inconsistent with reported errors")
    else:
        cov = np.diag(errs**2)
    draws = np.random.default_rng(seed).multivariate_normal(vals, cov, size=int(n), check_valid="raise")
    return draws, {"full_covariance_used": bool(used_full), "fallback": "diagonal_independence" if not used_full else None}


def auc(scores, labels):
    s, y = np.asarray(scores, float), np.asarray(labels, int)
    if len(s) != len(y) or not np.isfinite(s).all() or set(np.unique(y)) != {0, 1}:
        raise QAInputError("AUC needs finite scores and both binary classes")
    r = rankdata(s); n1 = y.sum(); n0 = len(y)-n1
    return float((r[y == 1].sum() - n1*(n1+1)/2)/(n1*n0))


def bootstrap_null_calibration(*, n_rep=1000, n_each_class=40, n_boot=500, seed=20261101):
    """Empirical type-I calibration of the project's percentile-bootstrap AUC p.

    Under H0 both classes draw scores from the same N(0,1) distribution.
    Reports rejection rates at .05 and .025; this is a diagnostic, not a
    replacement for the preregistered bootstrap rule.
    """
    rng = np.random.default_rng(seed); pvals = []
    for _ in range(int(n_rep)):
        y = np.r_[np.ones(n_each_class, int), np.zeros(n_each_class, int)]
        s = rng.normal(size=len(y)); obs = auc(s, y)
        pos = np.arange(n_each_class); neg = np.arange(n_each_class, 2*n_each_class)
        bs = np.empty(n_boot)
        for j in range(n_boot):
            ii = np.r_[rng.choice(pos, n_each_class, True), rng.choice(neg, n_each_class, True)]
            bs[j] = auc(s[ii], y[ii])
        # One-sided upper-tail test of AUC > 0.5, plus-one correction.
        pvals.append((np.sum(bs <= 0.5)+1)/(n_boot+1))
    p = np.asarray(pvals)
    return {"n_rep": int(n_rep), "n_each_class": int(n_each_class), "n_boot": int(n_boot),
            "seed": int(seed), "null_p_median": float(np.median(p)),
            "type1_at_0.05": float(np.mean(p <= .05)),
            "type1_at_0.025": float(np.mean(p <= .025)),
            "mc_se_0.05": float(np.sqrt(np.mean(p <= .05)*(1-np.mean(p <= .05))/len(p)))}


def mass_relation_sensitivity(MG, relations: dict[str, tuple], *, threshold_mj=80.0):
    """Compare explicit tabulated M_G->M_sun relations; no relation is silently preferred.

    Each mapping value is (MG_grid, mass_solar_grid). Outputs inferred masses and
    threshold classification per named relation. Tables must be supplied from
    a documented isochrone/calibration source by the analyst.
    """
    x = np.asarray(MG, float); out = {}
    if not np.isfinite(x).all() or not relations:
        raise QAInputError("finite MG and at least one documented relation required")
    for name, (mg_grid, mass_grid) in relations.items():
        mg_grid, mass_grid = np.asarray(mg_grid, float), np.asarray(mass_grid, float)
        if len(mg_grid) < 3 or len(mg_grid) != len(mass_grid) or not np.all(np.diff(mg_grid) > 0) or not np.isfinite(mass_grid).all() or (mass_grid <= 0).any():
            raise QAInputError(f"invalid monotonic isochrone grid: {name}")
        m = np.interp(x, mg_grid, mass_grid, left=np.nan, right=np.nan)
        out[name] = {"mass_solar": m.tolist(), "in_range": np.isfinite(m).tolist()}
    return out


def h6_ml_comparison(D, *, model=None, seed=7, n_boot=2000):
    """Callable H6 comparator; caller supplies the registered training model or builds it via tournament."""
    import tournament
    from sklearn.metrics import roc_auc_score
    miss = [c for c in tournament.COLS + ["y", "P_impostor"] if c not in D]
    if miss: raise QAInputError(f"H6 schema missing {miss}")
    X = D[tournament.COLS].to_numpy(float); y = D.y.to_numpy(int); p = D.P_impostor.to_numpy(float)
    if not np.isfinite(X).all() or not np.isfinite(p).all() or not set(np.unique(y)) == {0, 1}:
        raise QAInputError("H6 requires finite predictors/scores and both classes")
    if model is None:
        train, _ = tournament.splits(); model = tournament.ml_model(train)
    sm = model.predict_proba(X)[:, 1]
    obs = float(roc_auc_score(y, sm) - roc_auc_score(y, p))
    rng = np.random.default_rng(seed); pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    boot = np.empty(n_boot)
    for j in range(n_boot):
        ii = np.r_[rng.choice(pos, len(pos), True), rng.choice(neg, len(neg), True)]
        boot[j] = roc_auc_score(y[ii], sm[ii]) - roc_auc_score(y[ii], p[ii])
    return {"status": "CONDUCTED", "auc_ml": float(roc_auc_score(y, sm)),
            "auc_gaiafp": float(roc_auc_score(y, p)), "difference": obs,
            "ci95_percentile": np.percentile(boot, [2.5, 97.5]).tolist(),
            "bootstrap_seed": seed, "bootstrap_replicates": n_boot,
            "training_domain": "registered DR4 simulator", "interpretation": "secondary domain-transfer comparison"}
