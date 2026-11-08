"""8 Nov 2026 (exploratory): mass under-estimate for the GAIA-FP DR3 CANDIDATES themselves, using the 95 candidates that also
have a Gaia AstroSpectroSB1 orbit (labels from astrospectro_check.py, fixed 9 Oct). Ratio = dynamical m2 / dark-assumed m2 (mfit).
Sealed ids are dropped first."""
import json, numpy as np, pandas as pd
L = pd.read_csv('../results/astrospectro_labels.csv', dtype={'source_id': str})
C = pd.read_csv('../results/dr3_candidates_scored.csv', dtype={'source_id': str})
S = set(pd.read_csv('../realdata/excluded_sealed_ids.csv', dtype={'source_id': str}).source_id.str.strip())
D = L.merge(C[['source_id', 'mfit', 'P_impostor', 'verdict']], on='source_id'); D = D[~D.source_id.isin(S)]
imp = D[D.label == 1]; r = imp.m2_dyn/imp.mfit
rng = np.random.default_rng(7); bs = [np.median(rng.choice(r.values, len(r))) for _ in range(2000)]
out = dict(n_candidates_with_combined_orbit=len(D), n_impostor_labelled=len(imp), n_genuine_labelled=int((D.label == 0).sum()),
           median_ratio=float(r.median()), ratio_ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
           ratio_quartiles=[float(r.quantile(.25)), float(r.quantile(.75))],
           median_mfit_MJ=float(imp.mfit.median()), median_m2dyn_MJ=float(imp.m2_dyn.median()),
           frac_impostors_true_mass_above_80MJ=float((imp.m2_dyn > 80).mean()))
print(json.dumps(out, indent=1)); json.dump(out, open('../results/candidate_mass_bias.json', 'w'), indent=1)
