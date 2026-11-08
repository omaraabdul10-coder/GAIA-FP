#!/usr/bin/env python3
"""Download the pre-built GALAH DR3 per-spectrum RV ADQL chunks from VizieR TAP.

The script is resumable: already downloaded chunk CSVs are skipped after header
validation. It does not assign binary labels; it only retrieves measurements.
"""
from __future__ import annotations
import argparse, csv, io, time
from pathlib import Path
import pandas as pd
import requests

ROOT=Path(__file__).resolve().parents[2]
QUERY_DIR=ROOT/'results'/'qa2'/'partial_completion'/'galah_adql'
DEFAULT_RAW=ROOT/'realdata'/'galah_epoch_rv_chunks'
DEFAULT_COMBINED=ROOT/'realdata'/'galah_epoch_rv_crossmatch.csv'
TAP='https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync'
REQUIRED=['source_id','galah_id','rv_kms','rv_error_kms','rv_method_flag','hjd','mjd_local']

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--tap-url',default=TAP)
    ap.add_argument('--raw-dir',type=Path,default=DEFAULT_RAW)
    ap.add_argument('--combined',type=Path,default=DEFAULT_COMBINED)
    ap.add_argument('--start',type=int,default=1)
    ap.add_argument('--stop',type=int,default=None)
    ap.add_argument('--retries',type=int,default=4)
    ap.add_argument('--timeout',type=int,default=180)
    ap.add_argument('--force',action='store_true',help='redownload existing chunks')
    args=ap.parse_args()
    qfiles=sorted(QUERY_DIR.glob('galah_epoch_rv_chunk_*.adql'))
    if not qfiles: raise SystemExit(f'No ADQL chunks found in {QUERY_DIR}')
    if args.stop is None: args.stop=len(qfiles)
    if args.start<1 or args.stop>len(qfiles) or args.start>args.stop: raise SystemExit('Invalid chunk range')
    args.raw_dir.mkdir(parents=True,exist_ok=True)
    sess=requests.Session(); sess.headers.update({'User-Agent':'GAIA-FP reproducible research downloader/1.0'})
    saved=[]
    for idx,qpath in enumerate(qfiles,args.start):
        if idx>args.stop: break
        target=args.raw_dir/f'{qpath.stem}.csv'
        if target.exists() and not args.force:
            try:
                h=pd.read_csv(target,nrows=0).columns.tolist()
                if all(c in h for c in REQUIRED):
                    print(f'SKIP {idx}/{len(qfiles)} {target.name} (already valid)'); saved.append(target); continue
            except Exception: pass
        query=qpath.read_text(encoding='utf-8').strip()
        last=None
        for attempt in range(1,args.retries+1):
            try:
                r=sess.post(args.tap_url,data={'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'csv','QUERY':query},timeout=args.timeout)
                r.raise_for_status()
                content=r.text.lstrip('\ufeff\n\r ')
                if not content or content.startswith('<?xml') or 'QUERY_STATUS' in content[:1000] and not content.startswith('source_id'):
                    raise RuntimeError('TAP response is not a CSV result; first bytes: '+content[:400])
                frame=pd.read_csv(io.StringIO(content))
                missing=[c for c in REQUIRED if c not in frame.columns]
                if missing: raise RuntimeError(f'Missing expected output columns {missing}; got {frame.columns.tolist()}')
                tmp=target.with_suffix('.csv.tmp')
                frame.to_csv(tmp,index=False)
                tmp.replace(target)
                print(f'OK {idx}/{len(qfiles)} {target.name}: {len(frame)} rows')
                saved.append(target); last=None; break
            except Exception as e:
                last=e; print(f'RETRY {idx}/{len(qfiles)} attempt {attempt}: {e}')
                if attempt<args.retries: time.sleep(min(5*attempt,20))
        if last is not None: raise SystemExit(f'Chunk {idx} failed after {args.retries} attempts: {last}')
    if args.start==1 and args.stop==len(qfiles):
        frames=[pd.read_csv(p,dtype={'source_id':'string','galah_id':'string'}) for p in saved]
        combined=pd.concat(frames,ignore_index=True) if frames else pd.DataFrame(columns=REQUIRED)
        args.combined.parent.mkdir(parents=True,exist_ok=True)
        tmp=args.combined.with_suffix(args.combined.suffix+'.tmp'); combined.to_csv(tmp,index=False); tmp.replace(args.combined)
        print(f'COMBINED {len(combined)} rows from {len(saved)} chunks -> {args.combined}')
    else:
        print('Partial chunk range downloaded. Run again for the remaining chunks; combine after all chunks exist.')

if __name__=='__main__': main()
