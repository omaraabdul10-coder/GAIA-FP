"""
dr3_study.py — H7-DR3: REAL-DATA test of GAIA-FP on Gaia DR3 astrometric substellar candidates against independent
public spectroscopic-survey SB2 catalogues. Pre-registered in ../DR3_STUDY_PLAN.md (hashed before analysis).

Inputs in ../realdata/ (all public; provenance in ../realdata/PROVENANCE.md):
  dr3_candidates.csv     Gaia DR3 nss_two_body_orbit ⋈ binary_masses ⋈ gaia_source (+ dr2_neighbourhood), m2 < 80 MJ
  dr3_field.csv          Gaia DR3 field-star sample for the main-sequence ridge (phot_g_mean_mag, bp_rp, parallax)
  sb2_lamost.csv         Kovalev+2024 LAMOST-MRS SB2 ids matching candidates (column gaia_dr3_source_id)
  sb2_galah.csv          Traven+2020 GALAH SB2 ids matching candidates (column gaia_dr2_source_id)
  sb2_apogee.csv         Kounkel+2021 APOGEE SB2 rows near candidates (ID, ra, dec [J2000])
  lamost_cov.csv         Wang+2019 LAMOST-MRS RV catalogue: gaia_dr2_source_id, n_epochs (stars LAMOST-MRS observed)
  excluded_sealed_ids.csv  source_ids of the sealed GAIA-FP labelled set (membership only, no labels) — dropped FIRST
Outputs: ../results/dr3_study.json, ../results/dr3_candidates_scored.csv
"""
import json, sys, numpy as np, pandas as pd
from scipy.spatial import cKDTree
from blind_eval import roc_auc, clopper_pearson

REAL, OUT = '../realdata/', '../results/'
APOGEE_RADIUS_ARCSEC = 2.0
DR2_MAX_DIST_MAS = 1000.0
MIN_P1_POSITIVES = 10
SEED = 2026

# ------------------------------------------------------------------ matching utilities
def propagate(ra, dec, pmra, pmdec, from_epoch=2016.0, to_epoch=2000.0):
    """Linear proper-motion propagation (adequate for |dt| = 16 yr and these distances). pm in mas/yr."""
    dt = to_epoch - from_epoch
    pmra = np.nan_to_num(pmra); pmdec = np.nan_to_num(pmdec)
    dec2 = dec + pmdec*dt/3.6e6
    ra2 = ra + pmra*dt/3.6e6/np.cos(np.radians(dec))
    return ra2 % 360.0, dec2

def _unit(ra, dec):
    r, d = np.radians(ra), np.radians(dec)
    return np.c_[np.cos(d)*np.cos(r), np.cos(d)*np.sin(r), np.sin(d)]

def sep_arcsec(ra1, dec1, ra2, dec2):
    u, v = _unit(np.atleast_1d(ra1), np.atleast_1d(dec1)), _unit(np.atleast_1d(ra2), np.atleast_1d(dec2))
    return np.degrees(2*np.arcsin(np.clip(np.linalg.norm(u-v, axis=1)/2, 0, 1)))*3600

def positional_match(ra, dec, cat_ra, cat_dec, radius_arcsec):
    """For each target: number of catalogue rows within radius, index of nearest, separation. Ambiguous if n > 1."""
    n = np.zeros(len(ra), int); idx = np.full(len(ra), -1); sep = np.full(len(ra), np.nan)
    if len(cat_ra) == 0: return n, idx, sep
    tree = cKDTree(_unit(cat_ra, cat_dec)); chord = 2*np.sin(np.radians(radius_arcsec/3600)/2)
    hits = tree.query_ball_point(_unit(ra, dec), chord)
    for i, h in enumerate(hits):
        n[i] = len(h)
        if h:
            s = sep_arcsec(np.full(len(h), ra[i]), np.full(len(h), dec[i]), cat_ra[h], cat_dec[h]); j = int(np.argmin(s))
            idx[i] = h[j]; sep[i] = s[j]
    return n, idx, sep

