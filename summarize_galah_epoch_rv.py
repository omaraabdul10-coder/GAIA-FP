#!/usr/bin/env python3
"""Summarize GALAH per-epoch RV data against all 2,102 GAIA-FP candidates.

Does not apply an unregistered binary threshold. Rows with fallback/no-method
flags or invalid uncertainties are excluded from variability calculations.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import chi2

ROOT=Path(__file__).resolve().parents[2]
DEFAULT_IDS=ROOT/'results/qa2/partial_completion/galah_adql/candidate_source_ids.txt'

def summarize(group: pd.DataFrame) -> dict:
    rv=pd.to_numeric(group['rv_kms'],errors='coerce').to_numpy(float)
    er=pd.to_numeric(group['rv_error_kms'],errors='coerce').to_numpy(float)
    flag=pd.to_numeric(group['rv_method_flag'],errors='coerce').to_numpy(float)
    hjd=pd.to_numeric(group.get('hjd',pd.Series(np.nan,index=group.index)),errors='coerce').to_numpy(float)
    mjd=pd.to_numeric(group.get('mjd_local',pd.Series(np.nan,index=group.index)),errors='coerce').to_numpy(float)
    # Do not mix HJD and MJDlocal zero-points within a source. Prefer HJD
    # whenever any HJD values exist; use MJDlocal only if HJD is absent entirely.
    if np.isfinite(hjd).any():
        epoch=hjd; epoch_scale='HJD'
    else:
        epoch=mjd; epoch_scale='MJDlocal'
    good=np.isin(flag,[0,1]) & np.isfinite(rv) & np.isfinite(er) & (er>0) & np.isfinite(epoch)
    rv,er,epoch=rv[good],er[good],epoch[good]
    # Deduplicate identical GALAH ID / epoch rows; conflicting duplicate rows are
    # collapsed by inverse-variance weighting to avoid double-counting exposures.
    gid=group.get('galah_id',pd.Series('',index=group.index)).astype(str).to_numpy()[good]
    if len(rv):
        tmp=pd.DataFrame({'gid':gid,'epoch':epoch,'rv':rv,'err':er})
        ded=[]
        for _,g in tmp.groupby(['gid','epoch'],sort=False):
            w=1/np.square(g.err.to_numpy())
            ded.append((float(g.epoch.iloc[0]),float(np.sum(w*g.rv)/np.sum(w)),float(np.sqrt(1/np.sum(w)))))
        ded=pd.DataFrame(ded,columns=['epoch','rv','err'])
        rv=ded.rv.to_numpy(); er=ded.err.to_numpy(); epoch=ded.epoch.to_numpy()
    n=len(rv)
    out={'n_valid_epochs':int(n),'epoch_scale':epoch_scale if n else None,
         'time_baseline_days':float(np.ptp(epoch)) if n>=2 else None,
         'weighted_mean_rv_kms':None,'weighted_rms_kms':None,'peak_to_peak_kms':None,
         'robust_mad_sigma_kms':None,'chi2_constant_rv':None,'chi2_dof':max(n-1,0),
         'chi2_p_value':None,'variability_assessment':'insufficient_data' if n<2 else 'diagnostic_only'}
    if n:
        w=1/np.square(er); mu=float(np.sum(w*rv)/np.sum(w))
        scatter=float(np.sqrt(np.sum(w*np.square(rv-mu))/np.sum(w)))
        mad=float(1.4826*np.median(np.abs(rv-np.median(rv))))
        out.update(weighted_mean_rv_kms=mu,weighted_rms_kms=scatter,
                   peak_to_peak_kms=float(np.ptp(rv)),robust_mad_sigma_kms=mad)
    if n>=2:
        q=float(np.sum(np.square((rv-mu)/er)))
        out.update(chi2_constant_rv=q,chi2_p_value=float(chi2.sf(q,n-1)))
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',type=Path)
    ap.add_argument('--outdir',type=Path,default=ROOT/'results/qa2/partial_completion/galah_epoch_rv')
    ap.add_argument('--selftest',action='store_true')
    args=ap.parse_args()
    if args.selftest:
        g=pd.DataFrame({'galah_id':['a','a','a','a'],'rv_kms':[10.,12.,99.,11.],
          'rv_error_kms':[1.,1.,1.,1.],'rv_method_flag':[0,1,2,4],
          'hjd':[1.,2.,3.,4.],'mjd_local':[np.nan]*4})
        r=summarize(g)
        assert r['n_valid_epochs']==2 and r['peak_to_peak_kms']==2.0 and r['chi2_dof']==1
        print(json.dumps({'status':'SYNTHETIC SELFTEST ONLY — NOT A SCIENTIFIC RESULT','result':r},indent=2))
        return
    if args.input is None or not args.input.exists():
        raise SystemExit('Input epoch-RV file missing. See GALAH_RV_EPOCH_CROSSMATCH_PROTOCOL.md and query package.')
    ids=pd.read_csv(DEFAULT_IDS,header=None,names=['source_id'],dtype='int64')
    df=pd.read_csv(args.input,dtype={'source_id':'string','galah_id':'string'})
    required=['source_id','galah_id','rv_kms','rv_error_kms','rv_method_flag']
    missing=[c for c in required if c not in df.columns]
    if missing: raise SystemExit(f'Missing required columns: {missing}')
    rows=[]
    for sid,g in df.groupby('source_id',sort=False):
        rows.append({'source_id':str(sid),**summarize(g)})
    result=pd.DataFrame(rows)
    out=ids.assign(source_id=ids.source_id.astype(str)).merge(result,on='source_id',how='left')
    out['n_valid_epochs']=out.n_valid_epochs.fillna(0).astype(int)
    out['variability_assessment']=out.variability_assessment.fillna('no_GALAH_match')
    args.outdir.mkdir(parents=True,exist_ok=True)
    out.to_csv(args.outdir/'galah_epoch_rv_candidate_summary.csv',index=False)
    summary={'input_rows':int(len(df)),'matched_candidate_sources':int(df.source_id.nunique()),
       'all_candidates':int(len(ids)),'candidates_with_ge2_valid_epochs':int((out.n_valid_epochs>=2).sum()),
       'candidates_with_ge3_valid_epochs':int((out.n_valid_epochs>=3).sum()),
       'method_flags_in_input':{str(k):int(v) for k,v in df.rv_method_flag.value_counts(dropna=False).items()},
       'note':'Continuous diagnostics only; no binary cutoff or RV-confirmed false-positive label applied.'}
    (args.outdir/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
