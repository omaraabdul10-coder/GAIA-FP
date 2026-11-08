#!/usr/bin/env python3
"""Build evidence-only source_id lineage tables from the frozen GAIA-FP snapshot.

No exclusion reason is inferred from absence alone. A missing downstream row is
reported as a missing output membership; upstream cause remains UNKNOWN unless
an intermediate source table records it.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results' / 'final_completion'
OUT.mkdir(parents=True, exist_ok=True)

def ids(path, col='source_id'):
    d = pd.read_csv(path, dtype={col: 'string'})
    if col not in d:
        raise ValueError(f'{path}: missing {col}')
    return d[col].dropna().str.strip()

raw = ids(ROOT/'realdata/dr3_nss_two_body_orbit_raw.csv')
cand = ids(ROOT/'realdata/dr3_candidates.csv')
mech = ids(ROOT/'results/mechanism_scored.csv')
astro95 = ids(ROOT/'realdata/dr3_astrospectro_ch.csv')
char95 = ids(ROOT/'results/qa2/partial_completion/astrospectro_95_object_characterization.csv')

sets = {
    'raw_nss': set(raw), 'candidate_table': set(cand),
    'mechanism_scored': set(mech), 'astrospectro_ch_95': set(astro95),
    'characterization_95': set(char95),
}
# The 746 discrepancy is the mechanism-scored population's 746 IDs not present
# in the 71,759-row raw NSS file. Keep this distinct from the old H10 row delta.
mech_only = sorted(sets['mechanism_scored'] - sets['raw_nss'], key=int)
if len(mech_only) != 746:
    raise RuntimeError(f'Expected 746 mechanism-only IDs, found {len(mech_only)}')
rows=[]
for sid in mech_only:
    rows.append({
        'source_id': sid,
        **{f'present_{name}': sid in s for name,s in sets.items()},
        'lineage_class': 'mechanism_scored_not_in_raw_NSS',
        'interpretation': 'Population-definition/source-catalogue difference; per-ID upstream provenance not available in this snapshot.'
    })
pd.DataFrame(rows).to_csv(OUT/'DATA_LINEAGE_746.csv', index=False)

# Full population membership reconciliation for reproducibility.
all_ids = sorted(sets['raw_nss'] | sets['mechanism_scored'], key=int)
full=[]
for sid in all_ids:
    full.append({'source_id':sid, **{f'present_{name}':sid in s for name,s in sets.items()}})
pd.DataFrame(full).to_csv(OUT/'DATA_LINEAGE_RAW_NSS_vs_MECHANISM_FULL.csv', index=False)

# Exact 95-object membership. The 33 rows are known to be present in raw NSS,
# candidate_table and the 95-object input, but absent from mechanism_scored.
ids95 = sorted(sets['characterization_95'], key=int)
if len(ids95) != 95:
    raise RuntimeError(f'Expected 95 characterization IDs, found {len(ids95)}')
rows=[]
for sid in ids95:
    in_mech = sid in sets['mechanism_scored']
    rows.append({
        'source_id':sid,
        'present_raw_nss':sid in sets['raw_nss'],
        'present_candidate_table':sid in sets['candidate_table'],
        'present_astrospectro_ch_95':sid in sets['astrospectro_ch_95'],
        'present_characterization_95':True,
        'present_mechanism_scored':in_mech,
        'mechanism_output_status':'PRESENT' if in_mech else 'ABSENT',
        'first_observed_missing_stage':'mechanism_scored_output' if not in_mech else '',
        'upstream_filter_reason':'NOT_IDENTIFIABLE_FROM_AVAILABLE_FILES' if not in_mech else 'NOT_APPLICABLE',
        'evidence':'realdata/dr3_nss_two_body_orbit_raw.csv; realdata/dr3_candidates.csv; realdata/dr3_astrospectro_ch.csv; results/qa2/partial_completion/astrospectro_95_object_characterization.csv; results/mechanism_scored.csv',
        'note':'Absence from mechanism_scored does not identify which upstream join/filter failed. The source input results/dark_companion_scored.csv and its intermediate filter masks are absent.' if not in_mech else 'Present in mechanism_scored output.'
    })
out95=pd.DataFrame(rows)
if int((~out95.present_mechanism_scored).sum()) != 33:
    raise RuntimeError('Expected exactly 33/95 IDs absent from mechanism_scored')
out95.to_csv(OUT/'LINEAGE_33_OF_95.csv', index=False)

summary = {
 'raw_nss_rows':len(raw), 'raw_nss_unique':raw.nunique(),
 'candidate_rows':len(cand), 'candidate_unique':cand.nunique(),
 'mechanism_rows':len(mech), 'mechanism_unique':mech.nunique(),
 'raw_nss_intersection_mechanism':len(sets['raw_nss'] & sets['mechanism_scored']),
 'raw_nss_only':len(sets['raw_nss'] - sets['mechanism_scored']),
 'mechanism_only_746':len(mech_only),
 'characterization_95':len(ids95),
 'characterization95_in_raw_nss':sum(s in sets['raw_nss'] for s in ids95),
 'characterization95_in_candidate_table':sum(s in sets['candidate_table'] for s in ids95),
 'characterization95_in_mechanism':sum(s in sets['mechanism_scored'] for s in ids95),
 'characterization95_missing_mechanism':sum(s not in sets['mechanism_scored'] for s in ids95),
 'old_H10_2672_minus_1926_lineage':'NOT RECONSTRUCTABLE: original 2,672-row and 1,926-row source tables/IDs are not in this archive.'
}
import json
(OUT/'lineage_membership_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
