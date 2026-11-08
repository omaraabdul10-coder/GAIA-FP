"""
dr4_run.py: DR4 day-1 scoring (amendment v0.6 A17 + A25). Frozen files are not edited; they are called or re-implemented here.

PRIMARY = "v3.2" (v0.6 A25): the registered v3.1 method with the error corrections of the 31 Oct audit (AUDIT_REPORT.md):
  * sigma_a0 = a0 / significance (Gaia's full-covariance value) instead of the rms of the four TI errors   [A1-F8]
  * candidates whose colour lies outside the CMD ridge range are excluded and counted (no silent clamping)  [A1-F5]
  * RVS term from rvs_v32 (monotone, 8000 draws, per-candidate seed, own epochs, q from p(q,n|a0,dM))      [A2-F2,3,4,10,11]
  * population-prior covariates without G and ln d (they rebuild M_G, i.e. the CMD evidence, in the prior) [A2-F8]
  * v0.4 A1 prior selection (prior_select.posterior, seed 0) and v0.5 A6 SB1 truncation, as registered;
    v0.5 A7: score_emp = cmd_z + rvs_z (the primary RVS combination for H2)
  * every warning is recorded (hier_em silences warnings at import)                                         [A2-F12]
REPORTED ALONGSIDE: P_impostor_v31 (frozen dr4_pipeline.score + A1, i.e. the registered method with its defects) and
P_impostor_noA6 (v3.2 with A6 off, v0.6 A23).
"""
import hashlib, json, warnings, numpy as np, pandas as pd
import dr4_pipeline as D, dr4_schema as S, dr4_empirical as EMP, prior_select as PS
from hier_em import phi
from joint_lr import llr_a0_cmd
import rvs_v32 as V

T = D.T_ABSTAIN

def guards(X):
    bad = []
    chk = lambda cond, msg: bad.append(msg) if not np.all(cond) else None
    chk(X.a0 > 0, 'a0 <= 0'); chk(X.a0err > 0, 'a0err <= 0'); chk(X.d > 0, 'distance <= 0'); chk(X.M > 0, 'mass <= 0')
    chk((X.inc >= 0) & (X.inc <= 180), 'inclination outside [0, 180] deg'); chk((X.e >= 0) & (X.e < 1), 'e outside [0, 1)')
    chk(X.P > 0, 'period <= 0'); chk(X.sig_cmd > 0.02, 'sig_cmd <= 0.02'); chk(np.isfinite(X.dm), 'dm not finite')
    chk(X.index.equals(pd.RangeIndex(len(X))), 'index not 0..n-1')
    if bad: raise S.SchemaError('physical guard failed: ' + '; '.join(bad))

def verdict(p): return np.where(p <= T, 'likely_substellar', np.where(p >= 1 - T, 'likely_impostor', 'ambiguous_followup_needed'))

def phi_v32(X):
    F = np.c_[np.log(X['P']), X['e'], np.log(np.clip(X['mfit'], 0.1, None))]
    return (F - F.mean(0))/F.std(0)

def _rvs_job(job):
    """one candidate's RVS term (module-level so it can run in a worker process)."""
    i, r, g, a6_variant = job
    n_ = len(g['t']); s_ = float(np.median(g['width_err'])) if len(g['width_err']) else np.nan
    z_, L_, w_ = V.llr_rvs(r, g['t'], g['width'], g['width_err'], sb1_truncate=True)
    L0_ = V.llr_rvs(r, g['t'], g['width'], g['width_err'], sb1_truncate=False)[1] if a6_variant and w_ in ('OK', 'H_T_EXCLUDED_BY_A6') else L_
    return i, n_, s_, z_, L_, w_, L0_

def prepare(cand, field):
    S.check(cand, S.ORBIT, 'candidates'); S.check(cand, S.SOURCE, 'candidates'); S.check_unit_plausibility(cand)
    S.check(field, {'phot_g_mean_mag': S.SOURCE['phot_g_mean_mag'], 'bp_rp': S.SOURCE['bp_rp'], 'parallax': (0.0, 1e3, 1.0, 'mas')}, 'field')
    cand = cand.copy(); cand['source_id'] = cand.source_id.astype(str).str.strip()
    if cand.source_id.duplicated().any(): cand = cand.drop_duplicates('source_id')
    ridge = D.fit_ms_ridge(field)
    X = D.features(cand, ridge)
    out = dict(n_input=len(cand))
    inrange = (X.bp_rp >= ridge['color'].min()) & (X.bp_rp <= ridge['color'].max())
    out['n_colour_outside_ridge'] = int((~inrange).sum())
    X = X[inrange].reset_index(drop=True)
    X = D.select_candidates(X)                                            # frozen rule (first-order m2 < 80 MJ)
    fin = np.isfinite(X[['a0', 'a0err', 'P', 'e', 'dm', 'M', 'd', 'sig_cmd']].values).all(1) & (X.a0 > 0) & (X.a0err > 0)
    out['n_nonfinite_dropped'] = int((~fin).sum()); X = X[fin].reset_index(drop=True)
    return X, out

