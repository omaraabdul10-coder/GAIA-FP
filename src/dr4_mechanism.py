"""
dr4_mechanism.py: the confirmatory DR4 run of amendment v0.6 (H12 mechanism, H13 label blindness, H14 amplitude).

Steps (frozen):
  1. Read the DR4 combined astrometric + single-lined orbit table (same columns as the DR3 AstroSpectroSB1 download).
  2. Drop every source_id that is in the DR3 AstroSpectroSB1 table (realdata/dr3_astrospectro_all.csv) or in the sealed list.
  3. Build labels, CMD offsets and vbroad excess with dark_companion.h10. Amendment v0.6 A15: pass the DR4 field files
     (CMD field, field vbroad from the D2b-identical query) as arguments 2 and 3; the DR3 defaults are only for testing.
  4. Run mechanism.main (M1, M2a, M2b, M3, M4, P0) and h13 below.
Dry run on DR3 (development numbers): python dr4_mechanism.py --dry-run-dr3
"""
import json, sys, numpy as np, pandas as pd
import mechanism as M

SEED, NBOOT = 7, 2000

def h13(Y, n=NBOOT, seed=SEED):
    """Label blindness: the bright-companion fraction (beta_hat >= 0.2) is higher at large RV separation (Kmax >= 50 km/s)
    than at small separation (Kmax < 30 km/s). Pass if the 95% lower bound of the ratio > 1."""
    bh, Km = Y.beta.values, Y.Kmax.values
    def r(i):
        hi, lo = Km[i] >= 50, Km[i] < 30
        return (bh[i][hi] >= 0.2).mean()/(bh[i][lo] >= 0.2).mean()
    idx = np.arange(len(Y)); est = r(idx); rng = np.random.default_rng(seed)
    bs = np.array([r(rng.integers(0, len(Y), len(Y))) for _ in range(n)]); bs = bs[~np.isnan(bs)]   # keep +inf (A2-F17)
    if len(bs) < 0.5*n: bs = np.array([np.nan])                 # too few bright companions at small separation: no verdict
    return dict(ratio=[float(est), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                n_high=int((Km >= 50).sum()), n_low=int((Km < 30).sum()), pass_=bool(not np.isnan(bs).any() and np.percentile(bs, 2.5) > 1))

def h12_pvalue(Y, n=NBOOT, seed=SEED):
    """v0.6 A18: one-sided bootstrap p-value of the intersection-union test H12 = M1 and M2b and M2a.
    p = max(p_M1 [null r <= 0], p_M2b [null diff <= 0], p_M2a [null r >= 0.10]); same covariates and seed as mechanism.py."""
    cov = ['grvs_mag', 'bp_rp', 'logP', 'eccentricity']
    R = M.prank(Y, ['VB', 'b', 'k'] + cov); Z = np.c_[[R[c] for c in cov]].T
    dark = (Y.label == 0).values; Yd = Y[dark].reset_index(drop=True); Rd = M.prank(Yd, ['VB', 'k'] + cov); Zd = np.c_[[Rd[c] for c in cov]].T
    rng = np.random.default_rng(seed); N, Nd = len(Y), len(Yd); b1, b2, b3 = [], [], []
    for _ in range(n):
        i = rng.integers(0, N, N); rb, rk = M.pcorr(R['VB'][i], R['b'][i], Z[i]), M.pcorr(R['VB'][i], R['k'][i], Z[i])
        b1.append(rb); b2.append(rb - rk); j = rng.integers(0, Nd, Nd); b3.append(M.pcorr(Rd['VB'][j], Rd['k'][j], Zd[j]))
    b1, b2, b3 = map(np.array, (b1, b2, b3))
    p1, p2, p3 = (np.sum(b1 <= 0) + 1)/(n + 1), (np.sum(b2 <= 0) + 1)/(n + 1), (np.sum(b3 >= 0.10) + 1)/(n + 1)
    return dict(p_M1=float(p1), p_M2b=float(p2), p_M2a=float(p3), p_H12=float(max(p1, p2, p3)))

RHO_MC = 5000      # v0.6 A27 (audit A2: n_mc = 200 changes ~20% of labels with the seed)

def rho_labels_chunked(X, n_mc=RHO_MC, seed=7, chunk=500, base=None):
    """dark_companion.rho_labels with n_mc draws, computed in chunks (same rule, same per-row draw structure).
    `base` is the ORIGINAL rho_labels function (passed explicitly: calling DC.rho_labels while it is monkeypatched would
    recurse forever -- caught by the 6 Nov dry run)."""
    import dark_companion as DC
    f = base or DC.rho_labels
    labs, meds = [], []
    for k, i in enumerate(range(0, len(X), chunk)):
        l, m = f(X.iloc[i:i+chunk], n_mc=n_mc, seed=seed + k); labs.append(l); meds.append(m)
    return np.concatenate(labs), np.concatenate(meds)

def exclusion_ids(idmap=None):
    """v0.6 A15: DR4 ids to exclude = DR4 counterparts (nearest within 1") of DR3 AstroSpectroSB1 or sealed sources, plus the
    same ids taken literally (in case the id did not change). Ids are compared as stripped strings (no int/str mismatch)."""
    dr3 = set(pd.read_csv('../realdata/dr3_astrospectro_all.csv', dtype={'source_id': str}).source_id.str.strip())
    sealed = set(pd.read_csv('../realdata/excluded_sealed_ids.csv', dtype={'source_id': str}).source_id.str.strip())
    excl = dr3 | sealed
    if idmap is not None:
        Mp = pd.read_csv(idmap, dtype={'dr3_source_id': str, 'dr4_source_id': str})
        Mp = Mp[Mp.angular_distance_arcsec <= 1.0]
        excl |= set(Mp.loc[Mp.dr3_source_id.str.strip().isin(dr3 | sealed), 'dr4_source_id'].str.strip())
    return excl

def main(argv):
    if '--dry-run-dr3' in argv:
        Y = pd.read_csv('../results/mechanism_scored.csv', dtype={'source_id': str})
        out = dict(status='DRY RUN on DR3 (development values, not a test)', H13=h13(Y), H12_pvalue=h12_pvalue(Y))
        print(json.dumps(out, indent=1)); json.dump(out, open('../results/dr4_mechanism_dryrun_dr3.json', 'w'), indent=1); return
    import argparse, dark_companion as DC
    ap = argparse.ArgumentParser(); ap.add_argument('orbits'); ap.add_argument('field_cmd', nargs='?', default='../realdata/dr3_field.csv')
    ap.add_argument('field_vbroad', nargs='?', default='../realdata/dr3_field_vbroad.csv'); ap.add_argument('--idmap')
    a = ap.parse_args(argv)
    d4 = pd.read_csv(a.orbits, dtype={'source_id': str}); d4['source_id'] = d4.source_id.str.strip()
    excl = exclusion_ids(a.idmap)
    n_in = len(d4); d4 = d4[~d4.source_id.isin(excl)]
    # note: dark_companion.h10 also drops sealed ids, but it compares with INTEGER ids, so with string ids its own check is a
    # no-op; the exclusion above (strings, cross-match aware) is the one that counts (audit finding, 31 Oct 2026).
    field_cmd = pd.read_csv(a.field_cmd)
    field = pd.read_csv(a.field_vbroad)
    ridge = DC.D.fit_ms_ridge(field_cmd)
    MGf = field.phot_g_mean_mag + 5*np.log10(field.parallax/100)
    msf = (field.bp_rp >= ridge['color'].min()) & (field.bp_rp <= ridge['color'].max()) & (MGf > np.interp(field.bp_rp, ridge['color'], ridge['ridge']) - 2.0)
    _orig = DC.rho_labels; DC.rho_labels = lambda X, n_mc=200, seed=7: rho_labels_chunked(X, base=_orig)   # A27, in memory only
    try:
        res, X = DC.h10(d4, field_cmd, DC.vb_field(field[msf]))
    finally:
        DC.rho_labels = _orig
    X.to_csv('../results/dr4_new_scored.csv', index=False)
    import os, shutil
    R = '../results/'
    for f in ('mechanism.json', 'mechanism_scored.csv'):        # keep the DR3 outputs: mechanism.main writes to fixed names
        shutil.copy(R+f, R+'dr3_'+f)
    try:
        M.main(R+'dr4_new_scored.csv')
        os.replace(R+'mechanism.json', R+'dr4_mechanism.json'); os.replace(R+'mechanism_scored.csv', R+'dr4_mechanism_scored.csv')
    finally:
        for f in ('mechanism.json', 'mechanism_scored.csv'):
            os.replace(R+'dr3_'+f, R+f)
    Y = pd.read_csv(R+'dr4_mechanism_scored.csv', dtype={'source_id': str})
    out = json.load(open('../results/dr4_mechanism.json')); out['H13'] = h13(Y); out['H10_style_summary'] = res
    out['confirmatory'] = out['n_V'] >= 668                      # power rule of amendment v0.6
    out['n_input_rows'] = n_in; out['n_after_exclusion'] = len(d4); out['idmap_used'] = a.idmap is not None
    c = out['M4_c_hat']; out['H14'] = dict(c_hat=c, reproduces_DR3=bool(c[2] >= 1.4 and c[1] <= 2.3), theory_c4_rejected=bool(c[2] < 4))
    out['H12_mechanism_supported'] = bool(out['M1_pass'] and out['M2a_pass'] and out['M2b_pass'])
    out['H12_pvalue'] = h12_pvalue(Y)
    out['H12_status'] = 'CONDUCTED' if out['confirmatory'] else 'NOT_CONDUCTED:BELOW_MIN_N'   # v0.6 A14/A19: only a CONDUCTED H12 enters Holm
    try:                                                            # v0.6 A33/A34 (secondary): same NEW systems, same labels
        import new_hypotheses as NH; out['H18_H19'] = NH.h18_h19(X)[0]
    except Exception as e:
        out['H18_H19'] = dict(status=f'NOT_CONDUCTED:CODE_ERROR: {type(e).__name__}: {e}')
    json.dump(out, open('../results/dr4_mechanism.json', 'w'), indent=1, default=float)

if __name__ == '__main__':
    main(sys.argv[1:])
