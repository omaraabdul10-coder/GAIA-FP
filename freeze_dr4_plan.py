#!/usr/bin/env python3
"""Create a local pre-release SHA256 freeze record for DR4 prediction code/plan.

This is a reproducibility hash, NOT an OSF registration or trusted timestamp.
"""
from pathlib import Path
import hashlib,json,datetime
ROOT=Path(__file__).resolve().parents[1]
FILES=[
 'PREREGISTRATION.md','PREREG_AMENDMENT_v0.5.md','PREREG_AMENDMENT_v0.6_DRAFT.md',
 'DR4_READINESS.md','src/dr4_run.py','src/rvs_v32.py','src/dr4_evaluate.py',
 'src/dr4_schema.py','src/dr4_adapters.py','src/dr4_epoch_adapter.py','src/dr4_fetch.py',
 'src/dr4_dynamical.py','src/dr4_h12_prepare.py','src/dr4_mechanism.py',
 'src/dr4_mechanism_guarded.py','configs/dr4_epoch_astrometry_mapping.template.json'
]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
missing=[x for x in FILES if not (ROOT/x).is_file()]
if missing: raise SystemExit(f'Missing freeze inputs: {missing}')
manifest={'status':'LOCAL_PRE_RELEASE_HASH_FREEZE_NOT_OSF_REGISTERED',
 'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'purpose':'Freeze DR4 prediction code, thresholds, schema adapters and analysis plan before DR4 release.',
 'label_access':'Prediction pipeline does not read sealed labels; dr4_evaluate.py opens labels only after catalogue SHA256 validation.',
 'primary_model':'v3.2 (src/dr4_run.py + src/rvs_v32.py; local v0.6 A25 draft)',
 'registered_comparator':'v3.1 output retained alongside v3.2',
 'sensitivity':'A6-off posterior retained as sensitivity output',
 'verdict_threshold':0.15,
 'A6':'secondary-to-primary flux ratio ell=q**n >= 0.2 AND K_sum*(1+e) >= 30 km/s',
 'files':{x:sha(ROOT/x) for x in FILES},
 'limitations':['This local hash does not prove external preregistration or immutable timestamping.',
                'The v0.6 amendment is a local draft; it must not be described as OSF-registered.',
                'Live Gaia DR4 schema/fetch and real-data evaluation have not been executed.']}
out=ROOT/'audit'/'DR4_PRE_RELEASE_FREEZE_2026-11-03.json';out.write_text(json.dumps(manifest,indent=2)+'\n')
with (ROOT/'audit'/'DR4_PRE_RELEASE_FREEZE_2026-11-03.sha256').open('w') as f:
 for x,h in manifest['files'].items(): f.write(f'{h}  {x}\n')
print(out)