def score(cand, field, rvs=None, seed=0, a6_variant=True, v31=True, workers=None):
    rec = []
    with warnings.catch_warnings(record=True) as W:
        warnings.simplefilter('always')
        X, info = prepare(cand, field)
        X31 = X.copy()                                                    # v3.1 keeps the registered a0 error
        sig = np.where(np.isfinite(X.significance) & (X.significance > 0), X.a0/X.significance, X.a0err)
        info['n_a0err_from_significance'] = int((np.isfinite(X.significance) & (X.significance > 0)).sum())
        X['a0err'] = sig
        guards(X)
        Lc = llr_a0_cmd(X.a0.values, X.a0err.values, X.P.values, X.M.values, X.d.values, X.dm.values, X.sig_cmd.values[:, None])
        if not np.isfinite(Lc).all(): raise S.SchemaError('non-finite a0|CMD log LR')
        z = np.full(len(X), np.nan); Lr = np.zeros(len(X)); Lr0 = np.zeros(len(X)); why = np.array(['NO_RVS_EPOCHS']*len(X), object)
        nep = np.zeros(len(X), int); srv = np.full(len(X), np.nan)
        jobs = [(i, r.to_dict(), (rvs or {}).get(r['source_id']), a6_variant) for i, r in X.iterrows()]
        jobs = [j for j in jobs if j[2] is not None]
        if workers and workers > 1 and len(jobs) > 50:     # order-independent by construction (per-candidate seeds)
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(max_workers=workers) as ex: res = list(ex.map(_rvs_job, jobs, chunksize=8))
        else:
            res = [_rvs_job(j) for j in jobs]
        for i, n_, s_, z_, L_, w_, L0_ in res:
            nep[i], srv[i], z[i], Lr[i], why[i], Lr0[i] = n_, s_, z_, L_, w_, L0_
        X['z'], X['nep'], X['srv'], X['rvs_status'] = z, nep, srv, why
        X['llr_cmd'] = Lc; X['llr_rvs'] = Lr; X['log_lr'] = np.clip(Lc + Lr, -30, 30)
        p, pi, C_star, cv = PS.posterior(X.log_lr.values, phi_v32(X), seed=0)
        X['P_impostor'], X['prior_pi'], X['verdict'] = p, pi, verdict(p)
        if a6_variant:
            X['P_impostor_noA6'] = PS.posterior(np.clip(Lc + Lr0, -30, 30), phi_v32(X), seed=0)[0]
        if v31:                                                           # registered method, with its known defects
            X31s = D.score(X31, rvs=rvs, seed=seed)
            p31 = PS.posterior(X31s.log_lr.values, phi(X31s), seed=0)[0]
            X['P_impostor_v31'] = p31; X['verdict_v31'] = verdict(p31)
        X = EMP.add_scores(X)
        rec = [f'{w.category.__name__}: {w.message}' for w in W]
    for c in [c for c in X.columns if c.startswith('P_impostor')] + ['prior_pi']:
        if not (np.isfinite(X[c]) & (X[c] >= 0) & (X[c] <= 1)).all(): raise S.SchemaError(f'{c} outside [0, 1] or not finite')
    if not np.isfinite(X.score_emp).all(): raise S.SchemaError('score_emp not finite')
    info.update(n_scored=len(X), C_star=C_star, cv_scores={str(k): v for k, v in cv.items()},
                rvs_status=pd.Series(why).value_counts().to_dict(), n_rvs_ge15=int((nep >= 15).sum()),
                n_warnings=len(rec), warnings_first20=sorted(set(rec))[:20])
    return X, info

COLS = ['source_id', 'G', 'bp_rp', 'd', 'P', 'e', 'inc', 'om', 'a0', 'a0err', 'mfit', 'M', 'dm', 'sig_cmd', 'ruwe', 'significance',
        'z', 'nep', 'rvs_status', 'llr_cmd', 'llr_rvs', 'log_lr', 'prior_pi', 'P_impostor', 'verdict', 'P_impostor_noA6',
        'P_impostor_v31', 'verdict_v31', 'score_emp']

def write(Xs, info, out_csv):
    Xs[[c for c in COLS if c in Xs]].to_csv(out_csv, index=False)
    h = hashlib.sha256(open(out_csv, 'rb').read()).hexdigest()
    open(out_csv + '.sha256', 'w').write(f'{h}  {out_csv.split("/")[-1]}\n')
    json.dump(dict(info, sha256=h, verdicts=Xs.verdict.value_counts().to_dict()), open(out_csv.replace('.csv', '_info.json'), 'w'), indent=1, default=float)
    return h
