#!/usr/bin/env python3
"""Audit H11 DR3 matched-control construction without changing its frozen output.

The registered seed-11 matching output is retained. Additional random-order seeds
are sensitivity diagnostics only; none replaces the seed-11 control set.
"""
from __future__ import annotations
import argparse, json, hashlib, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import h11_control as H
import dr4_pipeline as D


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--n-seeds',type=int,default=12)
    ap.add_argument('--seed-start',type=int,default=1)
    ap.add_argument('--out',default='results/qa2/h11_matching_sensitivity.json')
    a=ap.parse_args()
    raw=pd.read_csv(ROOT/'realdata/dr3_nss_two_body_orbit_raw.csv',dtype={'source_id':str})
    cand=pd.read_csv(ROOT/'results/dr3_candidates_scored.csv',dtype={'source_id':str})
    sealed=set(pd.read_csv(ROOT/'realdata/excluded_sealed_ids.csv',dtype={'source_id':str}).source_id.astype(str).str.strip())
    cand_ids=set(cand.source_id.astype(str).str.strip())
    raw=raw[~raw.source_id.astype(str).str.strip().isin(sealed|cand_ids)]
    field=pd.read_csv(ROOT/'realdata/dr3_field.csv')
    ctrl=H.pool(raw,field)
    if len(ctrl)<len(cand): raise SystemExit('control pool smaller than candidate list; stop')
    # Verify the archived/frozen registered seed-11 assignment exactly.
    ref=pd.read_csv(ROOT/'results/h11_controls.csv',dtype={'source_id':str,'matched_candidate':str})
    idx11=H.match(cand,ctrl,seed=11)
    rec=ctrl.iloc[idx11].reset_index(drop=True)
    exact=(rec.source_id.astype(str).to_numpy()==ref.source_id.astype(str).to_numpy()).all()
    if not exact: raise SystemExit('seed-11 reconstruction differs from archived controls; do not overwrite')
    if ref.source_id.duplicated().any(): raise SystemExit('duplicate control source_id')
    if set(ref.source_id.astype(str)) & cand_ids: raise SystemExit('candidate/control overlap')
    if set(ref.source_id.astype(str)) & sealed: raise SystemExit('sealed/control overlap')
    # Compute paired diagnostics for each seed. Coordinates use the registered metric.
    def coords(T): return np.c_[T.G.to_numpy(float),np.log10(T.P.to_numpy(float)),T.significance.to_numpy(float)]
    C=coords(ctrl);Q=coords(cand);scale=C.std(axis=0,ddof=1);scale[scale==0]=1.0
    C=C/scale;Q=Q/scale
    seed_summaries=[]; per_seed=[]
    for seed in [a.seed_start+i for i in range(a.n_seeds)]:
        ix=H.match(cand,ctrl,seed=seed)
        if (ix<0).any() or len(np.unique(ix))!=len(ix): raise SystemExit(f'incomplete/duplicate assignment at seed {seed}')
        B=ctrl.iloc[ix].reset_index(drop=True)
        d=np.sqrt(((Q-C[ix])**2).sum(axis=1))
        entry={'seed':seed,'mean_pair_distance':float(d.mean()),'median_pair_distance':float(np.median(d)),
               'p95_pair_distance':float(np.quantile(d,.95)),'max_pair_distance':float(d.max())}
        for col,transform in [('G',lambda x:x),('P',np.log10),('significance',lambda x:x)]:
            x=transform(cand[col].to_numpy(float));y=transform(B[col].to_numpy(float))
            pooled=np.sqrt((x.var(ddof=1)+y.var(ddof=1))/2)
            entry[f'smd_{col}']=float((x.mean()-y.mean())/pooled) if pooled else 0.0
            entry[f'ks_{col}']=float(ks_2samp(x,y).statistic)
        per_seed.append(entry)
    cols=['G','P','significance'];
    # Primary seed 11 is intentionally included in the sensitivity panel.
    for seed in [11]:
        ix=H.match(cand,ctrl,seed=seed);B=ctrl.iloc[ix].reset_index(drop=True)
        d=np.sqrt(((Q-C[ix])**2).sum(axis=1))
        ent={'seed':11,'mean_pair_distance':float(d.mean()),'median_pair_distance':float(np.median(d)),
             'p95_pair_distance':float(np.quantile(d,.95)),'max_pair_distance':float(d.max())}
        for col,transform in [('G',lambda x:x),('P',np.log10),('significance',lambda x:x)]:
            x=transform(cand[col].to_numpy(float));y=transform(B[col].to_numpy(float));pooled=np.sqrt((x.var(ddof=1)+y.var(ddof=1))/2)
            ent[f'smd_{col}']=float((x.mean()-y.mean())/pooled) if pooled else 0.0
            ent[f'ks_{col}']=float(ks_2samp(x,y).statistic)
        if not any(x['seed']==11 for x in per_seed): per_seed.append(ent)
    out={'status':'AUDIT_ONLY_NO_FROZEN_OUTPUT_CHANGED','registered_seed':11,'seed11_reproduced_exactly':bool(exact),
         'raw_rows':int(len(pd.read_csv(ROOT/'realdata/dr3_nss_two_body_orbit_raw.csv'))),
         'candidate_n':int(len(cand)),'sealed_ids_n':int(len(sealed)),'control_pool_n':int(len(ctrl)),
         'matched_n':int(len(ref)),'unique_controls_n':int(ref.source_id.nunique()),
         'candidate_control_overlap':0,'sealed_control_overlap':0,
         'control_mass_proxy_range_MJ':[float(ctrl.mfit.min()),float(ctrl.mfit.max())],
         'random_order_seed_sweep':per_seed,
         'interpretation':'A small SMD across G, log10(P), and significance supports observed-covariate balance. The 80–300 MJ pool is an approximate first-order mass proxy, not a verified dynamical label. Matching is descriptive preparation for H11 O1 stability; it does not establish DR4 outcomes.'}
    outp=ROOT/a.out;outp.parent.mkdir(parents=True,exist_ok=True);outp.write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
