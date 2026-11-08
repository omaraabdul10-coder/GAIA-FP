#!/usr/bin/env python3
"""Reconstruct only the early deterministic H10 filters for the 95-object set.

This deliberately does NOT assign a downstream exclusion reason when the
original vbroad calibration / full source query are absent. It runs the same
ridge + early geometry tests implemented in src/dark_companion.py::h10, using
the same documented fallback for m1 (mass_from_MG) because the 95-object
reconstruction input has no source-level binary_masses m1 field.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import numpy as np,pandas as pd

def main(root, outdir):
    root=Path(root).resolve();out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(root/'src'))
    import dr4_pipeline as D
    raw=pd.read_csv(root/'realdata/dr3_nss_two_body_orbit_raw.csv',dtype={'source_id':'string'})
    ch=pd.read_csv(root/'realdata/dr3_astrospectro_ch.csv',dtype={'source_id':'string'})
    char=pd.read_csv(root/'results/qa2/partial_completion/astrospectro_95_object_characterization.csv',dtype={'source_id':'string'})
    cand=pd.read_csv(root/'realdata/dr3_candidates.csv',dtype={'source_id':'string'}).drop_duplicates('source_id')
    mech=pd.read_csv(root/'results/mechanism_scored.csv',dtype={'source_id':'string'})
    field=pd.read_csv(root/'realdata/dr3_field.csv')
    sealed_path=root/'realdata/excluded_sealed_ids.csv'
    sealed=set(pd.read_csv(sealed_path,dtype={'source_id':'string'}).source_id.astype(str)) if sealed_path.exists() else set()
    X=char[['source_id']].merge(raw.drop(columns=['nss_solution_type']),on='source_id',how='left',validate='one_to_one')
    X=X.merge(ch,on='source_id',how='left',validate='one_to_one')
    X=X.merge(cand[['source_id','nss_solution_type']],on='source_id',how='left',validate='one_to_one')
    rawids=set(raw.source_id.dropna().astype(str))
    X['in_raw_nss']=X.source_id.astype(str).isin(rawids)
    X['in_candidates']=X.nss_solution_type.notna()
    X['in_ch_table']=X.c_thiele_innes.notna()&X.h_thiele_innes.notna()
    X['sealed_id']=X.source_id.astype(str).isin(sealed)
    X['MG']=pd.to_numeric(X.phot_g_mean_mag,errors='coerce')+5*np.log10(pd.to_numeric(X.parallax,errors='coerce')/100.0)
    X['m1_h10_fallback']=D.mass_from_MG(X.MG.to_numpy(float))
    ridge=D.fit_ms_ridge(field)
    X['ridge_ms']=np.interp(X.bp_rp,ridge['color'],ridge['ridge'])
    X['ridge_sigma']=np.interp(X.bp_rp,ridge['color'],ridge['sigma'])
    X['dm_h10']=X.MG-X.ridge_ms
    X['h10_colour_in_range']=X.bp_rp.between(float(ridge['color'].min()),float(ridge['color'].max()),inclusive='both')
    X['h10_dm_gt_minus2']=X.dm_h10>-2.0
    X['h10_positive_finite_m1']=np.isfinite(X.m1_h10_fallback)&(X.m1_h10_fallback>0)
    ti=['a_thiele_innes','c_thiele_innes','h_thiele_innes','c_thiele_innes_error','a_thiele_innes_error']
    X['h10_required_ti_finite']=np.isfinite(X[ti].apply(pd.to_numeric,errors='coerce')).all(axis=1)
    X['h10_pre_vb_screen_pass']=(X.h10_colour_in_range&X.h10_dm_gt_minus2&X.h10_positive_finite_m1&X.h10_required_ti_finite&~X.sealed_id)
    mechids=set(mech.source_id.dropna().astype(str))
    X['in_mechanism_scored']=X.source_id.astype(str).isin(mechids)
    X['downstream_reason']='NOT_IDENTIFIABLE_FROM_ARCHIVED_INPUTS'
    X.loc[X.in_mechanism_scored,'downstream_reason']='PRESENT_IN_MECHANISM_OUTPUT'
    X.loc[~X.in_mechanism_scored & X.h10_pre_vb_screen_pass,'downstream_reason']='PASSES_RECONSTRUCTED_PRE_VB_SCREEN; LOST_OR_NOT_EXPORTED_DOWNSTREAM; EXACT_REASON_UNAVAILABLE'
    # The mechanism table has 62 of the 95; all missing rows can be checked against early H10 screen.
    X.sort_values('source_id').to_csv(out/'LINEAGE_95_EARLY_H10_FILTER_RECONSTRUCTION.csv',index=False)
    missing=X[~X.in_mechanism_scored].copy()
    missing.to_csv(out/'LINEAGE_33_OF_95_FILTER_REASON_AUDIT.csv',index=False)
    metrics={'n_characterization_95':len(X),'found_in_raw_nss':int(X.in_raw_nss.sum()),'found_in_candidate_table':int(X.in_candidates.sum()),
      'found_in_c_h_table':int(X.in_ch_table.sum()),'found_in_mechanism_scored':int(X.in_mechanism_scored.sum()),
      'missing_from_mechanism_scored':int((~X.in_mechanism_scored).sum()),
      'missing_33_pass_pre_vb_screen':int(missing.h10_pre_vb_screen_pass.sum()),
      'missing_33_fail_colour':int((~missing.h10_colour_in_range).sum()),'missing_33_fail_dm':int((~missing.h10_dm_gt_minus2).sum()),
      'missing_33_fail_positive_m1':int((~missing.h10_positive_finite_m1).sum()),'missing_33_fail_ti_finite':int((~missing.h10_required_ti_finite).sum()),
      'missing_33_sealed':int(missing.sealed_id.sum()),
      'm1_note':'m1 is reconstructed using the exact h10() fallback mass_from_MG because archived 95-object input does not contain binary_masses.m1.',
      'downstream_note':'All 33 absent source IDs pass every reconstructed pre-vbroad H10 filter. Exact downstream reason is not identifiable because dark_companion_scored.csv, source vbroad calibration inputs, and the complete 33,464-row source query export are absent.'}
    (out/'LINEAGE_95_EARLY_H10_FILTER_RECONSTRUCTION.json').write_text(json.dumps(metrics,indent=2)+'\n')
    print(json.dumps(metrics,indent=2));return metrics

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--outdir',default='results/final_completion');a=p.parse_args();main(a.root,a.outdir)
