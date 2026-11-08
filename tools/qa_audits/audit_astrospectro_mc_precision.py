#!/usr/bin/env python3
"""High-draw precision diagnostic for the 95-system DR3 AstroSpectroSB1 label check.

This is a sensitivity/audit product, NOT a replacement for the historical A3/H8
400-draw result. It uses every draw for both rho and m2, whereas the historical
astrospectro_check.py implementation computes m2 from only the first 150 draws.
The old results file is never overwritten.
"""
from __future__ import annotations
import argparse, json, sys, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import brentq
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from dr4_pipeline import campbell
MJ=1/1047.6

def solve_m2_vectorized(a1,P_yr,m1):
    """Solve m2^3/(m1+m2)^2 = a1^3/P^2 (solar-mass units) by monotone bisection."""
    f=np.asarray(a1,float)**3/(np.asarray(P_yr,float)**2)
    m1=np.asarray(m1,float);x=f/np.maximum(m1,1e-12)
    lo=np.zeros_like(x);hi=2*x+1.0
    for _ in range(55):
        mid=(lo+hi)/2;v=mid**3/(1+mid)**2
        mask=v<x;lo=np.where(mask,mid,lo);hi=np.where(mask,hi,mid)
    return ((lo+hi)/2)*m1

def run_one(D,n_mc,seed):
    rng=np.random.default_rng(seed);rows=[]
    for r in D.itertuples(index=False):
        d=r._asdict()
        def draw(k): return d[k]+d[k+'_error']*rng.standard_normal(n_mc)
        A,B,F,G=(draw(k) for k in ['a_thiele_innes','b_thiele_innes','f_thiele_innes','g_thiele_innes'])
        C,H=draw('c_thiele_innes'),draw('h_thiele_innes');plx=draw('parallax')
        m1=np.clip(d['m1']+0.5*(d['m1_upper']-d['m1_lower'])*rng.standard_normal(n_mc),0.08,None)
        a0,inc,_,_=campbell(A,B,F,G);sini=np.sin(np.radians(inc));a1_sini=np.hypot(C,H)
        a1=a1_sini/np.clip(sini,1e-3,None);rho=(a0/plx)*sini/a1_sini
        P=d['period']/365.25;m2=solve_m2_vectorized(a1,P,m1)/MJ
        q=lambda x,p:float(np.nanpercentile(x,p))
        rlo,rhi=q(rho,2.5),q(rho,97.5);mlo,mhi=q(m2,2.5),q(m2,97.5)
        label=1 if (mlo>80 or rhi<0.9) else (0 if (mhi<80 and rlo>0.9) else -1)
        rows.append({'source_id':str(int(d['source_id'])),'rho':q(rho,50),'rho_lo':rlo,'rho_hi':rhi,
                     'm2_dyn':q(m2,50),'m2_lo':mlo,'m2_hi':mhi,'label':label,'n_mc':n_mc,'seed':seed})
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--n-mc',type=int,default=50000);ap.add_argument('--seeds',default='0,1,17')
    ap.add_argument('--out-dir',default='results/qa2/astrospectro_mc_precision');a=ap.parse_args()
    seeds=[int(x) for x in a.seeds.split(',') if x.strip()]
    c=pd.read_csv(ROOT/'realdata/dr3_candidates.csv');c=c[c.nss_solution_type.eq('AstroSpectroSB1')].drop_duplicates('source_id')
    ch=pd.read_csv(ROOT/'realdata/dr3_astrospectro_ch.csv');D=c.merge(ch,on='source_id')
    outdir=ROOT/a.out_dir;outdir.mkdir(parents=True,exist_ok=True)
    old=pd.read_csv(ROOT/'results/astrospectro_labels.csv',dtype={'source_id':str})
    runs=[];seed_labels=[]
    for seed in seeds:
        z=run_one(D,a.n_mc,seed);p=outdir/f'labels_{a.n_mc}_seed{seed}.csv';z.to_csv(p,index=False);runs.append(z)
        seed_labels.append(z[['source_id','label']].rename(columns={'label':f'seed_{seed}'}))
    merged=seed_labels[0]
    for z in seed_labels[1:]:merged=merged.merge(z,on='source_id',how='inner')
    lc=[x for x in merged.columns if x.startswith('seed_')]
    stable=int((merged[lc].nunique(axis=1)==1).sum());vary=merged[merged[lc].nunique(axis=1)>1]
    comparisons={}
    for z in runs:
        m=old.merge(z,on='source_id',suffixes=('_historical','_precision'))
        comparisons[str(int(z.seed.iloc[0]))]={'historical_400draw_agreement':float((m.label_historical==m.label_precision).mean()),
            'changed_objects':int((m.label_historical!=m.label_precision).sum()),
            'counts':{str(k):int(v) for k,v in z.label.value_counts().items()}}
    # Numerical solver cross-check against brentq on 1,000 independent random tuples.
    rng=np.random.default_rng(991);m1=rng.uniform(.08,2,1000);a1=10**rng.uniform(-2,.5,1000);P=10**rng.uniform(-1,1,1000)
    vec=solve_m2_vectorized(a1,P,m1);f=a1**3/P**2;scalar=[]
    for i in range(len(m1)):
        upper=2*f[i]+m1[i]
        scalar.append(brentq(lambda x:x**3/(m1[i]+x)**2-f[i],1e-14,upper))
    scalar=np.asarray(scalar);solver_rel=float(np.max(np.abs(vec-scalar)/np.maximum(scalar,1e-12)))
    report={'status':'SUPPLEMENTARY_HIGH_DRAW_MONTE_CARLO_AUDIT_NOT_PRIMARY_A3_RESULT','n_objects':len(D),'n_mc_per_seed':a.n_mc,'seeds':seeds,
      'counts_by_seed':{str(int(z.seed.iloc[0])):{str(k):int(v) for k,v in z.label.value_counts().items()} for z in runs},
      'agreement_across_precision_seeds':stable,'n_precision_seed_sensitive':int(len(vary)),
      'seed_sensitive_objects':vary.to_dict(orient='records'),'historical_400_draw_comparison':comparisons,
      'solver_validation':{'method':'vectorized monotone bisection vs scipy.brentq','n':1000,'max_relative_error':solver_rel},
      'limitations':['The error draws assume independence because the source export supplies marginal errors, not full covariance matrices.','This diagnostic uses all n_mc draws for both rho and m2; the historical A3 code computes m2 from only the first 150 draws.','The full-draw diagnostic is a sensitivity audit and must not silently overwrite the registered/historical A3 output.']}
    (outdir/'summary.json').write_text(json.dumps(report,indent=2))
    (outdir/'precision_seed_labels.csv').write_text(merged.to_csv(index=False))
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