# ------------------------------------------------------------------ labels (pre-registered rules)
def build_labels(cand, lamost_sb2, galah_sb2, apogee, lamost_cov):
    L = pd.DataFrame(dict(source_id=cand['source_id'].values))
    L['sb2_lamost'] = cand['source_id'].isin(set(lamost_sb2['gaia_dr3_source_id'].astype('int64'))).values
    dr2ok = cand['dr2_source_id'].notna() & (cand['dr2_angular_distance'].fillna(1e9) < DR2_MAX_DIST_MAS)
    L['sb2_galah'] = (dr2ok & cand['dr2_source_id'].isin(set(galah_sb2['gaia_dr2_source_id'].astype('int64')))).values
    ra0, de0 = propagate(cand['ra'].values, cand['dec'].values, cand['pmra'].values, cand['pmdec'].values)
    n, idx, sep = positional_match(ra0, de0, apogee['ra'].values, apogee['dec'].values, APOGEE_RADIUS_ARCSEC)
    L['apogee_n_within'] = n; L['apogee_sep_arcsec'] = sep
    L['apogee_ambiguous'] = n > 1
    L['sb2_apogee'] = (n == 1)
    if {'ra', 'dec'}.issubset(lamost_cov.columns):
        # Deviation 4 (DR3_STUDY_DEVIATIONS.md): VizieR serves the LAMOST-MRS 'Gaia' id as a double (precision lost),
        # so coverage is matched by POSITION (same propagation and radius as APOGEE; ambiguous -> no coverage).
        # LAMOST input-catalogue epoch is not uniform, so test both J2000 and the Gaia epoch (2016.0) and keep the
        # epoch giving a unique match (if both are unique they must agree; if they disagree -> ambiguous)
        cr, cd = lamost_cov['ra'].values, lamost_cov['dec'].values
        n1, i1, _ = positional_match(ra0, de0, cr, cd, APOGEE_RADIUS_ARCSEC)
        n2, i2, _ = positional_match(cand['ra'].values, cand['dec'].values, cr, cd, APOGEE_RADIUS_ARCSEC)
        ic = np.where(n1 == 1, i1, np.where(n2 == 1, i2, -1))
        disagree = (n1 == 1) & (n2 == 1) & (i1 != i2)
        nc = np.where(disagree | (n1 > 1) | (n2 > 1), 2, (ic >= 0).astype(int))
        nep = np.where(nc == 1, lamost_cov['n_epochs'].values[np.clip(ic, 0, None)], 0)
        L['lamost_nep'] = nep.astype(int); L['lamost_cov_ambiguous'] = nc > 1
    else:
        cov = lamost_cov.groupby('gaia_dr2_source_id')['n_epochs'].max()
        L['lamost_nep'] = np.where(dr2ok, cand['dr2_source_id'].map(cov).fillna(0), 0).astype(int)
    L['sb2_any'] = L['sb2_lamost'] | L['sb2_galah'] | L['sb2_apogee']
    # P1 population: observed by LAMOST-MRS (>=2 epochs) OR in the LAMOST SB2 catalogue
    in_p1 = (L['lamost_nep'] >= 2) | L['sb2_lamost']
    L['label_P1'] = np.where(in_p1 & ~L['apogee_ambiguous'], np.where(L['sb2_any'], 1, 0), -1)   # -1 = not in P1 population
    return L

# ------------------------------------------------------------------ metrics
def boot_auc(s, y, n=2000, seed=SEED):
    r = np.random.default_rng(seed); pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]; v = []
    for _ in range(n):
        i = np.r_[r.choice(pos, len(pos)), r.choice(neg, len(neg))]; v.append(roc_auc(s[i], y[i]))
    return [float(x) for x in np.percentile(v, [2.5, 97.5])]

def paired_diff(s1, s2, y, n=2000, seed=SEED):
    r = np.random.default_rng(seed); pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]; v = []
    for _ in range(n):
        i = np.r_[r.choice(pos, len(pos)), r.choice(neg, len(neg))]; v.append(roc_auc(s1[i], y[i]) - roc_auc(s2[i], y[i]))
    return [float(np.mean(v))] + [float(x) for x in np.percentile(v, [2.5, 97.5])]

def evaluate(scores, y, primary='GAIA-FP'):
    out = dict(n_pos=int((y == 1).sum()), n_neg=int((y == 0).sum()))
    if out['n_pos'] == 0 or out['n_neg'] == 0:
        out['status'] = 'no data'; return out
    out['auc'] = {k: float(roc_auc(v, y)) for k, v in scores.items()}
    out['auc_ci'] = {k: boot_auc(v, y) for k, v in scores.items()}
    out['diff_vs_baselines'] = {k: paired_diff(scores[primary], v, y) for k, v in scores.items() if k != primary}
    if out['n_pos'] < MIN_P1_POSITIVES:
        out['status'] = f'UNDERPOWERED (n_pos < {MIN_P1_POSITIVES})'
    else:
        out['status'] = 'SUCCESS' if out['auc_ci'][primary][0] > 0.5 else 'FAILURE'
    return out

