#!/usr/bin/env python3
"""Cross-match the published El-Badry et al. (2024) 21-system RV sample.

The 2024 systems are published NS candidates with multi-epoch RV follow-up;
that paper explicitly notes ultra-massive WDs / tight WD+WD alternatives are
not fully excluded. We therefore call them external RV-followed dark-companion
references, not an unquestionable 21-object NS ground-truth set.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd

IDS=[
'2995961897685517312','6481502062263141504','5820382041374661888','1871419337958702720','5530442371304582912',
'5136025521527939072','4922744974687373440','1434445448240677376','3494029910469026432','1694708646628402048',
'4637171465304969216','5580526947012630912','1350295047363872512','2426116249713980416','6328149636482597888',
'1058875159778407808','1801110822095134848','2397135910639986304','1028887114002082432','465093354131112960',
'1007185297091149824']
SPECIAL={'5136025521527939072','1801110822095134848'}

def main(root,outdir):
    root=Path(root).resolve();out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    files={'raw_nss':'realdata/dr3_nss_two_body_orbit_raw.csv','candidates_2119':'realdata/dr3_candidates.csv',
      'mechanism_scored':'results/mechanism_scored.csv','characterization_95':'results/qa2/partial_completion/astrospectro_95_object_characterization.csv'}
    sets={}
    for key,rel in files.items():
        d=pd.read_csv(root/rel,dtype={'source_id':'string'});sets[key]=set(d.source_id.dropna().astype(str))
    corrected_path=root/'results/final_completion/mechanism_scored_S1_CORRECTED_c1.csv'
    scores=pd.read_csv(corrected_path,dtype={'source_id':'string'}) if corrected_path.exists() else pd.DataFrame()
    outrows=[]
    for sid in IDS:
        row={'source_id':sid,'in_published_2024_21_system_RV_followup_sample':True,
          'in_2026_MS_NS_reference_pair':sid in SPECIAL,'in_raw_gaia_nss':sid in sets['raw_nss'],
          'in_gaiafp_2119_candidate_parent':sid in sets['candidates_2119'],
          'in_gaiafp_mechanism_scored':sid in sets['mechanism_scored'],
          'in_gaiafp_95_physical_characterization':sid in sets['characterization_95'],
          '2024_reference_status':'published RV-followed NS candidate; WD alternatives not completely excluded'}
        if len(scores) and sid in set(scores.source_id):
            r=scores[scores.source_id==sid].iloc[0]
            row.update({'S1_corrected_c1':r.S1_corrected_c1,'B2':r.B2,'VB':r.VB,'label_H10':r.label})
        outrows.append(row)
    df=pd.DataFrame(outrows);df.to_csv(out/'EXTERNAL_NS_RV_REFERENCE_CROSSMATCH.csv',index=False)
    matched=df[df.in_gaiafp_mechanism_scored]
    special=df[df.in_2026_MS_NS_reference_pair]
    report={'external_reference':'El-Badry et al. 2024, DOI 10.33232/001c.121261; arXiv:2405.00089',
      'crossmatched_21_RV_followup_sources':len(df),'in_raw_gaia_nss':int(df.in_raw_gaia_nss.sum()),
      'in_gaiafp_candidate_parent':int(df.in_gaiafp_2119_candidate_parent.sum()),
      'in_mechanism_scored':int(df.in_gaiafp_mechanism_scored.sum()),
      'in_95_physical_characterization':int(df.in_gaiafp_95_physical_characterization.sum()),
      'in_2026_MS_NS_reference_pair':special.source_id.tolist(),
      'scored_external_reference_source_ids':matched.source_id.tolist(),
      'scored_reference_records':matched.to_dict('records'),
      'interpretation':'Only one of the 21 literature RV-followed NS candidates is present in the archived mechanism_scored output: Gaia DR3 1801110822095134848. Its corrected S1 is in the dark-consistent tail (see row-level score JSON). None of the 21 lies in the 2,119-object substellar candidate parent or in the 95-object validation subset. This is a one-object external, out-of-domain sanity check, not independent validation of sensitivity, specificity, or AUC. The 2024 authors explicitly say ultramassive WD and tight WD+WD alternatives cannot be fully excluded.'}
    (out/'EXTERNAL_NS_RV_REFERENCE_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='scored_reference_records'},indent=2));return report

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--outdir',default='results/final_completion');a=p.parse_args();main(a.root,a.outdir)
