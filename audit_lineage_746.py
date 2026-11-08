#!/usr/bin/env python3
"""Rebuild exact source-ID set-membership lineage for the archived 746 rows."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd

def main(root,outdir):
    root=Path(root).resolve();out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    paths={'raw_nss':'realdata/dr3_nss_two_body_orbit_raw.csv','candidate_2119':'realdata/dr3_candidates.csv',
      'ch_95':'realdata/dr3_astrospectro_ch.csv','characterization_95':'results/qa2/partial_completion/astrospectro_95_object_characterization.csv',
      'mechanism_scored':'results/mechanism_scored.csv'}
    sets={};counts={}
    for name,rel in paths.items():
        d=pd.read_csv(root/rel,dtype={'source_id':'string'})
        ids=set(d.source_id.dropna().astype(str));sets[name]=ids
        counts[name]={'rows':len(d),'unique_source_ids':len(ids)}
    mechanism_only=sorted(sets['mechanism_scored']-sets['raw_nss'])
    raw_only=sorted(sets['raw_nss']-sets['mechanism_scored'])
    names=list(sets)
    union=sorted(set.union(*sets.values()))
    rows=[]
    for sid in union:
        r={'source_id':sid}
        for n in names:r[f'in_{n}']=sid in sets[n]
        rows.append(r)
    pd.DataFrame(rows).to_csv(out/'DATA_LINEAGE_ALL_SET_MEMBERSHIP.csv',index=False)
    tab=pd.DataFrame([{'source_id':sid,**{f'in_{n}':sid in sets[n] for n in names}} for sid in mechanism_only])
    tab.to_csv(out/'DATA_LINEAGE_746_EXACT_MEMBERSHIP.csv',index=False)
    # Keep 746 mechanism-only IDs separate from the distinct 2,672-1,926 numerical difference.
    result={'counts':counts,'raw_nss_mechanism_intersection':len(sets['raw_nss']&sets['mechanism_scored']),
      'mechanism_only_vs_raw_nss':len(mechanism_only),'raw_only_vs_mechanism':len(raw_only),
      'mechanism_only_are_candidate_ids':int(sum(s in sets['candidate_2119'] for s in mechanism_only)),
      'mechanism_only_are_ch95_ids':int(sum(s in sets['ch_95'] for s in mechanism_only)),
      'mechanism_only_are_characterization95_ids':int(sum(s in sets['characterization_95'] for s in mechanism_only)),
      'old_h10_count_difference':{'earlier_reported_rows':2672,'labelled_rows':1926,'difference':746,
        'same_identity_as_mechanism_only_746':'NOT_ESTABLISHED; original historical input rows/IDs are missing'},
      'conclusion':'The 746 IDs in this report are precisely mechanism_scored minus raw DR3 NSS. Their source-population/query vintage cannot be identified from the archived inputs. The old H10 2672-1926 difference is a distinct unverified discrepancy despite sharing the same count.'}
    (out/'DATA_LINEAGE_746_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--outdir',default='results/final_completion');a=p.parse_args();main(a.root,a.outdir)
