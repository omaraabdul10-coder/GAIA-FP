"""X3 sensitivity (VALIDATION only): follow-up policy comparison under pessimistic instrument assumptions."""
import json, warnings, numpy as np; warnings.filterwarnings('ignore')
import sim, tournament as T, followup
train, val = T.splits(); Xv = sim.build(*val, seed=21); Xv, L0, p0, _ = T.score(Xv)
res = {}
for nm, dv, sz in [('nominal_DV8_SZ0.12', 8.0, 0.12), ('DV15', 15.0, 0.12), ('SZ0.20', 8.0, 0.20), ('DV15_SZ0.20', 15.0, 0.20)]:
    followup.DV_MIN, followup.SIG_Z = dv, sz
    res[nm] = T.followup_experiment(Xv, p0, seed=4)
    print(nm, {k: (v['resolved_correct'], v['resolved_wrong']) for k, v in res[nm]['policies'].items()}, res[nm]['eig_choice'], flush=True)
json.dump(res, open('../results/x3_sensitivity.json', 'w'), indent=1, default=float)
