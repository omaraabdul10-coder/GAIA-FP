#!/usr/bin/env python3
"""Join LAMOST DR9 v2.0 LRS A/F/G/K per-spectrum RVs to GAIA-FP targets.

The exact-time path joins the official Multiple Epoch Catalog's aligned
obsid_list and midmjm_list to the per-spectrum AFGK catalogue on obsid.
`midmjm` is the Modified-Julian-minute timestamp at the middle of the
multiple exposures in one night; conversion to MJD days is midmjm / 1440.
The Gaia DR3 gaia_source_id is the exact identifier; no coordinate fallback.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import chi2

ALIASES={
 'gaia_source_id':['gaia_source_id','Gaia_source_id'],
 'obsid':['obsid','ObsID','obs_id'], 'mjd':['mjd','MJD'],
 'rv':['rv','RV'], 'rv_err':['rv_err','RV_err','rv_error'],
 'snrg':['snrg','SNR_g','snr_g'], 'fibermask':['fibermask','fiber_mask'],
 'class':['class','class1','spec_class'], 'subclass':['subclass','sub_class'],
 'fibertype':['fibertype','fiber_type']}

def rename_aliases(df):
    ren={}
    low={str(c).strip().lower():c for c in df.columns}
    for target,opts in ALIASES.items():
        hit=next((low[x.lower()] for x in opts if x.lower() in low),None)
        if hit is not None and hit!=target:ren[hit]=target
    return df.rename(columns=ren)

def read_lamost_table(path):
    p=Path(path)
    if p.suffix.lower() in {'.fits','.fit','.fts'} or p.name.lower().endswith(('.fits.gz','.fit.gz')):
        try: from astropy.table import Table
        except ImportError as exc: raise RuntimeError('FITS input requires astropy; alternatively export catalogue as CSV.') from exc
        return Table.read(p).to_pandas()
    return pd.read_csv(p,dtype='string')

def _split_list(value):
    if value is None or pd.isna(value): return []
    s=str(value).strip().strip('[]')
    if not s: return []
    # Multi-epoch catalogue stores aligned list fields separated by hyphens.
    return [x.strip() for x in re.split(r'[-,;|\s]+',s) if x.strip()]

def load_exact_obs_times(path):
    me=read_lamost_table(path)
    # Case-insensitive column map for the official multi-epoch fields.
    low={str(c).strip().lower():c for c in me.columns}
    if not {'obsid_list','midmjm_list'}<=set(low):
        raise ValueError('LAMOST Multiple Epoch Catalog must contain obsid_list and midmjm_list.')
    rows=[]; bad=[]
    for _,r in me.iterrows():
        obs=_split_list(r[low['obsid_list']]); times=_split_list(r[low['midmjm_list']])
        expected=r[low['obs_number']] if 'obs_number' in low else None
        if len(obs)!=len(times) or (expected is not None and not pd.isna(expected) and str(expected).strip().isdigit() and int(float(expected))!=len(obs)):
            bad.append({'obsid_list':str(r[low['obsid_list']]),'midmjm_list':str(r[low['midmjm_list']]),'obsid_n':len(obs),'time_n':len(times),'obs_number':expected})
            continue
        for oid,t in zip(obs,times):
            try: mjm=float(t)
            except Exception: continue
            rows.append({'obsid':str(oid),'midmjm':mjm,'mjd_exact':mjm/1440.0})
    times=pd.DataFrame(rows)
    if times.empty: raise ValueError('No aligned numeric obsid/midmjm pairs were recovered from the Multiple Epoch Catalog.')
    conflict=times.groupby('obsid').mjd_exact.agg(['min','max'])
    conflicting=set(conflict.index[(conflict['max']-conflict['min'])>1e-8])
    if conflicting:
        bad.extend([{'obsid':x,'reason':'conflicting_midmjm'} for x in sorted(conflicting)])
        times=times[~times.obsid.isin(conflicting)]
    times=times.drop_duplicates('obsid')
    return times,pd.DataFrame(bad)

def process(input_path,candidates_path,outdir,multi_epoch_path=None):
    src=rename_aliases(read_lamost_table(input_path))
    required={'gaia_source_id','obsid','rv','rv_err'}
    missing=sorted(required-set(src.columns))
    if missing:raise ValueError(f'LAMOST AFGK input missing required columns: {missing}')
    cand=pd.read_csv(candidates_path,dtype={'source_id':'string'})
    if 'source_id' not in cand:raise ValueError('Candidate table requires Gaia DR3 source_id.')
    cross=cand[['source_id']].dropna().drop_duplicates();cross.source_id=cross.source_id.astype('string').str.strip()
    src.gaia_source_id=src.gaia_source_id.astype('string').str.strip();src.obsid=src.obsid.astype('string').str.strip()
    for c in ['rv','rv_err','mjd']:
        if c in src:src[c]=pd.to_numeric(src[c],errors='coerce')
    if 'snrg' in src:src['snrg']=pd.to_numeric(src.snrg,errors='coerce')
    if 'fibermask' in src:src['fibermask_num']=pd.to_numeric(src.fibermask,errors='coerce')
    if multi_epoch_path:
        tmap,bad=load_exact_obs_times(multi_epoch_path)
        src=src.merge(tmap,on='obsid',how='left',validate='many_to_one')
        src['time_source']=np.where(src.mjd_exact.notna(),'LAMOST_DR9_multiple_epoch_midmjm','missing_multi_epoch_timestamp')
    else:
        bad=pd.DataFrame()
        if 'mjd' not in src:raise ValueError('No --multi-epoch table supplied and per-spectrum catalogue has no MJD.')
        src['mjd_exact']=src.mjd
        src['time_source']='LAMOST_AFGK_per_spectrum_mjd'
    joined=src.merge(cross,left_on='gaia_source_id',right_on='source_id',how='inner',validate='many_to_one')
    joined=joined.rename(columns={'source_id':'gaia_dr3_source_id'})
    joined['valid_numeric_rv']=np.isfinite(pd.to_numeric(joined.rv,errors='coerce'))&np.isfinite(pd.to_numeric(joined.rv_err,errors='coerce'))&(pd.to_numeric(joined.rv_err,errors='coerce')>0)&np.isfinite(pd.to_numeric(joined.mjd_exact,errors='coerce'))
    joined['science_object_fiber']=joined.fibertype.astype('string').str.strip().str.lower().eq('obj') if 'fibertype' in joined else True
    joined['accepted_for_constant_rv_test']=joined.valid_numeric_rv&joined.science_object_fiber
    accepted=joined[joined.accepted_for_constant_rv_test].copy()
    # One row per physical spectrum and target; conflicting repeats are not silently averaged.
    accepted=accepted.sort_values('rv_err').drop_duplicates(['gaia_dr3_source_id','obsid'])
    summaries=[]
    for sid,g in accepted.groupby('gaia_dr3_source_id'):
        n=len(g);w=1/np.square(g.rv_err.to_numpy(float));y=g.rv.to_numpy(float);mu=float(np.sum(w*y)/np.sum(w));q=float(np.sum(w*np.square(y-mu)));dof=n-1
        summaries.append({'source_id':str(sid),'n_epochs':n,'mjd_min':float(g.mjd_exact.min()),'mjd_max':float(g.mjd_exact.max()),
          'baseline_days':float(g.mjd_exact.max()-g.mjd_exact.min()),'weighted_mean_rv_kms':mu,
          'weighted_rv_scatter_kms':float(np.sqrt(np.sum(w*np.square(y-mu))/np.sum(w))),'chi2_constant_rv':q,
          'chi2_dof':dof,'p_constant_rv':float(chi2.sf(q,dof)) if dof>0 else np.nan,
          'median_rv_error_kms':float(g.rv_err.median()),'median_snrg':float(g.snrg.median()) if 'snrg' in g else np.nan,
          'n_nonzero_fibermask':int((g.fibermask_num.fillna(0)!=0).sum()) if 'fibermask_num' in g else np.nan,
          'timestamp_source':','.join(sorted(g.time_source.dropna().astype(str).unique()))})
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    joined.to_csv(out/'lamost_dr9_lrs_epoch_matches_all.csv',index=False);accepted.to_csv(out/'lamost_dr9_lrs_epoch_matches_valid_rv.csv',index=False)
    pd.DataFrame(summaries).to_csv(out/'lamost_dr9_lrs_source_summary.csv',index=False)
    if len(bad):bad.to_csv(out/'lamost_multi_epoch_alignment_rejects.csv',index=False)
    exact_rows=int(joined.mjd_exact.notna().sum()) if 'mjd_exact' in joined else 0
    summary={'input_rows':len(src),'matched_epoch_rows':len(joined),'valid_numeric_epoch_rows':len(accepted),
      'matched_gaia_dr3_sources':int(joined.gaia_dr3_source_id.nunique()),'sources_with_ge3_valid_epochs':int(sum(x['n_epochs']>=3 for x in summaries)),
      'exact_multi_epoch_join_used':bool(multi_epoch_path),'exact_midmjm_rows_matched':exact_rows,
      'method':'Gaia DR3 source_id exact join; obsid join to LAMOST DR9 Multiple Epoch Catalog; midmjm minutes / 1440 = MJD days.' if multi_epoch_path else 'Gaia DR3 source_id exact join; per-spectrum MJD used, exact sub-day precision not guaranteed.',
      'quality_note':'Finite RV, finite epoch, positive finite rv_err, fibertype=Obj required when supplied. fibermask/SNR are retained as audit fields; release-specific quality masks should be added before inferential use.',
      'interpretation_note':'Small p_constant_rv indicates disagreement with constant RV under formal errors. It is not proof of a compact companion.'}
    (out/'lamost_epoch_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--multi-epoch',default=None);ap.add_argument('--candidates',default='realdata/dr3_candidates.csv');ap.add_argument('--outdir',default='results/final_completion/lamost_epoch_rv');a=ap.parse_args()
    print(json.dumps(process(a.input,a.candidates,a.outdir,a.multi_epoch),indent=2))
