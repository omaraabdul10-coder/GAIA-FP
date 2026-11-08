#!/usr/bin/env python3
"""Recompute row-level H10 S1 using the P-in-days K_sum correction.

The frozen mechanism_scored.csv intentionally retains the historical S1
column under S1_pre_erratum_DO_NOT_USE. This script creates a separate,
provenance-labelled corrected score table and verifies its labelled-cohort AUC
against results/erratum_k_units.json. It does not overwrite archived scores.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np, pandas as pd

def main(input_csv, reference_json, out_csv, out_json):
    root=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(root/'src'))
    import dark_companion as DC
    import rvs_phase_test as R
    def K_days(M1,M2,P_years,e,inc_deg):
        return R.K_sum_kms(M1,M2,np.asarray(P_years,float)*365.25,e,inc_deg)
    DC.K_sum_kms=K_days
    x=pd.read_csv(input_csv,dtype={'source_id':'string'})
    required={'source_id','CMDLR','dm','sig','vbroad','vbroad_error','vb_med','vb_sig','m1','period','eccentricity','inc','pavg','label','B2','VB'}
    if not required<=set(x): raise ValueError(f'Missing columns: {sorted(required-set(x))}')
    good=np.isfinite(x[['CMDLR','dm','sig','vbroad','vb_med','vb_sig','m1','period','eccentricity','inc','pavg']]).all(axis=1)
    good &= (x.sig>0)&(x.vb_sig>0)&(x.m1>0)&(x.period>0)&(x.vbroad_nb_transits>=5)
    score=np.full(len(x),np.nan); idx=np.flatnonzero(good.to_numpy())
    for part in np.array_split(idx,max(1,int(np.ceil(len(idx)/400)))):
        g=x.iloc[part]
        W=DC.q_weights(g.dm.to_numpy(float),g.sig.to_numpy(float))
        lvb=DC.lr_vbroad(g.vbroad.to_numpy(float),g.vbroad_error.fillna(0).to_numpy(float),
          g.vb_med.to_numpy(float),g.vb_sig.to_numpy(float),g.m1.to_numpy(float),g.period.to_numpy(float),
          g.eccentricity.fillna(0).to_numpy(float),g.inc.to_numpy(float),g.pavg.to_numpy(float),W,c=1.0)
        score[part]=g.CMDLR.to_numpy(float)+lvb
    x['S1_corrected_c1']=score
    x['S1_provenance']='recomputed: K_sum_kms(period_days); c=1; q posterior from CMD only; not overwriting legacy column'
    x['S1_pre_erratum_DO_NOT_USE']=x['S1_pre_erratum_DO_NOT_USE'] if 'S1_pre_erratum_DO_NOT_USE' in x else np.nan
    x.to_csv(out_csv,index=False)
    lab=x.label.to_numpy(int); s=score; valid=(lab>=0)&np.isfinite(s)&np.isfinite(x.VB.to_numpy(float))
    from sklearn.metrics import roc_auc_score
    y=lab[valid]; out={'n_rows':len(x),'n_corrected_scores':int(np.isfinite(s).sum()),'n_labelled_valid':int(valid.sum()),
      'n_luminous':int((y==1).sum()),'n_dark_consistent':int((y==0).sum()),
      'auc_S1_corrected_c1':float(roc_auc_score(y,s[valid])),
      'auc_B2':float(roc_auc_score(y,x.B2.to_numpy(float)[valid])),
      'auc_VB':float(roc_auc_score(y,x.VB.to_numpy(float)[valid])),
      'auc_B2_plus_VB':float(roc_auc_score(y,(x.B2+x.VB).to_numpy(float)[valid])),
      'score_direction':'higher = more luminous-impostor-like; lower = more dark-companion-consistent',
      'formula':'S1 = CMDLR + lr_vbroad; K_sum_kms receives period in days (P_years*365.25); c=1.0',
      'input_sha256':hashlib.sha256(Path(input_csv).read_bytes()).hexdigest(),
      'output_csv_sha256':hashlib.sha256(Path(out_csv).read_bytes()).hexdigest()}
    if reference_json and Path(reference_json).exists():
        ref=json.loads(Path(reference_json).read_text())
        auc_ref=ref['H10_corrected_c1']['vbroad_subset_auc']['S1'][0]
        out['reference_auc_from_erratum_json']=float(auc_ref);out['absolute_auc_difference_from_reference']=abs(out['auc_S1_corrected_c1']-float(auc_ref))
        out['reference_reproduction_pass']=out['absolute_auc_difference_from_reference']<2e-4
        if not out['reference_reproduction_pass']:
            raise AssertionError('Corrected row-level H10 AUC failed reproduction tolerance; do not promote this output.')
    # External published Gaia NS example found in mechanism_scored, not among the 95 selected physical-label sample.
    ext='1801110822095134848'; rows=x[x.source_id.astype(str)==ext]
    if len(rows)==1 and np.isfinite(rows.S1_corrected_c1.iloc[0]):
        rr=rows.iloc[0]; dark=s[valid&(lab==0)]; lum=s[valid&(lab==1)]
        out['external_NS_reference_1801110822095134848']={
          'n_rows_matched':1,'label_in_H10':'unlabelled/undetermined (-1)','S1_corrected_c1':float(rr.S1_corrected_c1),
          'B2':float(rr.B2),'VB':float(rr.VB),'a0_mas':float(rr.a0),'m2dyn_msun':float(rr.m2dyn),
          'S1_percentile_within_dark_consistent_group':float(np.mean(dark<=rr.S1_corrected_c1)),
          'S1_percentile_within_luminous_group':float(np.mean(lum<=rr.S1_corrected_c1)),
          'S1_percentile_within_all_labelled':float(np.mean(s[valid]<=rr.S1_corrected_c1)),
          'interpretation':'One external, literature RV-followed NS-system reference only; not part of the 95-object substellar validation cohort. Descriptive single-object check, not a new performance estimate.'}
    Path(out_json).write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',default='results/mechanism_scored.csv');p.add_argument('--reference-json',default='results/erratum_k_units.json');p.add_argument('--out-csv',default='results/final_completion/mechanism_scored_S1_CORRECTED_c1.csv');p.add_argument('--out-json',default='results/final_completion/S1_CORRECTED_c1_VALIDATION.json');a=p.parse_args()
    main(a.input,a.reference_json,a.out_csv,a.out_json)
