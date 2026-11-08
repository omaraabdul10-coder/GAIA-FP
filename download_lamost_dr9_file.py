#!/usr/bin/env python3
"""Download a LAMOST DR9 v2.0 catalogue file from its official direct URL.

The LAMOST catalogue page renders the direct CSV/FITS links. Copy the exact
link for the DR9 v2.0 LRS AFGK Stellar Parameter Catalog and pass it here;
this script intentionally does not guess a release-specific filename/URL.
"""
import argparse,hashlib,json
from pathlib import Path
import requests

def download(url,out,expected_sha256=None,timeout=60):
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True);tmp=out.with_suffix(out.suffix+'.part')
    h=hashlib.sha256();n=0
    with requests.get(url,stream=True,timeout=timeout,headers={'User-Agent':'GAIA-FP reproducible research/1.0'}) as r:
        r.raise_for_status()
        ctype=r.headers.get('Content-Type','')
        with tmp.open('wb') as f:
            for chunk in r.iter_content(1024*1024):
                if not chunk: continue
                f.write(chunk);h.update(chunk);n+=len(chunk)
    digest=h.hexdigest()
    if n==0: tmp.unlink(missing_ok=True);raise RuntimeError('Downloaded file is empty')
    if expected_sha256 and digest.lower()!=expected_sha256.lower():
        tmp.unlink(missing_ok=True);raise RuntimeError(f'SHA256 mismatch: expected {expected_sha256}, got {digest}')
    # Refuse obvious HTML/login/error pages masquerading as a catalogue.
    with tmp.open('rb') as f: head=f.read(512).lstrip()
    if head.lower().startswith((b'<!doctype html',b'<html',b'<?xml')):
        tmp.unlink(missing_ok=True);raise RuntimeError('Response appears to be HTML/XML, not a catalogue file')
    tmp.replace(out)
    return {'url':url,'output':str(out.resolve()),'bytes':n,'sha256':digest,'content_type':ctype}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',required=True);p.add_argument('--out',required=True);p.add_argument('--sha256');p.add_argument('--timeout',type=int,default=60);a=p.parse_args()
    result=download(a.url,a.out,a.sha256,a.timeout);Path(a.out+'.provenance.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
