#!/usr/bin/env python3
"""Validate a Gaia Archive supplementary export before scoring. Does not score or impute."""
import argparse, json, hashlib
from pathlib import Path
import pandas as pd

REQUIRED = [
    'source_id', 'vbroad', 'vbroad_error', 'vbroad_nb_transits', 'grvs_mag',
    'period', 'eccentricity', 'a_thiele_innes', 'b_thiele_innes',
    'f_thiele_innes', 'g_thiele_innes', 'c_thiele_innes', 'h_thiele_innes',
    'corr_vec', 'm1', 'm1_lower', 'm1_upper'
]
NUMERIC = [c for c in REQUIRED if c != 'source_id' and c != 'corr_vec']

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('csv', type=Path)
    ap.add_argument('--expected-rows', type=int, default=22127)
    ap.add_argument('--id-column', default='source_id')
    a=ap.parse_args()
    df=pd.read_csv(a.csv, dtype={a.id_column:'string'})
    missing=[c for c in REQUIRED if c not in df.columns]
    if missing: raise SystemExit('FAIL missing columns: '+', '.join(missing))
    ids=df[a.id_column].str.strip()
    if ids.isna().any() or (ids=='').any(): raise SystemExit('FAIL null/blank source_id')
    if ids.duplicated().any(): raise SystemExit(f'FAIL duplicate IDs: {int(ids.duplicated().sum())}')
    if len(df)!=a.expected_rows: raise SystemExit(f'FAIL row count {len(df)} != expected {a.expected_rows}')
    for c in NUMERIC:
        df[c]=pd.to_numeric(df[c],errors='coerce')
    report={
      'status':'PASS_SCHEMA_AND_IDENTITY_ONLY',
      'rows':int(len(df)),
      'unique_source_ids':int(ids.nunique()),
      'missing_by_column':{c:int(df[c].isna().sum()) for c in NUMERIC},
      'vbroad_nonnull':int(df.vbroad.notna().sum()),
      'vbroad_nb_transits_nonnull':int(df.vbroad_nb_transits.notna().sum()),
      'm1_nonnull':int(df.m1.notna().sum()),
      'sha256':sha256(a.csv),
      'warning':'This validator does not establish astrophysical correctness, completeness of the uploaded ID list, or model performance.'
    }
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
