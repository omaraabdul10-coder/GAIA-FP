#!/usr/bin/env python3
"""Extract true APOGEE DR17 visit-level RV measurements for GAIA-FP targets.

Canonical science columns are JD (the exact visit mid-time), VHELIO (the
barycentric-corrected visit RV), and VRELERR (the corresponding uncertainty).
Integer-day MJD is retained for reference but is NEVER treated as exact cadence.
The Gaia DR3 source_id/APOGEE_ID crosswalk must come from the official APOGEE
allStar/allStarLite summary product; no coordinate-derived IDs are synthesized.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import chi2


def read_table(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() in {'.fits', '.fit', '.fts'} or p.name.lower().endswith(('.fits.gz','.fit.gz')):
        try:
            from astropy.table import Table
        except ImportError as exc:
            raise RuntimeError('FITS input requires astropy; export the official table as CSV or install astropy.') from exc
        return Table.read(p).to_pandas()
    return pd.read_csv(p, dtype='string')


def _casefold_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={c: str(c).strip().upper() for c in df.columns})


def process(allvisit_path, mapping_path, outdir, *, require_snr10=False, max_verr=None):
    v = _casefold_columns(read_table(allvisit_path))
    m = _casefold_columns(read_table(mapping_path))
    # Canonicalize Gaia / APOGEE mapping fields.
    mapping_aliases = {'SOURCE_ID': ['SOURCE_ID','GAIAEDR3_SOURCE_ID','GAIADR3_SOURCE_ID'],
                       'APOGEE_ID': ['APOGEE_ID']}
    for target, choices in mapping_aliases.items():
        if target not in m:
            got = next((x for x in choices if x in m), None)
            if got: m[target] = m[got]
    if 'SOURCE_ID' not in m or 'APOGEE_ID' not in m:
        raise ValueError('Mapping must contain Gaia DR3 source_id (or GAIAEDR3_SOURCE_ID) and APOGEE_ID.')
    # Visit table uses APOGEE_ID, JD, VHELIO, VRELERR, STARFLAG. RV_FLAG is optional.
    reqv = {'APOGEE_ID','JD','VHELIO','VRELERR','STARFLAG'}
    if not reqv <= set(v):
        missing = sorted(reqv-set(v))
        extra = ' `MJD` is integer-day only and cannot substitute for `JD`.' if 'JD' in missing else ''
        raise ValueError(f'allVisit missing canonical columns: {missing}.{extra}')
    m = m.rename(columns={'SOURCE_ID':'source_id','APOGEE_ID':'APOGEE_ID'})
    v = v.rename(columns={'VRELERR':'VERR'})
    if 'MJD' not in v: v['MJD'] = np.nan
    if 'RV_FLAG' not in v: v['RV_FLAG'] = 0
    if 'FIELD' in v and 'FIELD' in m:
        join_cols=['APOGEE_ID','FIELD']
        m['FIELD']=m.FIELD.astype('string').str.strip()
        v['FIELD']=v.FIELD.astype('string').str.strip()
    else:
        join_cols=['APOGEE_ID']
    for c in ['source_id','APOGEE_ID']:
        m[c]=m[c].astype('string').str.strip()
    # Multiple APOGEE fields for one Gaia source are legitimate. Require
    # uniqueness only for the actual visit join key, then aggregate visits
    # across all mapped fields at the Gaia source_id level.
    if m[join_cols].duplicated().any():
        raise ValueError('APOGEE mapping key is not unique; do not silently choose one cross-match.')
    for c in ['JD','MJD','VHELIO','VERR','STARFLAG','RV_FLAG']:
        v[c]=pd.to_numeric(v[c],errors='coerce')
    if 'SNR' in v: v['SNR']=pd.to_numeric(v.SNR,errors='coerce')
    j=v.merge(m,on=join_cols,how='inner',validate='many_to_one')
    # SDSS DR17 explicitly recommends excluding STARFLAG bits 0,3,4,19,22.
    star_reject_mask=(1<<0)|(1<<3)|(1<<4)|(1<<19)|(1<<22)
    # RV_FLAG bit 10 is RV_REJECT; bit 11 is RV_SUSPECT.
    rv_reject_mask=(1<<10)
    j['reject_starflag']=((j.STARFLAG.fillna(0).astype('int64') & star_reject_mask)!=0)
    j['reject_rvflag']=((j.RV_FLAG.fillna(0).astype('int64') & rv_reject_mask)!=0)
    j['rv_suspect_starflag']=((j.STARFLAG.fillna(0).astype('int64') & (1<<20))!=0)
    j['multiple_suspect_starflag']=((j.STARFLAG.fillna(0).astype('int64') & (1<<21))!=0)
    j['rv_suspect_rvflag']=((j.RV_FLAG.fillna(0).astype('int64') & (1<<11))!=0)
    j['valid_numeric']=np.isfinite(j.JD)&np.isfinite(j.VHELIO)&np.isfinite(j.VERR)&(j.VERR>0)
    if require_snr10:
        if 'SNR' not in j: raise ValueError('--require-snr10 requested but allVisit has no SNR column.')
        j['snr_ok']=j.SNR>=10
    else: j['snr_ok']=True
    if max_verr is not None: j['verr_ok']=j.VERR<=float(max_verr)
    else: j['verr_ok']=True
    j['accepted_primary']=j.valid_numeric & ~j.reject_starflag & ~j.reject_rvflag & j.snr_ok & j.verr_ok
    # A separate strict-quality sensitivity excludes the three persistence warnings
    # SDSS recommends removing for the highest-quality visit-RV subset.
    persistence_mask=(1<<9)|(1<<12)|(1<<13)
    j['reject_persistence_strict']=((j.STARFLAG.fillna(0).astype('int64') & persistence_mask)!=0)
    j['accepted_strict_quality']=j.accepted_primary & ~j.reject_persistence_strict
    accepted=j[j.accepted_primary].copy()
    accepted_strict=j[j.accepted_strict_quality].copy()
    summaries=[]
    for sid,g in accepted.groupby('source_id',dropna=True):
        n=len(g); w=1/np.square(g.VERR.to_numpy(float)); y=g.VHELIO.to_numpy(float)
        mu=float(np.sum(w*y)/np.sum(w)); q=float(np.sum(w*np.square(y-mu)))
        summaries.append({'source_id':str(sid),'APOGEE_IDs':';'.join(sorted(g.APOGEE_ID.astype(str).unique())),
          'FIELDS':';'.join(sorted(g.FIELD.astype(str).unique())) if 'FIELD' in g else '', 'n_epochs':n,
          'jd_min':float(g.JD.min()),'jd_max':float(g.JD.max()),'baseline_days':float(g.JD.max()-g.JD.min()),
          'mjd_min':float(g.MJD.min()) if g.MJD.notna().any() else np.nan,
          'mjd_max':float(g.MJD.max()) if g.MJD.notna().any() else np.nan,
          'weighted_mean_rv_kms':mu,'weighted_scatter_rv_kms':float(np.sqrt(np.sum(w*np.square(y-mu))/np.sum(w))),
          'chi2_constant_rv':q,'chi2_dof':n-1,'p_constant_rv':float(chi2.sf(q,n-1)) if n>1 else np.nan,
          'median_vrelerr_kms':float(g.VERR.median()),'n_rv_suspect':int((g.rv_suspect_starflag|g.rv_suspect_rvflag).sum()),
          'n_multiple_suspect':int(g.multiple_suspect_starflag.sum())})
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    j.to_csv(out/'apogee_allvisit_matched_with_flags.csv',index=False)
    accepted.to_csv(out/'apogee_allvisit_accepted.csv',index=False)
    accepted_strict.to_csv(out/'apogee_allvisit_high_quality.csv',index=False)
    pd.DataFrame(summaries).to_csv(out/'apogee_allvisit_source_summary.csv',index=False)
    summary={'allvisit_rows':len(v),'matched_rows':len(j),'accepted_rows':len(accepted),
      'matched_sources':int(j.source_id.nunique()),'sources_ge3_epochs':int(sum(x['n_epochs']>=3 for x in summaries)),
      'accepted_primary_rows':len(accepted),'accepted_strict_quality_rows':len(accepted_strict),
      'strict_additional_starflag_persistence_bits_excluded':[9,12,13],
      'timestamp_used':'JD (JD-MID from allVisit; float, days)','uncertainty_used':'VRELERR (km/s)',
      'integer_mjd_used_for_cadence':False,'starflag_reject_mask':star_reject_mask,'rv_flag_reject_mask':rv_reject_mask,
      'n_starflag_rv_suspect':int(j.rv_suspect_starflag.sum()),'n_starflag_multiple_suspect':int(j.multiple_suspect_starflag.sum()),
      'mapping_key':join_cols,
      'note':'APOGEE DR17 documentation defines JD as the visit time and VRELERR as the visit-RV uncertainty; MJD is integer-day only. Suspect/multiple flags are retained for review; RV variability is not compact-object confirmation.'}
    (out/'apogee_allvisit_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--allvisit',required=True);ap.add_argument('--mapping',required=True);ap.add_argument('--outdir',default='results/final_completion/apogee');ap.add_argument('--require-snr10',action='store_true');ap.add_argument('--max-verr',type=float,default=None);a=ap.parse_args()
    print(json.dumps(process(a.allvisit,a.mapping,a.outdir,require_snr10=a.require_snr10,max_verr=a.max_verr),indent=2))
