#!/usr/bin/env python3
"""Build a deterministic Gaia DR3 source_id <-> APOGEE_ID crosswalk.

Input is official SDSS DR17 allStar/allStarLite, which includes
GAIAEDR3_SOURCE_ID and APOGEE_ID. Ambiguous Gaia IDs and APOGEE IDs are
written separately and excluded from the one-to-one mapping by default.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from process_apogee_allvisit import read_table, _casefold_columns


def build(summary_path, candidate_path, outdir):
    s=_casefold_columns(read_table(summary_path))
    c=_casefold_columns(read_table(candidate_path))
    if 'GAIAEDR3_SOURCE_ID' not in s or 'APOGEE_ID' not in s:
        raise ValueError('Official allStar/allStarLite input must include GAIAEDR3_SOURCE_ID and APOGEE_ID.')
    if 'SOURCE_ID' not in c: raise ValueError('Candidate table must contain source_id.')
    keep=['GAIAEDR3_SOURCE_ID','APOGEE_ID']
    has_field='FIELD' in s.columns
    if has_field: keep.append('FIELD')
    s=s[keep].rename(columns={'GAIAEDR3_SOURCE_ID':'source_id'})
    c=c[['SOURCE_ID']].rename(columns={'SOURCE_ID':'source_id'})
    s['source_id']=s.source_id.astype('string').str.strip();s['APOGEE_ID']=s.APOGEE_ID.astype('string').str.strip()
    if has_field: s['FIELD']=s.FIELD.astype('string').str.strip()
    c['source_id']=c.source_id.astype('string').str.strip()
    s=s.dropna(subset=['source_id','APOGEE_ID']).drop_duplicates()
    s=s[s.source_id.isin(set(c.source_id.dropna()))]
    # A Gaia source may legitimately have APOGEE reductions in multiple fields.
    # The unique visit join key is (APOGEE_ID, FIELD), not source_id alone.
    key=['APOGEE_ID','FIELD'] if has_field else ['APOGEE_ID']
    if has_field:
        amb_keys=s.duplicated(key,keep=False)
    else:
        # Without FIELD, repeated Gaia IDs cannot be disambiguated safely.
        amb_keys=s.duplicated(['source_id'],keep=False) | s.duplicated(['APOGEE_ID'],keep=False)
    ambiguous=s[amb_keys].copy()
    clean=s[~amb_keys].copy()
    amb_source=set(ambiguous.source_id)
    amb_apogee=set(ambiguous.APOGEE_ID)
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    clean.sort_values(['source_id']+key).to_csv(out/'apogee_gaia_dr3_mapping.csv',index=False)
    ambiguous.sort_values(['source_id']+key).to_csv(out/'apogee_mapping_ambiguous.csv',index=False)
    missing=sorted(set(c.source_id.dropna())-set(clean.source_id))
    pd.DataFrame({'source_id':missing}).to_csv(out/'apogee_mapping_not_found_or_ambiguous.csv',index=False)
    report={'candidate_unique_source_ids':int(c.source_id.nunique()),'allstar_rows':len(s),
      'one_to_one_mapping_rows':len(clean),'matched_candidate_sources':int(clean.source_id.nunique()),
      'ambiguous_rows':len(ambiguous),'ambiguous_source_ids':len(amb_source),'ambiguous_apogee_ids':len(amb_apogee),
      'mapping_key':key,'multiple_fields_per_gaia_source_allowed':bool(has_field),
      'candidate_sources_unmapped_or_ambiguous':len(missing),
      'source_field':'GAIAEDR3_SOURCE_ID','join':'Exact identifier only; no sky-coordinate fallback.'}
    (out/'apogee_mapping_report.json').write_text(__import__('json').dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--allstar',required=True);ap.add_argument('--candidates',default='realdata/dr3_candidates.csv');ap.add_argument('--outdir',default='results/final_completion/apogee');a=ap.parse_args()
    print(build(a.allstar,a.candidates,a.outdir))
