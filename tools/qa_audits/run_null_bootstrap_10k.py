#!/usr/bin/env python3
"""10,000-replicate synthetic-null calibration of registered stratified percentile-bootstrap p.
Each 1,000-replicate chunk uses an independent deterministic SeedSequence child.
No Gaia data, labels, or trained model enters this diagnostic.
"""
from __future__ import annotations
import argparse,json,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from scipy.stats import rankdata, kstest

def auc_rows(S,y):
    R=rankdata(S,axis=1); n1=int(y.sum()); n0=len(y)-n1
    return (R[:,y==1].sum(axis=1)-n1*(n1+1)/2)/(n1*n0)

def run_chunk(statistic, n_rep, n_boot, seed, n_pos=39, n_neg=26, rho=.7):
    rng=np.random.default_rng(seed); y=np.r_[np.ones(n_pos,int),np.zeros(n_neg,int)]; n=len(y)
    pos=np.arange(n_pos); neg=np.arange(n_pos,n); P=np.empty(n_rep)
    yb=y.copy(); null=.5 if statistic=='auc' else 0.0
    for r in range(n_rep):
        s1=rng.normal(size=n)
        # Match sensitivity.null_calibration RNG consumption exactly: draw s2 even for AUC-only.
        s2=rho*s1+np.sqrt(1-rho**2)*rng.normal(size=n)
        idx=np.concatenate([rng.choice(pos,(n_boot,n_pos),True),rng.choice(neg,(n_boot,n_neg),True)],axis=1)
        a1=auc_rows(s1[idx],yb)
        st=a1 if statistic=='auc' else a1-auc_rows(s2[idx],yb)
        P[r]=(np.sum(st<=null)+1)/(n_boot+1)
    return P

def wilson(k,n,z=1.96):
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [float(c-h),float(c+h)]

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--statistic',choices=['auc','dauc'],required=True);ap.add_argument('--chunk',type=int,required=True);ap.add_argument('--n-rep',type=int,default=1000);ap.add_argument('--n-boot',type=int,default=2000);ap.add_argument('--base-seed',type=int,default=20261101);a=ap.parse_args()
    seed=a.base_seed+a.chunk
    t=time.time(); p=run_chunk(a.statistic,a.n_rep,a.n_boot,seed)
    d=ROOT/'results/qa2/null_calibration_10k/chunks';d.mkdir(parents=True,exist_ok=True)
    out=d/f'{a.statistic}_chunk{a.chunk:02d}.npz';np.savez_compressed(out,p_values=p,seed=seed,n_rep=a.n_rep,n_boot=a.n_boot)
    print(json.dumps({'statistic':a.statistic,'chunk':a.chunk,'n_rep':a.n_rep,'n_boot':a.n_boot,'seed':seed,'rate_0.05':float(np.mean(p<=.05)),'rate_0.025':float(np.mean(p<=.025)),'elapsed':round(time.time()-t,2),'file':str(out)}))
