#!/usr/bin/env python3
"""Re-run the registered 400-draw A3/H8 DR3 label computation across five seeds.

This deliberately calls the frozen astrospectro_check.main implementation in
isolated temporary output directories. It does not overwrite the historical
results/astrospectro_labels.csv or the frozen scores.
"""
from __future__ import annotations
import argparse,json,sys,tempfile,shutil
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
import astrospectro_check as A

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seeds',default='0,1,2,3,4');ap.add_argument('--n-mc',type=int,default=400)
    ap.add_argument('--out-dir',default='results/qa2/h8_seed_sweep');a=ap.parse_args()
    seeds=[int(x) for x in a.seeds.split(',') if x.strip()];outdir=ROOT/a.out_dir;outdir.mkdir(parents=True,exist_ok=True)
    base=ROOT/'results/astrospectro_labels.csv';historical=pd.read_csv(base,dtype={'source_id':str})
    frames=[];summary={}
    for seed in seeds:
        with tempfile.TemporaryDirectory(prefix='gaia_h8_') as td:
            tdp=Path(td)
            shutil.copy2(ROOT/'results/dr3_candidates_scored.csv',tdp/'dr3_candidates_scored.csv')
            result=A.main(real=str(ROOT/'realdata')+'/',out=str(tdp)+'/',n_mc=a.n_mc,seed=seed)
            cur=pd.read_csv(tdp/'astrospectro_labels.csv',dtype={'source_id':str})
        cur.to_csv(outdir/f'labels_seed{seed}.csv',index=False)
        m=historical.merge(cur,on='source_id',suffixes=('_historical','_seed'))
        summary[str(seed)]={'counts':{str(k):int(v) for k,v in cur.label.value_counts().items()},
             'agreement_with_historical_seed0':float((m.label_historical==m.label_seed).mean()),
             'changed_vs_historical':int((m.label_historical!=m.label_seed).sum()),
             'metrics':{'auc':result.get('auc',{}),'n_scored_labelled':result.get('n_scored_labelled')}}
        frames.append(cur[['source_id','label']].rename(columns={'label':f'seed_{seed}'}))
    combined=frames[0]
    for f in frames[1:]:combined=combined.merge(f,on='source_id',how='inner')
    labcols=[c for c in combined if c.startswith('seed_')]
    changed=combined[combined[labcols].nunique(axis=1)>1]
    report={'status':'REGISTERED_400_DRAW_SEED_SENSITIVITY_AUDIT','n_objects':int(len(combined)),'n_mc':a.n_mc,'seeds':seeds,
        'seed_results':summary,'stable_all_seeds':int(len(combined)-len(changed)),'seed_sensitive_count':int(len(changed)),
        'seed_sensitive_objects':changed.to_dict(orient='records'),
        'code_path_limitation':'Current astrospectro_check.py draws all n_mc values for rho but computes m2 from only the first 150 Monte Carlo draws. This audit reproduces that code exactly; see audit_astrospectro_mc_precision.py for an independent all-draw sensitivity analysis.',
        'historical_output_unchanged':True}
    (outdir/'summary.json').write_text(json.dumps(report,indent=2));combined.to_csv(outdir/'labels_by_seed.csv',index=False)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
