#!/usr/bin/env python3
"""Combine 10 x 1,000 synthetic-null bootstrap calibration chunks per statistic."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from scipy.stats import kstest
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'results/qa2/null_calibration_10k'

def wilson(k,n,z=1.96):
    p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d;h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [float(c-h),float(c+h)]

def summarise(stat):
    arrays=[]
    for i in range(10):
        pth=BASE/'chunks'/f'{stat}_chunk{i:02d}.npz'
        if not pth.exists(): raise SystemExit(f'missing chunk: {pth}')
        with np.load(pth) as z:
            p=z['p_values'];seed=int(z['seed']);nrep=int(z['n_rep']);nboot=int(z['n_boot'])
        if len(p)!=1000 or nrep!=1000 or nboot!=2000 or seed!=20261101+i:
            raise SystemExit(f'metadata mismatch in {pth}')
        arrays.append(p)
    P=np.concatenate(arrays)
    out={'statistic':stat,'n_rep':int(len(P)),'n_pos':39,'n_neg':26,'n_boot':2000,
         'chunk_seeds':list(range(20261101,20261111)),
         'data':'SYNTHETIC NULL ONLY; this evaluates bootstrap type-I behaviour, not model discrimination or Gaia outcomes.',
         'rejection':{},'ks_vs_uniform_p':float(kstest(P,'uniform').pvalue),
         'decile_counts':np.histogram(P,bins=np.linspace(0,1,11))[0].tolist(),
         'p_median':float(np.median(P)),'scientific_calibration_complete':False,
         'status':'10,000-REPLICATE SYNTHETIC NULL DIAGNOSTIC; not real Gaia validation'}
    if stat=='dauc': out['rho_between_null_scores']=0.7
    for a in (.05,.025):
        k=int(np.sum(P<=a));rate=k/len(P)
        out['rejection'][str(a)]={'count':k,'rate':rate,'wilson95':wilson(k,len(P)),
            'mc_se':float(np.sqrt(rate*(1-rate)/len(P)))}
    return P,out

if __name__=='__main__':
    auc,ra=summarise('auc');dauc,rd=summarise('dauc')
    np.savez_compressed(BASE/'null_p_values_10000.npz',auc=auc,dauc=dauc,
                        auc_seeds=np.arange(20261101,20261111),dauc_seeds=np.arange(20261101,20261111))
    (BASE/'auc_10000_summary.json').write_text(json.dumps(ra,indent=2))
    (BASE/'dauc_10000_summary.json').write_text(json.dumps(rd,indent=2))
    print(json.dumps({'auc':ra,'dauc':rd},indent=2))