# ------------------------------------------------------------------ main
def main(real=REAL, out=OUT):
    import dr4_pipeline as D
    cand = pd.read_csv(real+'dr3_candidates.csv'); field = pd.read_csv(real+'dr3_field.csv')
    sealed = set(pd.read_csv(real+'excluded_sealed_ids.csv')['source_id'].astype('int64'))
    n_raw = len(cand)
    # one row per source (pre-registered order of solution types, then nearest DR2 neighbour)
    order = {t: i for i, t in enumerate(['Orbital', 'AstroSpectroSB1', 'OrbitalTargetedSearchValidated', 'OrbitalTargetedSearch',
                                         'OrbitalAlternativeValidated', 'OrbitalAlternative'])}
    cand = cand.assign(_rank=cand['nss_solution_type'].map(order).fillna(99), _d=cand['dr2_angular_distance'].fillna(1e9))
    cand = cand.sort_values(['_rank', '_d']).drop_duplicates('source_id', keep='first').drop(columns=['_rank', '_d'])
    n_dedup = len(cand)
    cand = cand[~cand['source_id'].astype('int64').isin(sealed)].reset_index(drop=True)    # sealed objects dropped FIRST
    n_after_sealed = len(cand)
    qa = dict(n_raw_rows=n_raw, n_unique_sources=n_dedup, n_sealed_dropped=n_dedup - n_after_sealed)
    ridge = D.fit_ms_ridge(field)
    X = D.select_candidates(D.features(cand, ridge))
    qa['n_after_m2_cut_recomputed'] = len(X)
    ok = np.isfinite(X[['a0', 'a0err', 'P', 'e', 'dm', 'M', 'd', 'sig_cmd']].values).all(1) & (X['a0'] > 0) & (X['a0err'] > 0)
    qa['n_dropped_missing_or_invalid'] = int((~ok).sum()); X = X[ok].reset_index(drop=True)
    S = D.score(X, rvs=None, seed=0)
    lab = build_labels(cand.set_index('source_id').loc[S['source_id']].reset_index(),
                       pd.read_csv(real+'sb2_lamost.csv'), pd.read_csv(real+'sb2_galah.csv'),
                       pd.read_csv(real+'sb2_apogee.csv'), pd.read_csv(real+'lamost_cov.csv'))
    S = S.merge(lab, on='source_id', how='left')
    rng = np.random.default_rng(SEED)
    scores = {'GAIA-FP': S['P_impostor'].values, 'B1 RUWE': S['ruwe'].values, 'B2 CMD excess': -S['dm'].values,
              'B3 inverse significance': -S['significance'].fillna(S['significance'].median()).values,
              'B4 random': rng.random(len(S))}
    res = dict(qa=qa, ridge_sigma_median=float(np.median(ridge['sigma'])))
    m = S['label_P1'].values >= 0
    res['P1_LAMOST_population'] = evaluate({k: v[m] for k, v in scores.items()}, S['label_P1'].values[m])
    y2 = S['sb2_any'].astype(int).values
    res['P2_PU_all'] = evaluate(scores, y2); res['P2_PU_all']['note'] = 'positive-unlabelled: lower bound'
    pos = S['sb2_any'].values; npos = int(pos.sum())
    if npos:
        k85 = int((S['P_impostor'].values[pos] >= 0.85).sum()); k50 = int((S['P_impostor'].values[pos] >= 0.5).sum())
        kamb = int((S['verdict'].values[pos] == 'ambiguous_followup_needed').sum())
        res['P3_recall'] = {'P>=0.85': [k85, npos, list(clopper_pearson(k85, npos))],
                            'P>=0.5': [k50, npos, list(clopper_pearson(k50, npos))], 'ambiguous': [kamb, npos]}
    res['counts'] = dict(n_scored=len(S), sb2_lamost=int(S['sb2_lamost'].sum()), sb2_galah=int(S['sb2_galah'].sum()),
                         sb2_apogee=int(S['sb2_apogee'].sum()), apogee_ambiguous=int(S['apogee_ambiguous'].sum()),
                         lamost_observed_ge2=int((S['lamost_nep'] >= 2).sum()),
                         verdicts=S['verdict'].value_counts().to_dict(),
                         label_free_contamination_mean_P=float(S['P_impostor'].mean()))
    json.dump(res, open(out+'dr3_study.json', 'w'), indent=1, default=float)
    S.drop(columns=['best_followup']).to_csv(out+'dr3_candidates_scored.csv', index=False)
    print(json.dumps(res, indent=1, default=float))
    return res

if __name__ == "__main__":
    main()
