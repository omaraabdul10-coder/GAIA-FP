"""VALIDATION-only check of the v3.1 realism fix: per-candidate period uncertainty in the RVS template."""
import json, warnings, numpy as np; warnings.filterwarnings('ignore')
import sim, tournament as T, lik
from blind_eval import roc_auc
train, val = T.splits(); out = {}
for nm, cfg in [('fixed_1pct', {}), ('own_sigP', dict(own_sigP=True))]:
    X = sim.build(*val, cfg=cfg, seed=21); y = X['y'].values
    X, L, p, _ = T.score(X); br = (X['nep'] > 0).values
    zi = X['z'].values[(y == 1) & br]
    out[nm] = dict(auc=float(roc_auc(p, y)), rej95=T.rej95(p, y), auc_bright=float(roc_auc(p[br], y[br])),
                   imp_z_gt_2p33=float(np.mean(zi > 2.326)), median_sigP=float(np.median(X['sigP'])))
    print(nm, out[nm], flush=True)
json.dump(out, open('../results/sigp_validation.json', 'w'), indent=1)
