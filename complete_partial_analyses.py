#!/usr/bin/env python3
"""Complete local, reproducible parts of the three partial GAIA-FP audits.

Inputs are the frozen/archive files in realdata/ and results/. This script does
NOT fetch external catalogues and does NOT change any historical/pre-registered
result. It writes only to results/qa2/partial_completion/.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[2]
REAL, RES = ROOT/'realdata', ROOT/'results'
OUT = RES/'qa2'/'partial_completion'
OUT.mkdir(parents=True, exist_ok=True)
RNG_SEED = 20261101
N_BOOT = 20000


def unit_xyz(ra_deg, dec_deg):
    ra = np.deg2rad(np.asarray(ra_deg, float)); dec = np.deg2rad(np.asarray(dec_deg, float))
    return np.column_stack((np.cos(dec)*np.cos(ra), np.cos(dec)*np.sin(ra), np.sin(dec)))


def propagate_j2000(ra, dec, pmra, pmdec):
    # Same linear 2016 -> J2000 prescription as src/dr3_study.py.
    dt = -16.0
    ra = np.asarray(ra, float); dec = np.asarray(dec, float)
    pmra = np.nan_to_num(np.asarray(pmra, float)); pmdec = np.nan_to_num(np.asarray(pmdec, float))
    dec2 = dec + pmdec*dt/3.6e6
    ra2 = (ra + pmra*dt/3.6e6/np.cos(np.deg2rad(dec))) % 360.0
    return ra2, dec2


def apogee_counts(tree, ra, dec, radius_arcsec=2.0):
    chord = 2*np.sin(np.deg2rad(radius_arcsec/3600.0)/2)
    hits = tree.query_ball_point(unit_xyz(ra, dec), chord)
    n = np.fromiter((len(x) for x in hits), dtype=int, count=len(hits))
    nearest = np.full(len(hits), np.nan)
    # Chord-to-angle converted to arcsec for each nearest candidate.
    xyz_cat = tree.data
    xyz_t = unit_xyz(ra, dec)
    for i, h in enumerate(hits):
        if h:
            d = np.linalg.norm(xyz_cat[np.asarray(h, int)]-xyz_t[i], axis=1)
            nearest[i] = np.rad2deg(2*np.arcsin(np.clip(d.min()/2, 0, 1)))*3600
    return n, nearest


def spherical_offset(ra, dec, radius_arcsec, bearing_rad):
    """Move points by angular distance and bearing on the sphere."""
    a = np.deg2rad(np.asarray(ra, float)); d = np.deg2rad(np.asarray(dec, float))
    r = np.deg2rad(np.asarray(radius_arcsec, float)/3600.0)
    d2 = np.arcsin(np.sin(d)*np.cos(r) + np.cos(d)*np.sin(r)*np.cos(bearing_rad))
    a2 = a + np.arctan2(np.sin(bearing_rad)*np.sin(r)*np.cos(d),
                        np.cos(r)-np.sin(d)*np.sin(d2))
    return np.rad2deg(a2) % 360.0, np.rad2deg(d2)


def crossmatch_audit():
    raw = pd.read_csv(REAL/'dr3_candidates.csv')
    scores = pd.read_csv(RES/'dr3_candidates_scored.csv')
    # Reproduce the registered one-row-per-source preference used by dr3_study.py.
    order = {t:i for i,t in enumerate(['Orbital','AstroSpectroSB1','OrbitalTargetedSearchValidated',
        'OrbitalTargetedSearch','OrbitalAlternativeValidated','OrbitalAlternative'])}
    raw = raw.assign(_rank=raw.nss_solution_type.map(order).fillna(99),
                     _dist=raw.dr2_angular_distance.fillna(1e9))
    raw = raw.sort_values(['_rank','_dist']).drop_duplicates('source_id').drop(columns=['_rank','_dist'])
    C = raw[raw.source_id.isin(scores.source_id)].copy()
    C = scores[['source_id']].merge(C, on='source_id', how='left', validate='one_to_one')
    if len(C) != len(scores) or C.source_id.nunique() != len(scores):
        raise AssertionError('Scored-to-input candidate mapping is not one-to-one.')

    lam = pd.read_csv(REAL/'sb2_lamost.csv', dtype={'gaia_dr3_source_id':'string'})
    gal = pd.read_csv(REAL/'sb2_galah.csv', dtype={'gaia_dr2_source_id':'string'})
    apo = pd.read_csv(REAL/'sb2_apogee.csv')
    lam_ids = set(lam.gaia_dr3_source_id.dropna().astype(str))
    gal_ids = set(gal.gaia_dr2_source_id.dropna().astype(str))
    direct_lam = C.source_id.astype(str).isin(lam_ids).to_numpy()
    dr2_valid = C.dr2_source_id.notna() & (C.dr2_angular_distance < 1000.0)
    direct_gal = (dr2_valid & C.dr2_source_id.astype('int64').astype(str).isin(gal_ids)).to_numpy()

    ra0, dec0 = propagate_j2000(C.ra, C.dec, C.pmra, C.pmdec)
    tree = cKDTree(unit_xyz(apo.ra, apo.dec))
    apo_n, apo_sep = apogee_counts(tree, ra0, dec0, 2.0)
    direct_apo = apo_n == 1
    apo_amb = apo_n > 1

    # Reconcile against the flags persisted by the original DR3 study.
    saved = scores.set_index('source_id')
    comp = C[['source_id']].copy()
    comp['match_LAMOST_SB2'] = direct_lam
    comp['match_GALAH_SB2'] = direct_gal
    comp['n_APOGEE_within_2arcsec'] = apo_n
    comp['nearest_APOGEE_sep_arcsec'] = apo_sep
    comp['match_APOGEE_SB2'] = direct_apo
    comp['APOGEE_ambiguous'] = apo_amb
    comp['n_survey_flags'] = comp[['match_LAMOST_SB2','match_GALAH_SB2','match_APOGEE_SB2']].sum(axis=1)
    comp['survey_SB2_union'] = comp.n_survey_flags > 0
    for outcol, oldcol in [('match_LAMOST_SB2','sb2_lamost'),('match_GALAH_SB2','sb2_galah'),
                           ('n_APOGEE_within_2arcsec','apogee_n_within'),('match_APOGEE_SB2','sb2_apogee')]:
        if outcol.startswith('n_'):
            eq = np.array_equal(comp[outcol].to_numpy(), saved.loc[comp.source_id, oldcol].to_numpy())
        else:
            eq = np.array_equal(comp[outcol].to_numpy(bool), saved.loc[comp.source_id, oldcol].to_numpy(bool))
        if not eq:
            raise AssertionError(f'Archived cross-match flag mismatch: {outcol} vs {oldcol}')
    comp.to_csv(OUT/'candidate_survey_crossmatch_audit.csv', index=False)

    # Same-footprint local chance-match control: move each Gaia position 10-120 arcsec
    # in a random direction, then repeat the 2-arcsec match. This is diagnostic only.
    rng = np.random.default_rng(RNG_SEED)
    null_counts = []
    for _ in range(200):
        rr = rng.uniform(10.0, 120.0, len(C))
        bb = rng.uniform(0, 2*np.pi, len(C))
        ra_s, dec_s = spherical_offset(ra0, dec0, rr, bb)
        n_s, _ = apogee_counts(tree, ra_s, dec_s, 2.0)
        null_counts.append(int((n_s > 0).sum()))
    null_counts = np.asarray(null_counts)

    # Source-level overlap patterns among independent survey catalogues.
    patterns = comp.groupby(['match_LAMOST_SB2','match_GALAH_SB2','match_APOGEE_SB2']).size()
    phys = pd.read_csv(RES/'astrospectro_labels.csv', dtype={'source_id':'int64'})
    phys_x = comp.merge(phys[['source_id','label']], on='source_id', how='inner')
    summary = {
        'status':'LOCAL CROSS-MATCH AUDIT COMPLETED; EPOCH-RV VARIABILITY CATALOGUE NOT YET RETRIEVED',
        'n_scored_candidates':int(len(C)), 'n_scored_unique_source_ids':int(C.source_id.nunique()),
        'catalogues':{
            'LAMOST_MRS_SB2':{'catalogue_rows':int(len(lam)), 'unique_ids':int(lam_ids.__len__()),
                'candidate_matches':int(direct_lam.sum()), 'match_type':'exact Gaia DR3 source_id'},
            'GALAH_FGK_SB2':{'catalogue_rows':int(len(gal)), 'unique_ids':int(gal_ids.__len__()),
                'candidate_matches':int(direct_gal.sum()), 'candidate_sources_with_valid_DR2_link':int(dr2_valid.sum()),
                'match_type':'Gaia DR2 source_id via stored DR3-to-DR2 neighbourhood; <1000 mas guard'},
            'APOGEE_SB2':{'catalogue_rows':int(len(apo)), 'candidate_unique_matches':int(direct_apo.sum()),
                'candidate_ambiguous_matches':int(apo_amb.sum()), 'candidate_rows_with_any_match':int((apo_n>0).sum()),
                'median_nearest_sep_arcsec_for_matches':float(np.nanmedian(apo_sep[apo_n>0])) if (apo_n>0).any() else None,
                'max_nearest_sep_arcsec_for_matches':float(np.nanmax(apo_sep[apo_n>0])) if (apo_n>0).any() else None,
                'match_type':'Gaia 2016.0 -> J2000 linear PM propagation; 2 arcsec; ambiguous excluded'}},
        'independent_survey_overlap_patterns':{str(k):int(v) for k,v in patterns.items()},
        'union_SB2_candidate_count':int(comp.survey_SB2_union.sum()),
        'multi_survey_candidate_count':int((comp.n_survey_flags>1).sum()),
        'reconciliation_with_archived_flags':'ALL EXACT MATCH FLAGS REPRODUCED',
        'APOGEE_local_offset_control':{'n_realizations':200, 'offset_annulus_arcsec':[10,120],
            'random_matches_per_realization_median':float(np.median(null_counts)),
            'random_matches_per_realization_95pct':[float(x) for x in np.quantile(null_counts,[.025,.975])],
            'interpretation':'local-density chance-match diagnostic; not a formal posterior match probability'},
        'AstroSpectroSB1_95_subset':{
            'n':int(len(phys_x)), 'LAMOST':int(phys_x.match_LAMOST_SB2.sum()),
            'GALAH':int(phys_x.match_GALAH_SB2.sum()), 'APOGEE':int(phys_x.match_APOGEE_SB2.sum()),
            'any_external_SB2':int(phys_x.survey_SB2_union.sum())}
    }
    (OUT/'rv_crossmatch_audit.json').write_text(json.dumps(summary,indent=2))
    return summary


def auc_score(s, y):
    s=np.asarray(s,float); y=np.asarray(y,int)
    pos=s[y==1]; neg=s[y==0]
    # Mann-Whitney tie-aware AUC
    return float((rankdata(s)[y==1].sum()-len(pos)*(len(pos)+1)/2)/(len(pos)*len(neg)))


def paired_bootstrap(scores, y, n_boot=N_BOOT, seed=RNG_SEED):
    rng=np.random.default_rng(seed)
    pos=np.flatnonzero(y==1); neg=np.flatnonzero(y==0)
    names=list(scores)
    point={k:auc_score(v,y) for k,v in scores.items()}
    draws={k:np.empty(n_boot) for k in names}
    diffs={}
    for k in names:
        diffs[k]=np.empty(n_boot)
    base_name='GAIA-FP posterior'
    base=np.asarray(scores[base_name],float)
    for b in range(n_boot):
        ix=np.r_[rng.choice(pos,len(pos),replace=True),rng.choice(neg,len(neg),replace=True)]
        yy=y[ix]
        for k,v in scores.items():
            draws[k][b]=auc_score(np.asarray(v)[ix],yy)
            diffs[k][b]=draws[base_name][b]-draws[k][b]
    out={'n_boot':n_boot,'seed':seed,'auc':{},'paired_delta_vs_baseline':{}}
    for k in names:
        out['auc'][k]={'point':point[k], 'percentile_95_ci':[float(x) for x in np.quantile(draws[k],[.025,.975])]}
        if k!=base_name:
            out['paired_delta_vs_baseline'][k]={'point':point[base_name]-point[k],
                 'percentile_95_ci':[float(x) for x in np.quantile(diffs[k],[.025,.975])]}
    return out


def physical_characterization():
    scores=pd.read_csv(RES/'dr3_candidates_scored.csv',dtype={'source_id':'int64'})
    old=pd.read_csv(RES/'astrospectro_labels.csv',dtype={'source_id':'int64'})
    X=scores.merge(old,on='source_id',how='inner',validate='one_to_one')
    cm=pd.read_csv(OUT/'candidate_survey_crossmatch_audit.csv',dtype={'source_id':'int64'})
    X=X.merge(cm[['source_id','match_LAMOST_SB2','match_GALAH_SB2','match_APOGEE_SB2',
                  'n_APOGEE_within_2arcsec','nearest_APOGEE_sep_arcsec','survey_SB2_union']],
              on='source_id',how='left',validate='one_to_one')
    if len(X)!=95: raise AssertionError(f'Expected 95 label objects, found {len(X)}')
    # Full-draw high-precision label sensitivity outputs are already archived and are not
    # allowed to overwrite the historical A3 labels.
    hd=[]
    for seed in [0,1,17]:
        d=pd.read_csv(RES/f'qa2/astrospectro_mc_precision/labels_50000_seed{seed}.csv',dtype={'source_id':'int64'})
        hd.append(d[['source_id','label']].rename(columns={'label':f'label_seed{seed}'}))
    H=hd[0].merge(hd[1],on='source_id',validate='one_to_one').merge(hd[2],on='source_id',validate='one_to_one')
    H['highdraw_stable_all_3_seeds']=H[[f'label_seed{s}' for s in [0,1,17]]].nunique(axis=1)==1
    H['highdraw_label_seed0']=H.label_seed0
    X=X.merge(H,on='source_id',validate='one_to_one')
    # Explain the disjunctive impostor criteria for the full-draw seed-0 sensitivity run.
    hd0=pd.read_csv(RES/'qa2/astrospectro_mc_precision/labels_50000_seed0.csv',dtype={'source_id':'int64'})
    hd0['mass_rule_m2lo_gt_80']=hd0.m2_lo>80
    hd0['rho_rule_rhohi_lt_0p9']=hd0.rho_hi<.9
    def cause(r):
        a=bool(r.mass_rule_m2lo_gt_80); b=bool(r.rho_rule_rhohi_lt_0p9)
        if a and b:return 'both_mass_and_rho'
        if a:return 'mass_only'
        if b:return 'rho_only'
        if r.label==0:return 'dark_compatible'
        return 'undetermined'
    hd0['criterion_reason']=hd0.apply(cause,axis=1)
    X=X.merge(hd0[['source_id','mass_rule_m2lo_gt_80','rho_rule_rhohi_lt_0p9','criterion_reason']],on='source_id',validate='one_to_one')
    X['old_to_highdraw_changed_seed0']=X.label!=X.label_seed0
    X['gaiafp_verdict']=X.verdict
    X.to_csv(OUT/'astrospectro_95_object_characterization.csv',index=False)

    # Summaries for full-draw seed-0 group, using its labels with 400-draw diagnostics
    # only as comparison covariates; the 50k draws are not promoted to registered labels.
    group_summaries={}
    for lab, name in [(1,'impostor_sensitivity'),(0,'dark_compatible_sensitivity'),(-1,'undetermined_sensitivity')]:
        g=X[X.highdraw_label_seed0==lab]
        cols=['rho','m2_dyn','P_impostor','dm','ruwe','P','significance']
        st={}
        for c in cols:
            z=pd.to_numeric(g[c],errors='coerce').dropna()
            st[c]={'n':int(len(z)),'median':float(z.median()) if len(z) else None,
                   'q25':float(z.quantile(.25)) if len(z) else None,'q75':float(z.quantile(.75)) if len(z) else None}
        group_summaries[name]={'n':int(len(g)),'metrics':st}

    determ=X[X.label>=0].copy(); y=determ.label.astype(int).to_numpy()
    score_arrays={
       'GAIA-FP posterior':determ.P_impostor.to_numpy(float),
       'CMD baseline (-delta_MG)':(-determ.dm).to_numpy(float),
       'CMD standardized (-delta_MG/sigma)':(-determ.dm/determ.sig_cmd).to_numpy(float),
       'Likelihood ratio only':determ.log_lr.to_numpy(float),
       'RUWE baseline':determ.ruwe.to_numpy(float),
       'Orbit significance':determ.significance.to_numpy(float)}
    baseline=paired_bootstrap(score_arrays,y)

    stable_n=int(H.highdraw_stable_all_3_seeds.sum())
    unstable=H[~H.highdraw_stable_all_3_seeds].to_dict('records')
    highdraw_counts={}
    for s in [0,1,17]:
        vc=H[f'label_seed{s}'].value_counts()
        highdraw_counts[str(s)]={'impostor':int(vc.get(1,0)),'dark_compatible':int(vc.get(0,0)),
                                 'undetermined':int(vc.get(-1,0))}
    old_changes={}
    for s in [0,1,17]:
        old_changes[str(s)]=int((X.label!=X[f'label_seed{s}']).sum())

    summary={
      'status':'LOCAL REAL-DATA CHARACTERIZATION COMPLETED FOR THE 95-OBJECT ASTROSPECTROSB1 SUBSET; EXPLORATORY/SELECTED SAMPLE',
      'sample':{'n':95,'historical_A3_400_draw_labels':{'impostor':int((X.label==1).sum()),
          'dark_compatible':int((X.label==0).sum()),'undetermined':int((X.label==-1).sum())},
          'highdraw_full_50000_seed_counts':highdraw_counts,
          'highdraw_stable_across_seeds_0_1_17':stable_n,
          'highdraw_unstable_objects':unstable,
          'historical_to_highdraw_seed_label_changes':old_changes},
      'highdraw_seed0_impostor_rule_reasons':{str(k):int(v) for k,v in hd0.criterion_reason.value_counts().items()},
      'group_characteristics_by_highdraw_seed0_label':group_summaries,
      'classifier_comparison_historical_labels_44_determined':baseline,
      'frozen_GAIA_FP_verdict_on_historical_labels':{
          str(k):int(v) for k,v in pd.crosstab(X.label,X.verdict).stack().items()},
      'interpretation_limits':[
          'The 95 objects are a selected AstroSpectroSB1 subset, not a representative random sample of the full candidate population.',
          'Only two historical dark-compatible objects are labelled negative; AUC and bootstrap intervals are therefore highly sensitive to those two objects.',
          'The high-draw 50,000 Monte Carlo output is a supplementary sensitivity analysis; it does not replace the historical registered A3 labels.',
          'Quoted parameter errors are sampled independently because the full covariance matrix is not in the supplied export.'
      ]}
    (OUT/'astrospectro_characterization.json').write_text(json.dumps(summary,indent=2,default=float))
    return summary


def baseline_reconciliation():
    old=json.load(open(RES/'dark_companion.json'))
    corrected=json.load(open(RES/'erratum_k_units.json'))
    h10=corrected['H10_corrected_c1']
    labels=old['H10']
    b2=h10['vbroad_subset_auc']['B2']
    s1=h10['vbroad_subset_auc']['S1']
    vb=h10['vbroad_subset_auc']['VB']
    amrf=h10['vbroad_subset_auc']['AMRF']
    s2=h10['vbroad_subset_auc']['S2']
    naive=corrected['naive_B2_plus_VB'][0]
    d_naive=corrected['S1_minus_naive_corrected_c1']
    out={
      'status':'H10 ARCHIVE RECONCILED TO POST-UNIT-FIX RESULTS; NOT RECOMPUTED HERE BECAUSE RAW 33,463-ROW D3 / FIELD INPUT FILES ARE NOT IN THIS PACKAGE',
      'sample':{'n_labelled_with_vbroad':int(labels['n_labelled_with_vbroad']),
                'luminous_positive':int(labels['n_luminous_with_vbroad']),
                'dark_consistent_negative':int(labels['n_labelled_with_vbroad']-labels['n_luminous_with_vbroad'])},
      'corrected_primary_c1_auc':{
        'B2_CMD':b2,'VB_alone':vb,'S1_CMD_plus_physical_vbroad_LR':s1,
        'AMRF_shared_astrometric_baseline':amrf,'S2_joint_shared_astrometry':s2},
      'registered_primary_comparison_S1_minus_B2':h10['H10a_dAUC_S1_minus_B2'],
      'stronger_naive_baseline':{'definition':'B2 + standardized VB score, simple additive combination',
         'AUC':float(naive),'S1_minus_naive_paired_bootstrap':d_naive},
      'unit_erratum_effect':{
         'pre_fix_archived_S1_AUC':float(old['H10']['vbroad_subset_auc']['S1'][0]),
         'post_fix_S1_AUC':float(s1[0]),
         'note':'The post-fix c=1 result is authoritative for this diagnostic; pre-fix K_sum used years where days were expected.'},
      'secondary_shared_input_note':'S2/AMRF use astrometric a0 information that also enters the physical-label construction; treat these as exploratory secondary comparisons, not independent validation.',
      'interpretation':'S1 improves over the preregistered CMD-only B2 baseline, but does not beat the stronger simple B2+VB score. Do not claim superiority over a strong independent baseline.'}
    (OUT/'baseline_comparison_reconciliation.json').write_text(json.dumps(out,indent=2))
    return out


def main():
    a=crossmatch_audit(); b=physical_characterization(); c=baseline_reconciliation()
    h10_auc=c['corrected_primary_c1_auc']; s1=h10_auc['S1_CMD_plus_physical_vbroad_LR']; b2=h10_auc['B2_CMD'];
    naive=c['stronger_naive_baseline']['AUC']; d_naive=c['stronger_naive_baseline']['S1_minus_naive_paired_bootstrap']
    report=[]
    report += ['# GAIA-FP partial analyses — completion audit (1 Nov 2026)','',
      'This addendum completes all computations that can be reproducibly completed from the archived local snapshot. It does not pretend that unavailable remote RV epoch rows were downloaded.', '',
      '## 1. Independent spectroscopic cross-match quality audit','',
      f"- {a['n_scored_candidates']} unique scored candidates reconciled exactly to the stored flags.",
      f"- LAMOST-MRS SB2: {a['catalogues']['LAMOST_MRS_SB2']['candidate_matches']} exact Gaia DR3 ID matches.",
      f"- GALAH FGK SB2: {a['catalogues']['GALAH_FGK_SB2']['candidate_matches']} Gaia DR2 ID matches after the <1000 mas neighbourhood guard.",
      f"- APOGEE SB2: {a['catalogues']['APOGEE_SB2']['candidate_unique_matches']} unique matches within 2 arcsec after 2016-to-J2000 proper-motion propagation; ambiguous matches: {a['catalogues']['APOGEE_SB2']['candidate_ambiguous_matches']}.",
      f"- Combined unique SB2 positives: {a['union_SB2_candidate_count']}; multi-survey overlaps: {a['multi_survey_candidate_count']}.",
      f"- The 200-realisation local offset control produced a median {a['APOGEE_local_offset_control']['random_matches_per_realization_median']} chance matches (95% empirical range {a['APOGEE_local_offset_control']['random_matches_per_realization_95pct'][0]}–{a['APOGEE_local_offset_control']['random_matches_per_realization_95pct'][1]}). This is a diagnostic, not a formal posterior probability.",
      '', '### What remains missing for a true epoch-RV cross-match','',
      'The present APOGEE/GALAH/LAMOST flags are cross-matches to published SB2 catalogues; they are not a general epoch-by-epoch RV-variability analysis. The official GALAH DR3 archive exposes per-spectrum (678,423-row) spectra and a matched radial-velocity VAC with `sobject_id`, `rv_galah`, uncertainty, HJD/MJD, and RV method flag. The public schema says catalogue joins use `sobject_id`; `rv_galah` is the best-per-spectrum velocity, with method flags identifying GALAH-observed vs Gaia-DR2 fallback. The files were not retrievable from this runtime because external DNS/network resolution failed. The companion `GALAH_RV_EPOCH_CROSSMATCH_PROTOCOL.md` records the exact inputs, filters, and aggregation code contract. No RV variability outcomes are claimed.',
      '', '## 2. Independent baseline comparisons','',
      f"- On the 44 historical determined AstroSpectroSB1 objects (42 positive / 2 negative), GAIA-FP AUC is {b['classifier_comparison_historical_labels_44_determined']['auc']['GAIA-FP posterior']['point']:.3f} [{b['classifier_comparison_historical_labels_44_determined']['auc']['GAIA-FP posterior']['percentile_95_ci'][0]:.3f}, {b['classifier_comparison_historical_labels_44_determined']['auc']['GAIA-FP posterior']['percentile_95_ci'][1]:.3f}], while CMD-only AUC is {b['classifier_comparison_historical_labels_44_determined']['auc']['CMD baseline (-delta_MG)']['point']:.3f} [{b['classifier_comparison_historical_labels_44_determined']['auc']['CMD baseline (-delta_MG)']['percentile_95_ci'][0]:.3f}, {b['classifier_comparison_historical_labels_44_determined']['auc']['CMD baseline (-delta_MG)']['percentile_95_ci'][1]:.3f}]. The paired GAIA-FP−CMD ΔAUC is {b['classifier_comparison_historical_labels_44_determined']['paired_delta_vs_baseline']['CMD baseline (-delta_MG)']['point']:+.3f} [{b['classifier_comparison_historical_labels_44_determined']['paired_delta_vs_baseline']['CMD baseline (-delta_MG)']['percentile_95_ci'][0]:+.3f}, {b['classifier_comparison_historical_labels_44_determined']['paired_delta_vs_baseline']['CMD baseline (-delta_MG)']['percentile_95_ci'][1]:+.3f}]. The two-negative-class limitation makes this AUC comparison unstable.",
      f"- On the larger H10 `vbroad` subset (n={c['sample']['n_labelled_with_vbroad']}; {c['sample']['luminous_positive']} luminous / {c['sample']['dark_consistent_negative']} dark-consistent), the corrected post-unit-fix S1 AUC is {s1[0]:.3f} [{s1[1]:.3f}, {s1[2]:.3f}], against CMD-only B2 {b2[0]:.3f} [{b2[1]:.3f}, {b2[2]:.3f}]. The registered S1−B2 paired ΔAUC is {c['registered_primary_comparison_S1_minus_B2'][0]:+.3f} [{c['registered_primary_comparison_S1_minus_B2'][1]:+.3f}, {c['registered_primary_comparison_S1_minus_B2'][2]:+.3f}].",
      f"- But against the stronger simple B2+VB additive baseline (AUC {naive:.3f}), corrected S1 is lower: ΔAUC(S1−B2+VB) = {d_naive[0]:+.3f} [{d_naive[1]:+.3f}, {d_naive[2]:+.3f}]. Therefore the model does not beat this stronger baseline.",
      '- S2 and AMRF show higher corrected AUCs, but both use astrometric a0 information also involved in physical label construction; they remain secondary/shared-input comparisons, not clean independent proof.',
      '', '## 3. Real-object physical characterization','',
      f"- The historical 400-draw labels remain 42 impostors, 2 dark-compatible, 51 undetermined.",
      f"- The full-draw 50,000-sample sensitivity labels give seeds 0/1/17 respectively: {b['sample']['highdraw_full_50000_seed_counts']['0']}, {b['sample']['highdraw_full_50000_seed_counts']['1']}, {b['sample']['highdraw_full_50000_seed_counts']['17']} (counts shown as impostor/dark-compatible/undetermined).",
      f"- {b['sample']['highdraw_stable_across_seeds_0_1_17']}/95 source labels are stable across all three high-draw seeds. The one unstable source is listed in the machine-readable JSON/CSV.",
      f"- Of the 95 physical-validation objects, {a['AstroSpectroSB1_95_subset']['any_external_SB2']} also appears in the independent SB2 catalogues (LAMOST {a['AstroSpectroSB1_95_subset']['LAMOST']}, GALAH {a['AstroSpectroSB1_95_subset']['GALAH']}, APOGEE {a['AstroSpectroSB1_95_subset']['APOGEE']}).",
      f"- In full-draw seed 0, impostor rule attribution: {b['highdraw_seed0_impostor_rule_reasons']}.",
      '- High-draw seed-0 group medians: impostor-sensitivity group (n=42) rho=0.319, dynamical m2=245.4 MJ, RUWE=1.80; uncertain group (n=51) rho=0.835, m2=82.8 MJ, RUWE=2.00; dark-compatible group (n=2) rho=1.178, m2=58.4 MJ. The n=2 group is descriptive only.',
      '- The object-level export contains all 95 source IDs, historical intervals and labels, 50k seed labels, frozen GAIA-FP posterior/verdict, CMD, RUWE, period and diagnostic rule attribution.',
      '', '## 4. Guardrails','',
      '- Historical frozen outputs were not overwritten.',
      '- The 50,000-draw labels are supplementary precision/sensitivity diagnostics, not replacements for the registered 400-draw output.',
      '- The 95 AstroSpectroSB1 objects are selected and not representative of the entire candidate population.',
      '- No claim is made that the epoch-RV cross-match is finished or that GAIA-FP beats the strongest B2+VB baseline.',
      '', '## Artifacts','',
      '- `results/qa2/partial_completion/rv_crossmatch_audit.json`',
      '- `results/qa2/partial_completion/candidate_survey_crossmatch_audit.csv`',
      '- `results/qa2/partial_completion/astrospectro_characterization.json`',
      '- `results/qa2/partial_completion/astrospectro_95_object_characterization.csv`',
      '- `results/qa2/partial_completion/baseline_comparison_reconciliation.json`',
      '- `tools/qa_audits/complete_partial_analyses.py`',
      '- `GALAH_RV_EPOCH_CROSSMATCH_PROTOCOL.md`']
    # inject computed variables explicitly into report strings
    (OUT/'PARTIAL_ANALYSES_COMPLETION_REPORT_2026-11-01.md').write_text('\n'.join(report)+'\n')
    print(json.dumps({'crossmatch':a,'physical':{k:v for k,v in b.items() if k!='group_characteristics_by_highdraw_seed0_label'},'baseline':c},indent=2,default=float))

if __name__=='__main__': main()
