#!/usr/bin/env python3
"""APOGEE cadence-matched Keplerian RV recovery using true allVisit JD.

Input must be the accepted output of process_apogee_allvisit.py. We refuse
integer-MJD-only or proxy cadence: APOGEE's JD column is the visit JD-MID.
The injection is a detection-power study, not a measured-binary classifier.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import chi2

PERIODS_DAYS=[1.,10.,30.,100.,300.,1000.]
AMPLITUDES_KMS=[0.1,0.3,0.5,1.,3.,10.]
ECCENTRICITIES=[0.,0.3,0.6]
N_TRIALS=1000
ALPHA=0.01
SEED=20261103

def true_anomaly(jd,period,e,phase,omega):
    M=2*np.pi*(np.asarray(jd)-float(np.min(jd)))/period+phase
    M=(M+np.pi)%(2*np.pi)-np.pi; E=M.copy()
    for _ in range(50):
        d=(E-e*np.sin(E)-M)/(1-e*np.cos(E));E-=d
        if np.max(np.abs(d))<1e-12: break
    return 2*np.arctan2(np.sqrt(1+e)*np.sin(E/2),np.sqrt(1-e)*np.cos(E/2))

def kepler_rv(jd,period,e,K,phase,omega):
    nu=true_anomaly(jd,period,e,phase,omega)
    return K*(np.cos(nu+omega)+e*np.cos(omega))

def detect(y,err,alpha=ALPHA):
    if len(y)<3 or len(y)!=len(err) or np.any(~np.isfinite(err)) or np.any(err<=0): return False
    w=1/np.square(err);mu=np.sum(w*y)/np.sum(w);q=np.sum(w*np.square(y-mu))
    return chi2.sf(q,len(y)-1)<alpha

def run(input_csv,outdir,n_trials=N_TRIALS,seed=SEED):
    d=pd.read_csv(input_csv,dtype={'source_id':'string'})
    need={'source_id','JD','VERR'}
    if not need<=set(d):
        note='Use accepted APOGEE table with floating-point JD and VRELERR (canonicalized to VERR); integer MJD is insufficient.'
        raise ValueError(f'Input missing {sorted(need-set(d))}. {note}')
    d['JD']=pd.to_numeric(d.JD,errors='coerce');d['VERR']=pd.to_numeric(d.VERR,errors='coerce')
    d=d[np.isfinite(d.JD)&np.isfinite(d.VERR)&(d.VERR>0)]
    rng=np.random.default_rng(seed);rows=[];null_rows=[]
    for sid,g in d.groupby('source_id',dropna=True):
        g=g.sort_values('JD').drop_duplicates('JD');t=g.JD.to_numpy(float);err=g.VERR.to_numpy(float)
        if len(t)<3:continue
        fp=float(np.mean([detect(rng.normal(0,err),err) for _ in range(n_trials)]))
        null_rows.append({'source_id':str(sid),'n_epochs':len(t),'baseline_days':float(t.max()-t.min()),'null_false_positive_rate':fp})
        for P in PERIODS_DAYS:
          for K in AMPLITUDES_KMS:
           for e in ECCENTRICITIES:
            recovered=0
            for _ in range(n_trials):
                phase=rng.uniform(-np.pi,np.pi);omega=rng.uniform(0,2*np.pi)
                y=kepler_rv(t,P,e,K,phase,omega)+rng.normal(0,err)
                recovered+=int(detect(y,err))
            rows.append({'source_id':str(sid),'n_epochs':len(t),'baseline_days':float(t.max()-t.min()),
              'period_days':P,'K1_kms':K,'eccentricity':e,'n_trials':n_trials,
              'recovery_fraction':recovered/n_trials,'alpha':ALPHA,'seed':seed})
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    inj=pd.DataFrame(rows);nul=pd.DataFrame(null_rows)
    inj.to_csv(out/'exact_apogee_cadence_injection.csv',index=False)
    nul.to_csv(out/'exact_apogee_cadence_null_calibration.csv',index=False)
    if len(inj):
        agg=inj.groupby(['period_days','K1_kms','eccentricity'],as_index=False).agg(
          mean_recovery=('recovery_fraction','mean'),median_recovery=('recovery_fraction','median'),n_targets=('source_id','nunique'))
    else: agg=pd.DataFrame(columns=['period_days','K1_kms','eccentricity','mean_recovery','median_recovery','n_targets'])
    agg.to_csv(out/'exact_apogee_cadence_recovery_summary.csv',index=False)
    summary={'targets_with_ge3_epochs':int(nul.source_id.nunique()) if len(nul) else 0,'injection_rows':len(inj),
      'n_trials_per_cell_per_target':n_trials,'seed':seed,'alpha':ALPHA,
      'median_null_false_positive_rate':float(nul.null_false_positive_rate.median()) if len(nul) else None,
      'input_cadence':'actual allVisit JD (JD-MID), floating point days','measurement_error':'VRELERR (km/s)',
      'model':'Keplerian primary-star RV; random mean-anomaly phase and omega; Gaussian noise using each visit VRELERR',
      'note':'No source data were synthesized. Run only after official allVisit and allStarLite are retrieved. Detection power is conditional on the observed cadence and formal errors; it is not compact-object confirmation.'}
    (out/'exact_apogee_cadence_manifest.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--outdir',default='results/final_completion/apogee_exact_cadence');ap.add_argument('--trials',type=int,default=N_TRIALS);ap.add_argument('--seed',type=int,default=SEED);a=ap.parse_args();print(json.dumps(run(a.input,a.outdir,a.trials,a.seed),indent=2))
