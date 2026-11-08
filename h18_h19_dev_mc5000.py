"""8 Nov 2026: DR3 development values of H18/H19 recomputed with n_mc = 5000 rho labels (A27), as DR4 will use.
The 7 Nov values used the stored n_mc = 200 labels. Only the rows that enter H18/H19 are relabelled."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, '.')
import dark_companion as DC, mechanism as M, new_hypotheses as N
from dr4_mechanism import rho_labels_chunked
X = pd.read_csv('../results/dark_companion_scored.csv', dtype={'source_id': str})
Y = M.physics(X); Y['m2dark'] = N.dark_assumed_m2(Y.a0, Y.parallax, Y.period, Y.m1)
sel = (Y.m2dyn >= N.COMPACT_MSUN) | ((Y.m2dark >= N.BD_RANGE_MJ[0]*N.MJ) & (Y.m2dark < N.BD_RANGE_MJ[1]*N.MJ))
Xs = X[sel.values].reset_index(drop=True)
lab, rho = rho_labels_chunked(Xs, n_mc=5000, base=DC.rho_labels)
Xs['label'] = lab; Xs['rho'] = rho
res, _ = N.h18_h19(Xs)
res['n_mc'] = 5000; res['changed_labels_vs_n_mc_200'] = int((X[sel.values].label.values != lab).sum())
print(json.dumps(res, indent=1)); json.dump(res, open('../results/new_hypotheses_dev_dr3_mc5000.json', 'w'), indent=1)
